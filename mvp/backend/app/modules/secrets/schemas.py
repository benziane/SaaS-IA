"""
Secrets module schemas -- request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SecretRead(BaseModel):
    """Response schema for a registered secret."""

    id: str
    name: str
    secret_type: str
    status: str
    rotation_days: int
    registered_at: str
    last_rotated_at: Optional[str] = None
    next_rotation_at: Optional[str] = None
    rotation_count: int
    age_days: int
    notes: Optional[str] = None


class SecretAlertRead(BaseModel):
    """Response schema for a secret alert."""

    name: str
    type: str
    status: str
    urgency: str
    message: str
    overdue_days: Optional[int] = None
    days_remaining: Optional[int] = None


class SecretRegisterRequest(BaseModel):
    """Request to register a new secret for tracking."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Environment variable name (e.g. GEMINI_API_KEY)",
    )
    secret_type: str = Field(
        default="api_key",
        description="Type: api_key, database, jwt, webhook, other",
    )
    rotation_days: int = Field(
        default=90,
        ge=1,
        le=730,
        description="Rotation period in days",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional notes about this secret",
    )


class SecretRotateRequest(BaseModel):
    """Request to start rotation of a secret."""

    hint: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Metadata hint (NOT the actual value), e.g. 'rotated via admin panel'",
    )


class SecretHealthRead(BaseModel):
    """Response schema for secrets health score."""

    score: int
    total: int
    healthy: int
    warning: int
    overdue: int
    compromised: int


class RotationCheckRead(BaseModel):
    """Response schema for a rotation check entry."""

    name: str
    type: str
    age_days: int
    rotation_days: int
    status: str
    urgency: str
    overdue_days: int
