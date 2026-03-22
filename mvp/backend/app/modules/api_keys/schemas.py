"""
API Key schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    """Request to create an API key."""
    name: str = Field(..., min_length=1, max_length=100)
    permissions: list[str] = Field(default=["read", "write"])
    rate_limit_per_day: int = Field(default=1000, ge=1, le=100000)


class APIKeyRead(BaseModel):
    """API key response (without secret)."""
    id: UUID
    name: str
    key_prefix: str
    permissions: list[str]
    rate_limit_per_day: int
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreated(BaseModel):
    """Response when creating an API key (includes the secret)."""
    id: UUID
    name: str
    key: str
    key_prefix: str
    permissions: list[str]
    rate_limit_per_day: int
    message: str = "Save this key now. It will not be shown again."

    class Config:
        from_attributes = True
