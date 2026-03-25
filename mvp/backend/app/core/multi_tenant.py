"""
Multi-Tenant Infrastructure
============================

Thread-safe tenant context using contextvars and tenant management service.
Supports RLS (Row Level Security) via PostgreSQL session variables.

Usage:
    # In middleware: set tenant context from JWT
    TenantContext.set(tenant_id)

    # In services: get current tenant
    tenant_id = TenantContext.require()  # raises 403 if not set

    # In DB session: set PostgreSQL session variable for RLS
    await session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})
"""

from contextvars import ContextVar
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status

# ---------------------------------------------------------------------------
# TenantContext: Thread-safe (async-safe) tenant ID propagation
# ---------------------------------------------------------------------------

class TenantContext:
    """Thread-safe tenant context using contextvars.

    Each async task/request gets its own copy of the context variable,
    ensuring tenant isolation even under concurrent requests.
    """

    _tenant_id: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)

    @classmethod
    def set(cls, tenant_id: str) -> None:
        """Set the current tenant ID for the request context."""
        cls._tenant_id.set(tenant_id)

    @classmethod
    def get(cls) -> Optional[str]:
        """Get the current tenant ID, or None if not set."""
        return cls._tenant_id.get()

    @classmethod
    def require(cls) -> str:
        """Get the current tenant ID or raise HTTP 403.

        Use this in endpoints/services that require tenant context.

        Raises:
            HTTPException: 403 if tenant context is not set.
        """
        tenant_id = cls._tenant_id.get()
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant context required. Ensure tenant_id is in JWT or X-Tenant-ID header.",
            )
        return tenant_id

    @classmethod
    def clear(cls) -> None:
        """Clear the tenant context (called in middleware finally block)."""
        cls._tenant_id.set(None)

    @classmethod
    def get_uuid(cls) -> Optional[UUID]:
        """Get the current tenant ID as UUID, or None."""
        tid = cls._tenant_id.get()
        if tid is None:
            return None
        try:
            return UUID(tid)
        except ValueError:
            return None

    @classmethod
    def require_uuid(cls) -> UUID:
        """Get the current tenant ID as UUID or raise HTTP 403."""
        tid = cls.require()
        try:
            return UUID(tid)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid tenant_id format. Expected UUID.",
            )
