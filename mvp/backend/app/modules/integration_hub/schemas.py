"""
Integration Hub schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConnectorCreate(BaseModel):
    """Request to create a new integration connector."""
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(..., description="Connector type: webhook, oauth2, api_key")
    provider: str = Field(default="custom", max_length=50, description="Provider slug: slack, github, stripe, etc.")
    config: dict = Field(default_factory=dict, description="Provider-specific configuration")
    enabled: bool = Field(default=True)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Stripe Payments",
                "type": "webhook",
                "provider": "stripe",
                "config": {"events": ["payment_intent.succeeded", "invoice.paid"]},
                "enabled": True,
            }
        }


class ConnectorRead(BaseModel):
    """Connector response schema."""
    id: UUID
    user_id: UUID
    name: str
    type: str
    provider: str
    status: str
    webhook_url: Optional[str] = None
    events_received: int
    last_event_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookEventRead(BaseModel):
    """Webhook event response schema."""
    id: UUID
    connector_id: UUID
    event_type: str
    payload: dict
    status: str
    processed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TriggerCreate(BaseModel):
    """Request to create an event trigger."""
    connector_id: UUID
    event_type: str = Field(..., min_length=1, max_length=200)
    action_module: str = Field(..., min_length=1, max_length=100, description="Target module: transcription, knowledge, content_studio, etc.")
    action_config: dict = Field(default_factory=dict, description="Configuration passed to the action module")

    class Config:
        json_schema_extra = {
            "example": {
                "connector_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "push",
                "action_module": "knowledge",
                "action_config": {"auto_index": True},
            }
        }


class TriggerRead(BaseModel):
    """Trigger response schema."""
    id: UUID
    connector_id: UUID
    event_type: str
    action_module: str
    action_config: dict
    is_active: bool
    executions: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProviderInfo(BaseModel):
    """Supported provider information."""
    slug: str
    name: str
    description: str
    supported_types: list[str]
    icon: str
    events: list[str]
