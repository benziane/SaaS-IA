"""
Tenant schemas for request/response validation.
"""

import re
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# Slug validation: lowercase alphanumeric + hyphens, 3-100 chars
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]{1,98}[a-z0-9]$")


class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""

    name: str = Field(..., min_length=2, max_length=255, description="Display name")
    slug: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="URL-friendly unique identifier (lowercase, hyphens allowed)",
    )
    plan: str = Field(default="free", description="Subscription plan: free, pro, enterprise")
    config: dict[str, Any] = Field(default_factory=dict, description="Custom tenant settings")
    max_users: int = Field(default=5, ge=1, le=10000)
    max_storage_mb: int = Field(default=1000, ge=100, le=1000000)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.lower().strip()
        if not _SLUG_RE.match(v):
            raise ValueError(
                "Slug must be 3-100 chars, lowercase alphanumeric with hyphens, "
                "cannot start or end with a hyphen"
            )
        # Reserved slugs
        reserved = {"admin", "api", "app", "www", "mail", "ftp", "system", "root", "public"}
        if v in reserved:
            raise ValueError(f"Slug '{v}' is reserved")
        return v

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: str) -> str:
        allowed = {"free", "pro", "enterprise"}
        if v not in allowed:
            raise ValueError(f"Plan must be one of: {', '.join(sorted(allowed))}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corp",
                "slug": "acme-corp",
                "plan": "pro",
                "config": {"features": ["transcription", "knowledge"]},
                "max_users": 25,
                "max_storage_mb": 10000,
            }
        }


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    plan: Optional[str] = Field(None)
    is_active: Optional[bool] = None
    config: Optional[dict[str, Any]] = None
    max_users: Optional[int] = Field(None, ge=1, le=10000)
    max_storage_mb: Optional[int] = Field(None, ge=100, le=1000000)

    @field_validator("plan")
    @classmethod
    def validate_plan(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"free", "pro", "enterprise"}
        if v not in allowed:
            raise ValueError(f"Plan must be one of: {', '.join(sorted(allowed))}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Acme Corp Updated",
                "plan": "enterprise",
                "max_users": 100,
            }
        }


class BrandingUpdate(BaseModel):
    """Schema for updating tenant white-label branding."""

    logo_url: Optional[str] = Field(None, max_length=2048, description="URL to tenant logo")
    primary_color: Optional[str] = Field(
        None,
        max_length=7,
        description="Primary brand color in hex (e.g., #1976d2)",
    )
    favicon: Optional[str] = Field(None, max_length=2048, description="URL to favicon")
    custom_domain: Optional[str] = Field(
        None,
        max_length=255,
        description="Custom domain for white-label (e.g., app.acme.com)",
    )

    @field_validator("primary_color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Color must be a valid hex color (e.g., #1976d2)")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "logo_url": "https://cdn.acme.com/logo.png",
                "primary_color": "#1976d2",
                "favicon": "https://cdn.acme.com/favicon.ico",
                "custom_domain": "app.acme.com",
            }
        }


class TenantRead(BaseModel):
    """Schema for tenant response."""

    id: UUID
    name: str
    slug: str
    plan: str
    is_active: bool
    config: dict[str, Any] = Field(default_factory=dict)
    branding: dict[str, Any] = Field(default_factory=dict)
    max_users: int
    max_storage_mb: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantPublicConfig(BaseModel):
    """Public-facing tenant configuration for white-label (no auth required)."""

    name: str
    slug: str
    plan: str
    branding: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Response for listing tenants."""

    count: int
    tenants: list[TenantRead]
