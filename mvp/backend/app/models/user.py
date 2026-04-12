"""
User and Role models
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Role(str, Enum):
    """User roles"""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"


class User(SQLModel, table=True):
    """User model"""
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    role: Role = Field(default=Role.USER)
    is_active: bool = Field(default=True)
    email_verified: bool = Field(default=False)
    tenant_id: Optional[UUID] = Field(
        default=None,
        foreign_key="tenants.id",
        index=True,
        description="FK to tenants table for multi-tenant RLS isolation",
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "role": "user",
                "is_active": True
            }
        }

