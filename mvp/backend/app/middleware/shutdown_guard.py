"""
Shutdown guard middleware.

Returns 503 Service Unavailable for new requests once the application
has entered the shutdown phase, while allowing in-flight requests to
complete naturally.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.lifecycle import is_shutting_down, _increment_active, _decrement_active


class ShutdownGuardMiddleware(BaseHTTPMiddleware):
    """
    Reject incoming requests during graceful shutdown.

    When the application is shutting down:
      - New requests receive a 503 with ``Connection: close`` and
        ``Retry-After: 30`` headers so clients know to reconnect later.
      - In-flight requests (accepted before shutdown) are tracked via the
        active-request counter and allowed to finish.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if is_shutting_down():
            return JSONResponse(
                status_code=503,
                content={"detail": "Server is shutting down"},
                headers={
                    "Connection": "close",
                    "Retry-After": "30",
                },
            )

        await _increment_active()
        try:
            response = await call_next(request)
            return response
        finally:
            await _decrement_active()
