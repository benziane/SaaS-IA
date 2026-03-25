"""
Integration Hub service - External integrations with webhooks, OAuth2, and API key connectors.

Provides a Zapier-like experience for connecting external services
to platform modules via webhooks, triggers, and automated actions.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.integration_hub import (
    IntegrationConnector,
    IntegrationTrigger,
    WebhookEvent,
)

logger = structlog.get_logger()

# Supported providers registry
SUPPORTED_PROVIDERS = [
    {
        "slug": "slack",
        "name": "Slack",
        "description": "Receive Slack messages, commands, and interaction events",
        "supported_types": ["webhook", "oauth2"],
        "icon": "Chat",
        "events": ["message", "app_mention", "slash_command", "reaction_added", "channel_created"],
    },
    {
        "slug": "github",
        "name": "GitHub",
        "description": "Receive push, PR, issue, and release events from GitHub repositories",
        "supported_types": ["webhook", "oauth2"],
        "icon": "Code",
        "events": ["push", "pull_request", "issues", "release", "star", "fork", "workflow_run"],
    },
    {
        "slug": "stripe",
        "name": "Stripe",
        "description": "Receive payment, subscription, and invoice events from Stripe",
        "supported_types": ["webhook", "api_key"],
        "icon": "Payment",
        "events": ["payment_intent.succeeded", "payment_intent.failed", "invoice.paid", "customer.subscription.created", "charge.refunded"],
    },
    {
        "slug": "sendgrid",
        "name": "SendGrid",
        "description": "Receive email delivery, bounce, and engagement events",
        "supported_types": ["webhook", "api_key"],
        "icon": "Email",
        "events": ["delivered", "bounce", "open", "click", "spam_report", "unsubscribe"],
    },
    {
        "slug": "twilio",
        "name": "Twilio",
        "description": "Receive SMS, call, and messaging events from Twilio",
        "supported_types": ["webhook", "api_key"],
        "icon": "Phone",
        "events": ["sms.received", "sms.delivered", "call.completed", "call.initiated"],
    },
    {
        "slug": "notion",
        "name": "Notion",
        "description": "Sync pages, databases, and content from Notion workspaces",
        "supported_types": ["oauth2"],
        "icon": "Description",
        "events": ["page.created", "page.updated", "database.updated", "comment.created"],
    },
    {
        "slug": "linear",
        "name": "Linear",
        "description": "Receive issue, project, and cycle events from Linear",
        "supported_types": ["webhook", "oauth2"],
        "icon": "BugReport",
        "events": ["issue.created", "issue.updated", "issue.completed", "project.updated", "cycle.completed"],
    },
    {
        "slug": "google_drive",
        "name": "Google Drive",
        "description": "Sync files and receive change notifications from Google Drive",
        "supported_types": ["oauth2"],
        "icon": "CloudUpload",
        "events": ["file.created", "file.modified", "file.deleted", "file.shared"],
    },
    {
        "slug": "dropbox",
        "name": "Dropbox",
        "description": "Sync files and receive change notifications from Dropbox",
        "supported_types": ["oauth2"],
        "icon": "CloudQueue",
        "events": ["file.added", "file.modified", "file.deleted", "folder.created"],
    },
    {
        "slug": "hubspot",
        "name": "HubSpot",
        "description": "Receive CRM contact, deal, and company events from HubSpot",
        "supported_types": ["webhook", "oauth2"],
        "icon": "People",
        "events": ["contact.created", "contact.updated", "deal.created", "deal.closed", "company.created"],
    },
]


class IntegrationHubService:
    """Service for managing external integration connectors, webhooks, and triggers."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_connector(
        self,
        user_id: UUID,
        data: dict,
    ) -> IntegrationConnector:
        """Create a new integration connector."""
        connector = IntegrationConnector(
            user_id=user_id,
            name=data["name"],
            type=data["type"],
            provider=data.get("provider", "custom"),
            config_json=json.dumps(data.get("config", {}), ensure_ascii=False),
            is_active=data.get("enabled", True),
            status="active" if data.get("enabled", True) else "disabled",
        )
        self.session.add(connector)
        await self.session.commit()
        await self.session.refresh(connector)

        logger.info(
            "connector_created",
            connector_id=str(connector.id),
            name=connector.name,
            type=connector.type,
            provider=connector.provider,
        )
        return connector

    async def list_connectors(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[IntegrationConnector]:
        """List all connectors for a user."""
        result = await self.session.execute(
            select(IntegrationConnector)
            .where(IntegrationConnector.user_id == user_id)
            .order_by(IntegrationConnector.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_connector(
        self,
        connector_id: UUID,
        user_id: Optional[UUID] = None,
    ) -> Optional[IntegrationConnector]:
        """Get a connector by ID, optionally verifying ownership."""
        connector = await self.session.get(IntegrationConnector, connector_id)
        if not connector:
            return None
        if user_id and connector.user_id != user_id:
            return None
        return connector

    async def delete_connector(
        self,
        user_id: UUID,
        connector_id: UUID,
    ) -> bool:
        """Soft-delete a connector by disabling it."""
        connector = await self.session.get(IntegrationConnector, connector_id)
        if not connector or connector.user_id != user_id:
            return False

        connector.is_active = False
        connector.status = "disabled"
        connector.updated_at = datetime.utcnow()
        self.session.add(connector)
        await self.session.commit()

        logger.info("connector_deleted", connector_id=str(connector_id))
        return True

    async def test_connector(
        self,
        user_id: UUID,
        connector_id: UUID,
    ) -> dict:
        """Test connectivity for a connector (mock implementation)."""
        connector = await self.session.get(IntegrationConnector, connector_id)
        if not connector or connector.user_id != user_id:
            return {"success": False, "error": "Connector not found"}

        # Mock connectivity test based on provider
        provider_info = next(
            (p for p in SUPPORTED_PROVIDERS if p["slug"] == connector.provider),
            None,
        )

        if connector.type == "webhook":
            return {
                "success": True,
                "provider": connector.provider,
                "type": connector.type,
                "message": f"Webhook endpoint ready for {connector.provider}",
                "webhook_url": f"/api/integrations/webhook/{connector.id}",
            }
        elif connector.type == "api_key":
            config = json.loads(connector.config_json)
            has_key = bool(config.get("api_key"))
            return {
                "success": has_key,
                "provider": connector.provider,
                "type": connector.type,
                "message": "API key configured" if has_key else "API key not configured",
            }
        elif connector.type == "oauth2":
            config = json.loads(connector.config_json)
            has_token = bool(config.get("access_token"))
            return {
                "success": has_token,
                "provider": connector.provider,
                "type": connector.type,
                "message": "OAuth2 token present" if has_token else "OAuth2 authorization required",
            }

        return {
            "success": False,
            "provider": connector.provider,
            "type": connector.type,
            "message": f"Unknown connector type: {connector.type}",
        }

    async def receive_webhook(
        self,
        connector_id: UUID,
        payload: dict,
    ) -> Optional[WebhookEvent]:
        """Process an incoming webhook event."""
        connector = await self.session.get(IntegrationConnector, connector_id)
        if not connector or not connector.is_active:
            return None

        # Determine event type from payload (provider-specific heuristics)
        event_type = self._extract_event_type(connector.provider, payload)

        event = WebhookEvent(
            connector_id=connector_id,
            event_type=event_type,
            payload_json=json.dumps(payload, ensure_ascii=False, default=str),
            status="received",
        )
        self.session.add(event)

        # Update connector stats
        connector.events_received += 1
        connector.last_event_at = datetime.utcnow()
        self.session.add(connector)

        await self.session.commit()
        await self.session.refresh(event)

        logger.info(
            "webhook_received",
            connector_id=str(connector_id),
            event_type=event_type,
            provider=connector.provider,
        )

        # Fire matching triggers asynchronously
        await self._fire_triggers(connector, event)

        return event

    async def create_trigger(
        self,
        user_id: UUID,
        data: dict,
    ) -> IntegrationTrigger:
        """Create an event trigger (when X happens on connector, do Y in module)."""
        trigger = IntegrationTrigger(
            user_id=user_id,
            connector_id=data["connector_id"],
            event_type=data["event_type"],
            action_module=data["action_module"],
            action_config_json=json.dumps(data.get("action_config", {}), ensure_ascii=False),
        )
        self.session.add(trigger)
        await self.session.commit()
        await self.session.refresh(trigger)

        logger.info(
            "trigger_created",
            trigger_id=str(trigger.id),
            connector_id=str(trigger.connector_id),
            event_type=trigger.event_type,
            action_module=trigger.action_module,
        )
        return trigger

    async def list_triggers(
        self,
        user_id: UUID,
        connector_id: Optional[UUID] = None,
    ) -> list[IntegrationTrigger]:
        """List triggers for a user, optionally filtered by connector."""
        query = select(IntegrationTrigger).where(
            IntegrationTrigger.user_id == user_id
        )
        if connector_id:
            query = query.where(IntegrationTrigger.connector_id == connector_id)
        query = query.order_by(IntegrationTrigger.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_trigger(
        self,
        user_id: UUID,
        trigger_id: UUID,
    ) -> bool:
        """Delete a trigger."""
        trigger = await self.session.get(IntegrationTrigger, trigger_id)
        if not trigger or trigger.user_id != user_id:
            return False

        await self.session.delete(trigger)
        await self.session.commit()

        logger.info("trigger_deleted", trigger_id=str(trigger_id))
        return True

    async def list_events(
        self,
        user_id: UUID,
        connector_id: UUID,
        limit: int = 50,
    ) -> list[WebhookEvent]:
        """List received events for a connector."""
        # Verify ownership
        connector = await self.session.get(IntegrationConnector, connector_id)
        if not connector or connector.user_id != user_id:
            return []

        result = await self.session.execute(
            select(WebhookEvent)
            .where(WebhookEvent.connector_id == connector_id)
            .order_by(WebhookEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    def get_supported_providers() -> list[dict]:
        """Return the list of supported integration providers."""
        return SUPPORTED_PROVIDERS

    @staticmethod
    def _extract_event_type(provider: str, payload: dict) -> str:
        """Extract event type from webhook payload using provider-specific heuristics."""
        # GitHub sends event type in headers, but we get it from payload structure
        if provider == "github":
            if "action" in payload:
                ref_type = payload.get("ref_type", payload.get("pull_request", {}).get("state", ""))
                return f"{payload.get('action', 'unknown')}"
            if "ref" in payload and "commits" in payload:
                return "push"
            return "unknown"

        # Stripe uses a top-level 'type' field
        if provider == "stripe":
            return payload.get("type", "unknown")

        # Slack uses a top-level 'type' or 'event.type'
        if provider == "slack":
            event = payload.get("event", {})
            if isinstance(event, dict) and "type" in event:
                return event["type"]
            return payload.get("type", "unknown")

        # SendGrid uses an array of events
        if provider == "sendgrid":
            if isinstance(payload, list) and payload:
                return payload[0].get("event", "unknown")
            return payload.get("event", "unknown")

        # Linear uses 'type' or 'action'
        if provider == "linear":
            return payload.get("type", payload.get("action", "unknown"))

        # HubSpot uses subscriptionType
        if provider == "hubspot":
            if isinstance(payload, list) and payload:
                return payload[0].get("subscriptionType", "unknown")
            return payload.get("subscriptionType", "unknown")

        # Generic fallback
        return payload.get("event_type", payload.get("type", payload.get("event", "unknown")))

    async def _fire_triggers(
        self,
        connector: IntegrationConnector,
        event: WebhookEvent,
    ) -> None:
        """Find and execute matching triggers for a received event."""
        result = await self.session.execute(
            select(IntegrationTrigger).where(
                IntegrationTrigger.connector_id == connector.id,
                IntegrationTrigger.event_type == event.event_type,
                IntegrationTrigger.is_active == True,  # noqa: E712
            )
        )
        triggers = list(result.scalars().all())

        for trigger in triggers:
            try:
                trigger.executions += 1
                self.session.add(trigger)

                logger.info(
                    "trigger_fired",
                    trigger_id=str(trigger.id),
                    action_module=trigger.action_module,
                    event_type=event.event_type,
                )
            except Exception as e:
                logger.error(
                    "trigger_fire_failed",
                    trigger_id=str(trigger.id),
                    error=str(e),
                )

        # Mark event as processed
        event.status = "processed"
        event.processed_at = datetime.utcnow()
        self.session.add(event)
        await self.session.commit()
