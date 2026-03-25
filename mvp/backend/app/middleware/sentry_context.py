"""
Sentry context enrichment middleware.

Adds per-request tags (request_id, endpoint, method, module) and user
context to every Sentry scope so that error reports contain actionable
routing and identity information.

The middleware only enriches the scope -- it never catches or suppresses
exceptions. Sentry's own ASGI integration handles capture.

Graceful: if sentry-sdk is not installed the middleware is a transparent
pass-through.

Usage:
    app.add_middleware(SentryContextMiddleware)
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.request_id import request_id_ctx

# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------

_HAS_SENTRY = False

try:
    import sentry_sdk

    _HAS_SENTRY = True
except ImportError:
    pass


def _extract_module(path: str) -> str | None:
    """
    Extract the module name from an API path.

    Expected pattern: /api/<module>/...
    Returns the module segment or None if the path does not match.
    """
    parts = path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "api":
        return parts[1]
    return None


class SentryContextMiddleware(BaseHTTPMiddleware):
    """
    Enrich Sentry scope with per-request context.

    Tags set:
        - ``request_id`` -- correlation ID from contextvars
        - ``endpoint`` -- the raw request path
        - ``method`` -- HTTP method (GET, POST, ...)
        - ``module`` -- API module name extracted from the path

    User context:
        - ``id`` -- user ID from ``request.state.user_id`` if available
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not _HAS_SENTRY:
            return await call_next(request)

        with sentry_sdk.new_scope() as scope:
            # Tags
            rid = request_id_ctx.get()
            if rid:
                scope.set_tag("request_id", rid)

            scope.set_tag("endpoint", request.url.path)
            scope.set_tag("method", request.method)

            module = _extract_module(request.url.path)
            if module:
                scope.set_tag("module", module)

            # User context
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                scope.set_user({"id": str(user_id)})

            return await call_next(request)
