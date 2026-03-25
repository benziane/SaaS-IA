"""
GZip compression middleware with path & SSE exclusions.

Wraps Starlette's built-in GZipMiddleware and skips compression for:
- Health / metrics endpoints (Prometheus scrapes expect raw text).
- Server-Sent Events streams (chunked transfer, must not be buffered).

Usage:
    app.add_middleware(CompressionMiddleware)
"""

from __future__ import annotations

from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

EXCLUDED_PATHS: set[str] = {
    "/metrics",
    "/health/live",
    "/health/ready",
    "/health/startup",
}


class CompressionMiddleware:
    """GZip middleware that skips excluded paths and SSE responses."""

    def __init__(self, app: ASGIApp, minimum_size: int = 500) -> None:
        self.app = app
        self.gzip = GZipMiddleware(app, minimum_size=minimum_size)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")

        # Skip compression for excluded paths
        if path in EXCLUDED_PATHS:
            await self.app(scope, receive, send)
            return

        # Skip compression for SSE (text/event-stream)
        headers = dict(scope.get("headers", []))
        accept = headers.get(b"accept", b"").decode("latin-1", errors="replace")
        if "text/event-stream" in accept:
            await self.app(scope, receive, send)
            return

        # Delegate to Starlette GZipMiddleware
        await self.gzip(scope, receive, send)
