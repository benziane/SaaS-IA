"""
Prometheus metrics collection for production monitoring.

Defines application-level metrics and a FastAPI middleware to record
HTTP request counts, durations, and in-flight request gauges automatically.
"""

import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from prometheus_client import Counter, Histogram, Gauge


# ---------------------------------------------------------------------------
# HTTP metrics
# ---------------------------------------------------------------------------

http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

active_requests = Gauge(
    "active_requests",
    "Number of in-flight HTTP requests",
)

# ---------------------------------------------------------------------------
# Business metrics
# ---------------------------------------------------------------------------

transcription_jobs_total = Counter(
    "transcription_jobs_total",
    "Total number of transcription jobs by outcome",
    ["status"],
)

ai_provider_requests_total = Counter(
    "ai_provider_requests_total",
    "Total number of AI provider requests",
    ["provider", "success"],
)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Records Prometheus metrics for every HTTP request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Normalise the path so high-cardinality IDs do not explode label
        # cardinality.  We use the matched route template when available,
        # otherwise fall back to the raw path.
        endpoint = request.url.path

        # Attempt to resolve the route template (e.g. /api/transcription/{id})
        route = request.scope.get("route")
        if route and hasattr(route, "path"):
            endpoint = route.path

        method = request.method

        active_requests.inc()
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            # Record a 500 for unhandled exceptions, then re-raise so the
            # default exception handler still fires.
            duration = time.perf_counter() - start
            http_requests_total.labels(
                method=method, endpoint=endpoint, status_code="500"
            ).inc()
            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)
            active_requests.dec()
            raise

        duration = time.perf_counter() - start
        status_code = str(response.status_code)

        http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).inc()
        http_request_duration_seconds.labels(
            method=method, endpoint=endpoint
        ).observe(duration)
        active_requests.dec()

        return response
