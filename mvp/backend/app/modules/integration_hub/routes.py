"""
Integration Hub API routes - External integrations management and webhook reception.
"""

import hashlib
import hmac
import json
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

webhook_logger = structlog.get_logger()

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.integration_hub.schemas import (
    ConnectorCreate,
    ConnectorRead,
    ProviderInfo,
    TriggerCreate,
    TriggerRead,
    WebhookEventRead,
)
from app.modules.integration_hub.service import IntegrationHubService
from app.rate_limit import limiter

router = APIRouter()


def _connector_to_read(connector, request: Optional[Request] = None) -> ConnectorRead:
    """Convert an IntegrationConnector model to ConnectorRead schema."""
    webhook_url = None
    if connector.type == "webhook":
        base = ""
        if request:
            base = str(request.base_url).rstrip("/")
        webhook_url = f"{base}/api/integrations/webhook/{connector.id}"

    return ConnectorRead(
        id=connector.id,
        user_id=connector.user_id,
        name=connector.name,
        type=connector.type,
        provider=connector.provider,
        status=connector.status,
        webhook_url=webhook_url,
        webhook_secret=connector.webhook_secret if connector.type == "webhook" else None,
        events_received=connector.events_received,
        last_event_at=connector.last_event_at,
        is_active=connector.is_active,
        created_at=connector.created_at,
        updated_at=connector.updated_at,
    )


def _event_to_read(event) -> WebhookEventRead:
    """Convert a WebhookEvent model to WebhookEventRead schema."""
    payload = json.loads(event.payload_json) if event.payload_json else {}
    return WebhookEventRead(
        id=event.id,
        connector_id=event.connector_id,
        event_type=event.event_type,
        payload=payload,
        status=event.status,
        processed_at=event.processed_at,
        created_at=event.created_at,
    )


def _trigger_to_read(trigger) -> TriggerRead:
    """Convert an IntegrationTrigger model to TriggerRead schema."""
    action_config = json.loads(trigger.action_config_json) if trigger.action_config_json else {}
    return TriggerRead(
        id=trigger.id,
        connector_id=trigger.connector_id,
        event_type=trigger.event_type,
        action_module=trigger.action_module,
        action_config=action_config,
        is_active=trigger.is_active,
        executions=trigger.executions,
        created_at=trigger.created_at,
    )


# ──────────────────────────────────────────────────────────────
# Providers
# ──────────────────────────────────────────────────────────────

@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers():
    """List all supported integration providers."""
    return [ProviderInfo(**p) for p in IntegrationHubService.get_supported_providers()]


# ──────────────────────────────────────────────────────────────
# Connectors
# ──────────────────────────────────────────────────────────────

@router.post("/connectors", response_model=ConnectorRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_connector(
    request: Request,
    body: ConnectorCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new integration connector.

    Rate limit: 10 requests/minute
    """
    valid_types = {"webhook", "oauth2", "api_key"}
    if body.type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid connector type. Must be one of: {', '.join(sorted(valid_types))}",
        )

    service = IntegrationHubService(session)
    connector = await service.create_connector(
        user_id=current_user.id,
        data=body.model_dump(),
    )
    return _connector_to_read(connector, request)


@router.get("/connectors", response_model=list[ConnectorRead])
@limiter.limit("20/minute")
async def list_connectors(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List user's integration connectors.

    Rate limit: 20 requests/minute
    """
    service = IntegrationHubService(session)
    connectors = await service.list_connectors(current_user.id, skip, limit)
    return [_connector_to_read(c, request) for c in connectors]


@router.get("/connectors/{connector_id}", response_model=ConnectorRead)
@limiter.limit("30/minute")
async def get_connector(
    request: Request,
    connector_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a connector by ID.

    Rate limit: 30 requests/minute
    """
    service = IntegrationHubService(session)
    connector = await service.get_connector(connector_id, current_user.id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )
    return _connector_to_read(connector, request)


@router.delete("/connectors/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_connector(
    request: Request,
    connector_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Soft-delete a connector (disables it).

    Rate limit: 10 requests/minute
    """
    service = IntegrationHubService(session)
    deleted = await service.delete_connector(current_user.id, connector_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )
    return None


@router.post("/connectors/{connector_id}/test")
@limiter.limit("5/minute")
async def test_connector(
    request: Request,
    connector_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Test connectivity for a connector.

    Rate limit: 5 requests/minute
    """
    service = IntegrationHubService(session)
    result = await service.test_connector(current_user.id, connector_id)
    if not result.get("success") and result.get("error") == "Connector not found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )
    return result


# ──────────────────────────────────────────────────────────────
# Webhook receiver (public - no auth)
# ──────────────────────────────────────────────────────────────

def _verify_webhook_signature(body: bytes, secret: str, signature: Optional[str]) -> bool:
    """
    Validate an HMAC-SHA256 webhook signature.

    The caller must send the header ``X-Webhook-Signature`` whose value is
    ``sha256=<hex-digest>``.  The digest is computed over the raw request
    body using the connector's ``webhook_secret`` as the HMAC key.
    """
    if not signature:
        return False
    # Accept both "sha256=<hex>" and plain "<hex>" formats
    if signature.startswith("sha256="):
        signature = signature[7:]
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhook/{connector_id}")
async def receive_webhook(
    connector_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    Receive an incoming webhook event.

    External services (Stripe, GitHub, Slack, etc.) send events to this endpoint.
    The connector_id in the URL identifies which integration receives the event.

    Requires ``X-Webhook-Signature: sha256=<hex>`` header for HMAC-SHA256
    signature validation (MED-04).
    """
    # Read raw body once for both signature verification and payload parsing
    raw_body = await request.body()

    # --- MED-04: Validate webhook signature ---
    service = IntegrationHubService(session)
    connector = await service.get_connector(connector_id)
    if not connector or not connector.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found or disabled",
        )

    sig_header = request.headers.get("X-Webhook-Signature")
    if not _verify_webhook_signature(raw_body, connector.webhook_secret, sig_header):
        webhook_logger.warning(
            "webhook_signature_invalid",
            connector_id=str(connector_id),
            has_signature=bool(sig_header),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing webhook signature",
        )
    # --- End MED-04 ---

    try:
        payload = json.loads(raw_body)
    except Exception:
        payload = {"raw": raw_body.decode("utf-8", errors="replace")}

    event = await service.receive_webhook(connector_id, payload)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found or disabled",
        )
    return {
        "status": "received",
        "event_id": str(event.id),
        "event_type": event.event_type,
    }


# ──────────────────────────────────────────────────────────────
# Events
# ──────────────────────────────────────────────────────────────

@router.get("/connectors/{connector_id}/events", response_model=list[WebhookEventRead])
@limiter.limit("20/minute")
async def list_events(
    request: Request,
    connector_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List received events for a connector.

    Rate limit: 20 requests/minute
    """
    service = IntegrationHubService(session)
    events = await service.list_events(current_user.id, connector_id, limit)
    return [_event_to_read(e) for e in events]


# ──────────────────────────────────────────────────────────────
# Triggers
# ──────────────────────────────────────────────────────────────

@router.post("/triggers", response_model=TriggerRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_trigger(
    request: Request,
    body: TriggerCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Create an event trigger (when event X happens, execute action Y in module Z).

    Rate limit: 10 requests/minute
    """
    # Verify connector ownership
    service = IntegrationHubService(session)
    connector = await service.get_connector(body.connector_id, current_user.id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )

    trigger = await service.create_trigger(
        user_id=current_user.id,
        data=body.model_dump(),
    )
    return _trigger_to_read(trigger)


@router.get("/triggers", response_model=list[TriggerRead])
@limiter.limit("20/minute")
async def list_triggers(
    request: Request,
    connector_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List triggers, optionally filtered by connector.

    Rate limit: 20 requests/minute
    """
    service = IntegrationHubService(session)
    triggers = await service.list_triggers(current_user.id, connector_id)
    return [_trigger_to_read(t) for t in triggers]


@router.delete("/triggers/{trigger_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_trigger(
    request: Request,
    trigger_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a trigger.

    Rate limit: 10 requests/minute
    """
    service = IntegrationHubService(session)
    deleted = await service.delete_trigger(current_user.id, trigger_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trigger not found",
        )
    return None
