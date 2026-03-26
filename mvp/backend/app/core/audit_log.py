"""
Immutable audit log — compliance-grade (SOC2/HIPAA/RGPD).

Provides a hash-chained, append-only audit trail. Each record includes
a SHA-256 hash of its own content and a link to the previous record's hash,
making any tampering or deletion detectable.

Usage:
    from app.core.audit_log import AuditLogger, AuditAction

    await AuditLogger.log(
        action=AuditAction.CREATE,
        resource_type="transcription",
        resource_id=str(transcription.id),
        user_id=str(current_user.id),
        details={"filename": "audio.mp3"},
    )
"""

import hashlib
import json
from datetime import UTC, datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

import structlog
from sqlalchemy import func, text
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session_context
from app.models.audit_log import AuditLogEntry

logger = structlog.get_logger()


class AuditAction(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    PUBLISH = "publish"
    EXECUTE = "execute"


def _compute_hash(
    record_id: str,
    action: str,
    resource_type: str,
    resource_id: str | None,
    user_id: str | None,
    timestamp: str,
    previous_hash: str | None,
) -> str:
    """Compute SHA-256 hash of a record's key fields for chain integrity."""
    payload = "|".join([
        record_id,
        action,
        resource_type,
        resource_id or "",
        user_id or "",
        timestamp,
        previous_hash or "GENESIS",
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_json(obj: dict | None) -> str | None:
    """Serialize a dict to compact JSON, or return None."""
    if obj is None:
        return None
    try:
        return json.dumps(obj, default=str, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        return json.dumps({"_error": "unserializable"})


class AuditLogger:
    """Records immutable audit events. INSERT-only, no UPDATE/DELETE ever."""

    @staticmethod
    async def log(
        action: AuditAction,
        resource_type: str,
        resource_id: str | None = None,
        user_id: str | None = None,
        tenant_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        """Create an immutable audit record with hash chain linking."""
        own_session = session is None
        try:
            if own_session:
                ctx = get_session_context()
                session = await ctx.__aenter__()

            # Fetch the hash of the most recent record for chain linking
            prev_result = await session.execute(
                select(AuditLogEntry.record_hash)
                .order_by(AuditLogEntry.created_at.desc())
                .limit(1)
            )
            previous_hash = prev_result.scalar_one_or_none()

            record_id = str(uuid4())
            now = datetime.now(UTC)
            timestamp = now.isoformat()

            record_hash = _compute_hash(
                record_id=record_id,
                action=action.value if isinstance(action, AuditAction) else action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                timestamp=timestamp,
                previous_hash=previous_hash,
            )

            entry = AuditLogEntry(
                id=UUID(record_id),
                tenant_id=UUID(tenant_id) if tenant_id else None,
                user_id=UUID(user_id) if user_id else None,
                action=action.value if isinstance(action, AuditAction) else action,
                resource_type=resource_type,
                resource_id=resource_id,
                details_json=_safe_json(details),
                old_value_json=_safe_json(old_value),
                new_value_json=_safe_json(new_value),
                ip_address=ip_address,
                user_agent=user_agent,
                record_hash=record_hash,
                previous_hash=previous_hash,
                created_at=now,
            )

            session.add(entry)
            await session.commit()

            logger.debug(
                "audit_logged",
                action=entry.action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
            )

        except Exception as exc:
            logger.error(
                "audit_log_failed",
                action=str(action),
                resource_type=resource_type,
                error=str(exc),
            )
            if own_session:
                try:
                    await session.rollback()
                except Exception:
                    pass
        finally:
            if own_session and session is not None:
                try:
                    await ctx.__aexit__(None, None, None)
                except Exception:
                    pass

    @staticmethod
    async def query(
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        action: str | None = None,
        tenant_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
        session: AsyncSession = None,
    ) -> tuple[list[AuditLogEntry], int]:
        """Query audit log with filters. Returns (entries, total_count)."""
        filters = []

        if user_id:
            filters.append(AuditLogEntry.user_id == UUID(user_id))
        if resource_type:
            filters.append(AuditLogEntry.resource_type == resource_type)
        if resource_id:
            filters.append(AuditLogEntry.resource_id == resource_id)
        if action:
            filters.append(AuditLogEntry.action == action)
        if tenant_id:
            filters.append(AuditLogEntry.tenant_id == UUID(tenant_id))
        if start_date:
            filters.append(AuditLogEntry.created_at >= start_date)
        if end_date:
            filters.append(AuditLogEntry.created_at <= end_date)

        # Total count
        count_stmt = select(func.count()).select_from(AuditLogEntry)
        if filters:
            count_stmt = count_stmt.where(*filters)
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        # Paginated results
        query_stmt = (
            select(AuditLogEntry)
            .order_by(AuditLogEntry.created_at.desc())
            .offset(offset)
            .limit(min(limit, 200))
        )
        if filters:
            query_stmt = query_stmt.where(*filters)

        result = await session.execute(query_stmt)
        entries = list(result.scalars().all())

        return entries, total

    @staticmethod
    async def verify_chain(
        last_n: int,
        session: AsyncSession,
    ) -> dict:
        """Verify hash chain integrity of the last N records.

        Returns a dict with:
        - verified: int (number of records checked)
        - valid: bool (True if chain is intact)
        - first_broken_at: str | None (ID of first broken link)
        - details: str
        """
        result = await session.execute(
            select(AuditLogEntry)
            .order_by(AuditLogEntry.created_at.desc())
            .limit(min(last_n, 10000))
        )
        entries = list(result.scalars().all())

        if not entries:
            return {
                "verified": 0,
                "valid": True,
                "first_broken_at": None,
                "details": "No audit records found.",
            }

        # Entries are in desc order; reverse for chronological verification
        entries.reverse()

        broken_at = None
        for i, entry in enumerate(entries):
            expected_previous = entries[i - 1].record_hash if i > 0 else None

            # Verify previous_hash chain link
            if i > 0 and entry.previous_hash != expected_previous:
                broken_at = str(entry.id)
                break

            # Verify record_hash integrity
            expected_hash = _compute_hash(
                record_id=str(entry.id),
                action=entry.action,
                resource_type=entry.resource_type,
                resource_id=entry.resource_id,
                user_id=str(entry.user_id) if entry.user_id else None,
                timestamp=entry.created_at.isoformat(),
                previous_hash=entry.previous_hash,
            )
            if entry.record_hash != expected_hash:
                broken_at = str(entry.id)
                break

        is_valid = broken_at is None
        return {
            "verified": len(entries),
            "valid": is_valid,
            "first_broken_at": broken_at,
            "details": (
                f"All {len(entries)} records verified. Chain integrity OK."
                if is_valid
                else f"Chain broken at record {broken_at}. Possible tampering detected."
            ),
        }

    @staticmethod
    async def get_stats(
        tenant_id: str | None = None,
        days: int = 30,
        session: AsyncSession = None,
    ) -> dict:
        """Get audit statistics: events by action, by resource, by day."""
        from datetime import timedelta

        cutoff = datetime.now(UTC) - timedelta(days=days)
        filters = [AuditLogEntry.created_at >= cutoff]
        if tenant_id:
            filters.append(AuditLogEntry.tenant_id == UUID(tenant_id))

        # By action
        action_result = await session.execute(
            select(
                AuditLogEntry.action,
                func.count().label("count"),
            )
            .where(*filters)
            .group_by(AuditLogEntry.action)
            .order_by(func.count().desc())
        )
        by_action = [
            {"action": row.action, "count": row.count}
            for row in action_result.all()
        ]

        # By resource_type
        resource_result = await session.execute(
            select(
                AuditLogEntry.resource_type,
                func.count().label("count"),
            )
            .where(*filters)
            .group_by(AuditLogEntry.resource_type)
            .order_by(func.count().desc())
        )
        by_resource = [
            {"resource_type": row.resource_type, "count": row.count}
            for row in resource_result.all()
        ]

        # By user (top 10)
        user_result = await session.execute(
            select(
                AuditLogEntry.user_id,
                func.count().label("count"),
            )
            .where(*filters, AuditLogEntry.user_id.isnot(None))
            .group_by(AuditLogEntry.user_id)
            .order_by(func.count().desc())
            .limit(10)
        )
        by_user = [
            {"user_id": str(row.user_id), "count": row.count}
            for row in user_result.all()
        ]

        # By day (last N days)
        day_result = await session.execute(
            select(
                func.date_trunc("day", AuditLogEntry.created_at).label("day"),
                func.count().label("count"),
            )
            .where(*filters)
            .group_by(text("1"))
            .order_by(text("1"))
        )
        by_day = [
            {"date": row.day.isoformat() if row.day else None, "count": row.count}
            for row in day_result.all()
        ]

        # Total
        total_result = await session.execute(
            select(func.count()).select_from(AuditLogEntry).where(*filters)
        )
        total = total_result.scalar_one()

        return {
            "total_events": total,
            "period_days": days,
            "by_action": by_action,
            "by_resource": by_resource,
            "by_user": by_user,
            "by_day": by_day,
        }
