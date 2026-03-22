"""
API Key models for public API authentication.
"""

import secrets
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class APIKey(SQLModel, table=True):
    """API key for authenticating public API requests."""
    __tablename__ = "api_keys"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    key_hash: str = Field(max_length=255)
    key_prefix: str = Field(max_length=8)
    permissions_json: str = Field(default='["read", "write"]')
    rate_limit_per_day: int = Field(default=1000)
    is_active: bool = Field(default=True)
    last_used_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)
