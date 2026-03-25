"""
Tenant Middleware
=================

Extracts tenant_id from JWT claims or X-Tenant-ID header and sets:
1. TenantContext (contextvars) for application-level access
2. PostgreSQL session variable (app.tenant_id) for Row Level Security policies

The middleware is non-blocking for unauthenticated requests (public endpoints).
Tenant context is only set when a valid tenant_id is available.
"""

import structlog
from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import settings
from app.core.multi_tenant import TenantContext

logger = structlog.get_logger()

# Paths that should skip tenant resolution entirely
_SKIP_PATHS = frozenset({
    "/health",
    "/health/live",
    "/health/ready",
    "/health/startup",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/",
})


class TenantMiddleware(BaseHTTPMiddleware):
    """Extracts tenant_id from JWT or X-Tenant-ID header, sets PostgreSQL session variable."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip tenant resolution for health/docs/metrics endpoints
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        tenant_id = None

        try:
            # 1. Try to extract tenant_id from JWT claims (preferred)
            tenant_id = self._extract_from_jwt(request)

            # 2. Fallback: X-Tenant-ID header (for API key auth, service-to-service)
            if tenant_id is None:
                tenant_id = request.headers.get("X-Tenant-ID")

            # 3. Set context if tenant_id is available
            if tenant_id:
                TenantContext.set(tenant_id)

                # Store on request state for downstream access
                request.state.tenant_id = tenant_id

                logger.debug(
                    "tenant_context_set",
                    tenant_id=tenant_id,
                    source="jwt" if self._extract_from_jwt(request) else "header",
                    path=request.url.path,
                )

            response = await call_next(request)
            return response

        finally:
            # Always clear context to prevent leaking between requests
            TenantContext.clear()

    @staticmethod
    def _extract_from_jwt(request: Request) -> str | None:
        """Extract tenant_id from JWT Bearer token claims.

        Returns None if:
        - No Authorization header present
        - Token is invalid or expired
        - Token does not contain tenant_id claim
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            return payload.get("tenant_id")
        except JWTError:
            return None
