"""
Transactional Outbox — guaranteed event delivery.

The key insight: events are written in the SAME database transaction as
the data mutation, so if the mutation succeeds the event is guaranteed to
exist.  A Celery beat worker polls ``outbox_events`` and dispatches each
event to the appropriate handler (WebSocket push, notifications, webhooks,
audit log).

Usage in a route::

    @router.post("/items")
    async def create_item(
        session: AsyncSession = Depends(get_session),
        user: User = Depends(get_current_user),
    ):
        item = Item(name="demo")
        session.add(item)

        await OutboxService.publish(
            event_type=EventType.RESOURCE_CREATED,
            resource_type="item",
            resource_id=str(item.id),
            payload={"name": item.name},
            user_id=str(user.id),
            session=session,          # <-- same session!
        )

        await session.commit()        # item + event committed atomically

Or with the decorator::

    @emit_event(EventType.RESOURCE_CREATED, resource_type="item")
    async def create_item(session, user, ...):
        ...
"""

from __future__ import annotations

import functools
import json
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Callable
from uuid import UUID

import structlog
from sqlalchemy import text, update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.outbox import OutboxEvent

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

class EventType(str, Enum):
    """Well-known event types emitted by the platform."""

    # Resource lifecycle
    RESOURCE_CREATED = "resource.created"
    RESOURCE_UPDATED = "resource.updated"
    RESOURCE_DELETED = "resource.deleted"

    # AI operations
    AI_JOB_STARTED = "ai.job.started"
    AI_JOB_COMPLETED = "ai.job.completed"
    AI_JOB_FAILED = "ai.job.failed"

    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"

    # Billing
    PLAN_CHANGED = "billing.plan_changed"
    QUOTA_EXCEEDED = "billing.quota_exceeded"

    # Notifications
    NOTIFICATION_CREATED = "notification.created"

    # Webhooks
    WEBHOOK_TRIGGERED = "webhook.triggered"


# ---------------------------------------------------------------------------
# OutboxService
# ---------------------------------------------------------------------------

class OutboxService:
    """Write events to the outbox table in the SAME DB transaction as mutations."""

    # ------------------------------------------------------------------
    # Publish (transactional write)
    # ------------------------------------------------------------------

    @staticmethod
    async def publish(
        event_type: EventType | str,
        resource_type: str,
        resource_id: str | None,
        payload: dict[str, Any],
        session: AsyncSession,
        user_id: str | None = None,
        tenant_id: str | None = None,
    ) -> UUID:
        """Write an event to the outbox table.

        The event is added to *session* but **not** committed — the caller
        must ``await session.commit()`` (or let the framework do it) so that
        the event is persisted atomically with the data mutation.

        Returns the generated event id.
        """
        event = OutboxEvent(
            event_type=str(event_type),
            resource_type=resource_type,
            resource_id=resource_id,
            payload_json=json.dumps(payload, default=str),
            user_id=UUID(user_id) if user_id else None,
            tenant_id=UUID(tenant_id) if tenant_id else None,
            status="pending",
        )
        session.add(event)

        logger.debug(
            "outbox_event_enqueued",
            event_id=str(event.id),
            event_type=str(event_type),
            resource_type=resource_type,
            resource_id=resource_id,
        )

        return event.id

    # ------------------------------------------------------------------
    # Process pending (called by Celery beat)
    # ------------------------------------------------------------------

    @staticmethod
    async def process_pending(batch_size: int = 100) -> int:
        """Poll for pending outbox events and dispatch them.

        Called by the Celery beat task every few seconds.

        1. SELECT pending events ordered by created_at.
        2. Mark each as ``processing``.
        3. Dispatch to handlers (WebSocket, notification, webhook, audit).
        4. Mark as ``processed`` (or ``failed`` on error, with retry logic).
        5. Return the count of events processed.
        """
        from app.database import get_session_context

        processed_count = 0

        async with get_session_context() as session:
            # Fetch pending events, oldest first
            result = await session.execute(
                select(OutboxEvent)
                .where(OutboxEvent.status.in_(["pending", "failed"]))
                .where(OutboxEvent.retry_count < OutboxEvent.max_retries)
                .order_by(OutboxEvent.created_at)
                .limit(batch_size)
            )
            events: list[OutboxEvent] = list(result.scalars().all())

            if not events:
                return 0

            # Mark as processing
            event_ids = [e.id for e in events]
            await session.execute(
                update(OutboxEvent)
                .where(OutboxEvent.id.in_(event_ids))
                .values(status="processing")
            )
            await session.commit()

        # Dispatch each event outside the select-transaction so that one
        # handler failure doesn't roll back the status update of others.
        for event in events:
            async with get_session_context() as session:
                try:
                    await OutboxService._dispatch(event)

                    await session.execute(
                        update(OutboxEvent)
                        .where(OutboxEvent.id == event.id)
                        .values(
                            status="processed",
                            processed_at=datetime.now(UTC),
                        )
                    )
                    await session.commit()
                    processed_count += 1

                    logger.info(
                        "outbox_event_processed",
                        event_id=str(event.id),
                        event_type=event.event_type,
                    )

                except Exception as exc:
                    new_retry = event.retry_count + 1
                    new_status = "failed" if new_retry < event.max_retries else "dead"
                    await session.execute(
                        update(OutboxEvent)
                        .where(OutboxEvent.id == event.id)
                        .values(
                            status=new_status,
                            retry_count=new_retry,
                            error=str(exc)[:2000],
                        )
                    )
                    await session.commit()

                    logger.warning(
                        "outbox_event_dispatch_failed",
                        event_id=str(event.id),
                        event_type=event.event_type,
                        retry_count=new_retry,
                        error=str(exc),
                    )

        return processed_count

    # ------------------------------------------------------------------
    # Cleanup (daily Celery beat task)
    # ------------------------------------------------------------------

    @staticmethod
    async def cleanup(days: int = 30) -> int:
        """Delete processed/dead events older than *days* days."""
        from app.database import get_session_context

        cutoff = datetime.now(UTC) - timedelta(days=days)

        async with get_session_context() as session:
            result = await session.execute(
                text(
                    "DELETE FROM outbox_events "
                    "WHERE status IN ('processed', 'dead') "
                    "AND created_at < :cutoff"
                ),
                {"cutoff": cutoff},
            )
            await session.commit()
            deleted = result.rowcount  # type: ignore[union-attr]

        logger.info("outbox_cleanup_completed", deleted=deleted, days=days)
        return deleted

    # ------------------------------------------------------------------
    # Internal dispatch — fan-out to handlers
    # ------------------------------------------------------------------

    @staticmethod
    async def _dispatch(event: OutboxEvent) -> None:
        """Fan-out a single event to all relevant handlers."""
        payload = json.loads(event.payload_json)

        # Run all handlers concurrently; collect exceptions but don't
        # let one handler's failure prevent the others from running.
        import asyncio

        results = await asyncio.gather(
            OutboxService._handle_notification(event, payload),
            OutboxService._handle_webhook(event, payload),
            OutboxService._handle_audit(event, payload),
            return_exceptions=True,
        )

        # If every handler raised, re-raise the first so the event gets
        # marked as failed.  If at least one succeeded we consider it
        # partially processed (logged, but marked processed).
        errors = [r for r in results if isinstance(r, Exception)]
        if errors and len(errors) == len(results):
            raise errors[0]

        if errors:
            for err in errors:
                logger.warning(
                    "outbox_handler_partial_failure",
                    event_id=str(event.id),
                    error=str(err),
                )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    @staticmethod
    async def _handle_notification(event: OutboxEvent, payload: dict) -> None:
        """Push a real-time notification via WebSocket + create a DB notification."""
        # Only certain event types warrant a user-visible notification
        _NOTIFY_TYPES = {
            EventType.AI_JOB_COMPLETED,
            EventType.AI_JOB_FAILED,
            EventType.PLAN_CHANGED,
            EventType.QUOTA_EXCEEDED,
            EventType.NOTIFICATION_CREATED,
        }

        if event.event_type not in {str(t) for t in _NOTIFY_TYPES}:
            return

        if event.user_id is None:
            return

        try:
            from app.core.notifications import NotificationService
            from app.database import get_session_context

            title = payload.get("title", event.event_type)
            body = payload.get("body", payload.get("message", ""))
            link = payload.get("link")

            # Determine notification type
            ntype = "info"
            if "failed" in event.event_type:
                ntype = "error"
            elif "completed" in event.event_type:
                ntype = "ai_complete"
            elif "quota" in event.event_type:
                ntype = "warning"

            async with get_session_context() as session:
                await NotificationService.create_notification(
                    user_id=event.user_id,
                    title=title,
                    body=body,
                    type=ntype,
                    link=link,
                    session=session,
                )

        except Exception as exc:
            logger.warning(
                "outbox_notification_handler_error",
                event_id=str(event.id),
                error=str(exc),
            )
            raise

    @staticmethod
    async def _handle_webhook(event: OutboxEvent, payload: dict) -> None:
        """Forward the event to integration_hub connectors (if configured)."""
        if event.event_type != str(EventType.WEBHOOK_TRIGGERED):
            return

        try:
            # integration_hub is an optional module; skip gracefully
            from app.modules.integration_hub.service import IntegrationHubService  # type: ignore[import-untyped]

            target_url = payload.get("webhook_url")
            if not target_url:
                return

            await IntegrationHubService.forward_webhook(
                url=target_url,
                event_type=event.event_type,
                payload=payload,
                tenant_id=str(event.tenant_id) if event.tenant_id else None,
            )
        except ImportError:
            # integration_hub module not installed — skip silently
            pass
        except Exception as exc:
            logger.warning(
                "outbox_webhook_handler_error",
                event_id=str(event.id),
                error=str(exc),
            )
            raise

    @staticmethod
    async def _handle_audit(event: OutboxEvent, payload: dict) -> None:
        """Write an audit log entry for the event."""
        # Structured log entry serves as the audit trail.  A dedicated
        # audit table can be added later without changing the outbox.
        logger.info(
            "audit_log",
            event_id=str(event.id),
            event_type=event.event_type,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            user_id=str(event.user_id) if event.user_id else None,
            tenant_id=str(event.tenant_id) if event.tenant_id else None,
            payload=payload,
            created_at=event.created_at.isoformat() if event.created_at else None,
        )


# ---------------------------------------------------------------------------
# Decorator — emit_event
# ---------------------------------------------------------------------------

def emit_event(event_type: EventType, resource_type: str) -> Callable:
    """Decorator that auto-publishes an outbox event after a successful call.

    The decorated function **must** accept ``session: AsyncSession`` and
    **may** accept ``user`` (with an ``id`` attribute).  The return value
    of the function is used to populate ``resource_id`` and ``payload``::

        @emit_event(EventType.RESOURCE_CREATED, resource_type="item")
        async def create_item(session: AsyncSession, user, data):
            item = Item(**data)
            session.add(item)
            return {"id": str(item.id), "name": item.name}

    The decorator calls ``OutboxService.publish`` with the returned dict
    before the session is committed, keeping both writes in the same
    transaction.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await fn(*args, **kwargs)

            # Extract session and user from kwargs (FastAPI Depends style)
            session: AsyncSession | None = kwargs.get("session")
            user = kwargs.get("user")

            if session is None:
                # Fall through — can't publish without a session
                logger.debug(
                    "emit_event_no_session",
                    fn=fn.__name__,
                    event_type=str(event_type),
                )
                return result

            # Build payload from result
            payload: dict[str, Any] = {}
            resource_id: str | None = None

            if isinstance(result, dict):
                payload = result
                resource_id = result.get("id")
            elif hasattr(result, "id"):
                resource_id = str(result.id)
                payload = {"id": resource_id}

            user_id = str(user.id) if user and hasattr(user, "id") else None

            await OutboxService.publish(
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                payload=payload,
                session=session,
                user_id=user_id,
            )

            return result

        return wrapper

    return decorator
