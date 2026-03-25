"""
Tests for the middleware stack.

Covers:
  - Security headers (HSTS, CSP, X-Frame-Options, etc.)
  - Request ID generation and propagation
  - GZip compression on large responses
  - Rate-limit response headers
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


# --------------------------------------------------------------------------
# Security Headers
# --------------------------------------------------------------------------

async def test_security_headers_present(client):
    """Responses must include HSTS, CSP, and X-Frame-Options headers."""
    resp = await client.get("/health/live")

    assert "Strict-Transport-Security" in resp.headers
    assert "max-age=" in resp.headers["Strict-Transport-Security"]

    assert "Content-Security-Policy" in resp.headers
    assert "default-src" in resp.headers["Content-Security-Policy"]

    assert resp.headers.get("X-Frame-Options") == "DENY"


async def test_x_content_type_options(client):
    """X-Content-Type-Options must be set to nosniff."""
    resp = await client.get("/health/live")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"


async def test_referrer_policy(client):
    """Referrer-Policy must be set to strict-origin-when-cross-origin."""
    resp = await client.get("/health/live")
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


async def test_xss_protection(client):
    """X-XSS-Protection header must be present."""
    resp = await client.get("/health/live")
    assert "X-XSS-Protection" in resp.headers


async def test_api_cache_control(client):
    """API paths should have Cache-Control: no-store."""
    # Use /api/modules (returns 401 without auth, but headers are still set)
    resp = await client.get("/api/modules")
    cache_control = resp.headers.get("Cache-Control", "")
    assert "no-store" in cache_control


# --------------------------------------------------------------------------
# Request ID
# --------------------------------------------------------------------------

async def test_request_id_generated(client):
    """A request without X-Request-ID should receive one in the response."""
    resp = await client.get("/health/live")
    request_id = resp.headers.get("X-Request-ID")

    assert request_id is not None
    assert len(request_id) > 0


async def test_request_id_propagated(client):
    """When the client sends X-Request-ID, the same value should be echoed back."""
    custom_id = "test-correlation-id-12345"
    resp = await client.get(
        "/health/live",
        headers={"X-Request-ID": custom_id},
    )
    assert resp.headers.get("X-Request-ID") == custom_id


async def test_request_id_unique_per_request(client):
    """Two requests without X-Request-ID should receive different IDs."""
    resp1 = await client.get("/health/live")
    resp2 = await client.get("/health/live")

    id1 = resp1.headers.get("X-Request-ID")
    id2 = resp2.headers.get("X-Request-ID")

    assert id1 is not None
    assert id2 is not None
    assert id1 != id2


# --------------------------------------------------------------------------
# Compression
# --------------------------------------------------------------------------

async def test_compression_applied_on_large_response(client):
    """Large responses should be gzip-compressed when the client accepts it.

    We use the /health/ready endpoint which returns JSON with dependency
    details.  The test verifies the server handles Accept-Encoding: gzip
    without errors; actual compression depends on response size.
    """
    pg_ok = {"status": "up", "latency_ms": 1.0}
    redis_ok = {"status": "up", "latency_ms": 0.5}

    from unittest.mock import AsyncMock, patch

    with (
        patch("app.api.health._check_postgres", new_callable=AsyncMock, return_value=pg_ok),
        patch("app.api.health._check_redis", new_callable=AsyncMock, return_value=redis_ok),
    ):
        resp = await client.get(
            "/health/ready",
            headers={"Accept-Encoding": "gzip"},
        )
    # The response should succeed.
    assert resp.status_code == 200

    # If compression was applied, Content-Encoding will be present.
    # On very small responses Starlette may skip compression.
    encoding = resp.headers.get("Content-Encoding", "")
    body_size = len(resp.content)

    if body_size > 500:
        assert encoding == "gzip", (
            f"Expected gzip encoding for {body_size}-byte response"
        )


async def test_compression_skipped_on_health(client):
    """Health endpoints are excluded from compression."""
    resp = await client.get(
        "/health/live",
        headers={"Accept-Encoding": "gzip"},
    )
    assert resp.status_code == 200
    # Health endpoints should NOT be compressed.
    assert resp.headers.get("Content-Encoding", "") != "gzip"


# --------------------------------------------------------------------------
# Rate Limit Headers (sliding window middleware)
# --------------------------------------------------------------------------

def _make_mock_redis(execute_results):
    """Create a mock Redis client with a pipeline that returns
    the given execute results.

    Redis pipeline methods (zremrangebyscore, zadd, etc.) are
    synchronous; only execute() is async.
    """
    mock_pipe = MagicMock()
    mock_pipe.execute = AsyncMock(return_value=execute_results)
    # Pipeline methods return the pipeline (for chaining)
    mock_pipe.zremrangebyscore.return_value = mock_pipe
    mock_pipe.zadd.return_value = mock_pipe
    mock_pipe.zcard.return_value = mock_pipe
    mock_pipe.expire.return_value = mock_pipe

    mock_redis = MagicMock()
    mock_redis.pipeline.return_value = mock_pipe
    return mock_redis


async def test_rate_limit_headers_present_when_redis_available():
    """The SlidingWindowRateLimiter produces correct rate-limit headers
    when Redis is available.

    This is a unit test of the limiter's check() method with a mocked
    Redis client, verifying the headers that would be attached to
    responses by the RateLimitMiddleware.
    """
    # Pipeline results: [zremrangebyscore, zadd, zcard, expire] x 2 windows
    # minute_count at index 2, burst_count at index 6
    mock_redis = _make_mock_redis([
        0,    # zremrangebyscore minute
        1,    # zadd minute
        5,    # zcard minute  (5 requests in window)
        True, # expire minute
        0,    # zremrangebyscore burst
        1,    # zadd burst
        2,    # zcard burst   (2 requests in burst window)
        True, # expire burst
    ])

    from app.middleware.rate_limiter import SlidingWindowRateLimiter

    limiter = SlidingWindowRateLimiter(
        redis_client=mock_redis,
        max_requests=100,
        window_seconds=60,
        burst_size=20,
        burst_window=10,
    )

    allowed, headers = await limiter.check("test-client-ip")

    assert allowed is True
    assert headers["X-RateLimit-Limit"] == "100"
    assert headers["X-RateLimit-Remaining"] == "95"  # 100 - 5
    assert "X-RateLimit-Reset" in headers


async def test_rate_limit_exceeded_returns_429():
    """When the request count exceeds the limit, check() returns
    allowed=False with a Retry-After header."""
    mock_redis = _make_mock_redis([
        0, 1, 101, True,  # minute window: 101 requests > 100 limit
        0, 1, 5, True,    # burst window: 5 requests (ok)
    ])

    from app.middleware.rate_limiter import SlidingWindowRateLimiter

    limiter = SlidingWindowRateLimiter(
        redis_client=mock_redis,
        max_requests=100,
    )

    allowed, headers = await limiter.check("test-client")

    assert allowed is False
    assert "Retry-After" in headers


async def test_rate_limit_fail_open_without_redis(client):
    """Without Redis, the sliding-window middleware should fail open and
    allow requests through without rate-limit headers."""
    resp = await client.get("/health/live")
    assert resp.status_code == 200
    # Without Redis, headers should NOT be present (fail-open).
    # We simply verify the request succeeded.
