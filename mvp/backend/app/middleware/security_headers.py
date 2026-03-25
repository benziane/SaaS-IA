"""
Security headers middleware.

Adds recommended security headers to every HTTP response:
- HSTS, CSP, X-Content-Type-Options, X-Frame-Options, etc.
- Cache-Control: no-store for API paths.
- Removes the Server header.

Usage:
    app.add_middleware(SecurityHeadersMiddleware)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


_DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject security headers into every response."""

    def __init__(self, app, csp_policy: str | None = None):
        super().__init__(app)
        # Pre-compute the static headers dict once at startup so we avoid
        # repeated string allocations on every request.
        self._static_headers: dict[str, str] = {
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
            "Content-Security-Policy": csp_policy or _DEFAULT_CSP,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # Apply all pre-computed security headers.
        for key, value in self._static_headers.items():
            response.headers[key] = value

        # Prevent caching of API responses.
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"

        # Remove the Server header to avoid leaking implementation details.
        response.headers.pop("Server", None)

        return response
