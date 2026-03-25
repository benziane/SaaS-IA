"""
Request logging middleware.
Logs every HTTP request with timing, status, user_id, and request_id.
Adds X-Response-Time header to responses.
"""
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.request_id import current_user_id_ctx

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs each HTTP request with:
    - Duration (ms)
    - Status code
    - Method + path
    - User ID (if authenticated)
    Skips health checks and metrics to reduce noise.
    """

    SKIP_PATHS: frozenset[str] = frozenset({
        "/health/live",
        "/health/ready",
        "/health/startup",
        "/metrics",
    })

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()

        # Extract user_id from request.state (set by auth dependency)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            current_user_id_ctx.set(str(user_id))

        try:
            response: Response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "http_request_error",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # Select log level based on status code
        if response.status_code >= 500:
            log_fn = logger.error
        elif response.status_code >= 400:
            log_fn = logger.warning
        else:
            log_fn = logger.info

        log_fn(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=request.client.host if request.client else None,
        )

        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response
