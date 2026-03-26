"""
Audit Middleware
================

Automatically logs write operations (POST, PUT, DELETE, PATCH) on /api/* endpoints.
Captures login/logout events, extracts user/tenant context, and fires audit records
in the background without blocking the response.

Skips: health checks, metrics, GET requests, WebSocket upgrades, docs endpoints.
"""

import asyncio

import structlog
from fastapi import Request
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config import settings
from app.core.audit_log import AuditAction, AuditLogger
from app.core.multi_tenant import TenantContext

logger = structlog.get_logger()

# HTTP methods that represent write operations
_WRITE_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})

# Paths to skip entirely
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

# Path prefixes to skip
_SKIP_PREFIXES = (
    "/ws",
)

# Map specific auth paths to audit actions
_AUTH_ACTION_MAP = {
    "/api/auth/login": AuditAction.LOGIN,
    "/api/auth/logout": AuditAction.LOGOUT,
    "/api/auth/logout-all": AuditAction.LOGOUT,
    "/api/auth/register": AuditAction.CREATE,
}

# Map HTTP methods to audit actions
_METHOD_ACTION_MAP = {
    "POST": AuditAction.CREATE,
    "PUT": AuditAction.UPDATE,
    "PATCH": AuditAction.UPDATE,
    "DELETE": AuditAction.DELETE,
}


def _extract_ip(request: Request) -> str | None:
    """Extract client IP, only trusting X-Forwarded-For from trusted proxies."""
    client_ip = request.client.host if request.client else None

    trusted_proxies = settings.trusted_proxies_set
    if trusted_proxies and client_ip in trusted_proxies:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

    return client_ip


def _extract_user_id(request: Request) -> str | None:
    """Extract user_id from request state or JWT token (best-effort)."""
    # Try request.state first (set by auth middleware/dependencies)
    user_id = getattr(getattr(request, "state", None), "user_id", None)
    if user_id:
        return str(user_id)

    # Fallback: decode JWT without full validation (just to get sub claim)
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # sub is email in this codebase, but we still log it as user identifier
        return payload.get("sub")
    except JWTError:
        return None


def _extract_resource_info(path: str) -> tuple[str, str | None]:
    """Extract resource_type and resource_id from API path.

    Examples:
        /api/transcription/abc-123  -> ("transcription", "abc-123")
        /api/knowledge/documents    -> ("knowledge", None)
        /api/auth/login             -> ("auth", None)
    """
    parts = path.strip("/").split("/")

    # Expect at least /api/<resource>
    if len(parts) < 2:
        return (parts[-1] if parts else "unknown", None)

    # Skip the "api" prefix
    resource_parts = parts[1:] if parts[0] == "api" else parts

    resource_type = resource_parts[0] if resource_parts else "unknown"
    resource_id = None

    # If there are more parts, the last segment might be a resource ID
    if len(resource_parts) >= 2:
        last = resource_parts[-1]
        # Heuristic: if it looks like a UUID or numeric ID, treat as resource_id
        if len(last) > 8 and "-" in last:
            resource_id = last
        elif last.isdigit():
            resource_id = last

    return resource_type, resource_id


class AuditMiddleware(BaseHTTPMiddleware):
    """Logs write operations to the immutable audit log (fire-and-forget)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method

        # Skip non-API, non-write, and excluded paths
        if method == "GET" or method == "OPTIONS" or method == "HEAD":
            return await call_next(request)

        if path in _SKIP_PATHS:
            return await call_next(request)

        if any(path.startswith(prefix) for prefix in _SKIP_PREFIXES):
            return await call_next(request)

        # WebSocket upgrade
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        # Process the request first
        response = await call_next(request)

        # Only log if the response is not a client error (4xx) for non-auth paths
        # Auth events (login failures) are still interesting to log
        is_auth_path = path in _AUTH_ACTION_MAP
        if not is_auth_path and response.status_code >= 400:
            return response

        # Determine audit action
        action = _AUTH_ACTION_MAP.get(path)
        if action is None:
            action = _METHOD_ACTION_MAP.get(method, AuditAction.EXECUTE)

        # Extract context
        user_id = _extract_user_id(request)
        tenant_id = TenantContext.get()
        ip_address = _extract_ip(request)
        user_agent = request.headers.get("User-Agent", "")[:512]
        resource_type, resource_id = _extract_resource_info(path)

        details = {
            "method": method,
            "path": path,
            "status_code": response.status_code,
        }

        # Fire-and-forget: schedule the audit log write without blocking
        asyncio.ensure_future(
            self._safe_log(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                user_id=user_id,
                tenant_id=tenant_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        )

        return response

    @staticmethod
    async def _safe_log(**kwargs) -> None:
        """Log an audit event, swallowing any exceptions."""
        try:
            await AuditLogger.log(**kwargs)
        except Exception as exc:
            logger.error("audit_middleware_log_failed", error=str(exc))
