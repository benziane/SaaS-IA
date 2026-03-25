"""
Request ID middleware with contextvars propagation.

Assigns a unique request ID to every incoming HTTP request, making it
available via contextvars for downstream logging and tracing. The ID is
read from the X-Request-ID header if provided by an upstream proxy,
otherwise a new one is generated.
"""

from contextvars import ContextVar
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# ── Context variables ────────────────────────────────────────────────────────

request_id_ctx: ContextVar[str] = ContextVar("request_id_ctx", default="")
current_user_id_ctx: ContextVar[str] = ContextVar("current_user_id_ctx", default="anonymous")


def get_request_id() -> str:
    """Return the current request ID from contextvars."""
    return request_id_ctx.get()


# ── Middleware ───────────────────────────────────────────────────────────────

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every request has a unique correlation ID.

    - Reads ``X-Request-ID`` from the incoming request headers.
    - If missing, generates a new hex UUID.
    - Stores the ID in a ContextVar so any code in the same async context
      can access it (loggers, services, tasks).
    - Copies the ID into ``request.state.request_id`` for convenience.
    - Echoes the ID back in the ``X-Request-ID`` response header.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        rid = request.headers.get("X-Request-ID") or uuid4().hex

        # Bind to contextvars
        token = request_id_ctx.set(rid)

        # Also store on request.state for easy access in route handlers
        request.state.request_id = rid

        try:
            response: Response = await call_next(request)
        finally:
            # Reset contextvar to avoid leaking across requests
            request_id_ctx.reset(token)

        response.headers["X-Request-ID"] = rid
        return response
