"""
Sliding Window Rate Limiter Middleware
======================================

Advanced rate limiting using Redis sorted sets for accurate sliding windows.
Provides per-minute and per-burst (10s) windows with proper HTTP headers.

This middleware COEXISTS with the existing slowapi-based rate_limit.py.
The slowapi limiter handles per-endpoint limits; this middleware adds
global sliding-window + burst protection at the middleware layer.

Architecture:
  - Uses Redis sorted sets (ZADD/ZCARD) for O(log N) sliding windows
  - Two windows: per-minute (100 req) and per-burst (20 req / 10s)
  - Fail-open: if Redis is unavailable, requests pass through
  - Identifier: authenticated user_id > X-Forwarded-For > client IP
"""

import hashlib
import time
from typing import Optional

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Bypass lists
# ---------------------------------------------------------------------------

WHITELISTED_IPS = frozenset({"127.0.0.1", "::1"})

EXEMPT_PATHS = frozenset({
    "/health/live",
    "/health/ready",
    "/health/startup",
    "/metrics",
})

# ---------------------------------------------------------------------------
# Sliding Window Rate Limiter (Redis sorted sets)
# ---------------------------------------------------------------------------


class SlidingWindowRateLimiter:
    """
    Token-bucket-style rate limiter backed by Redis sorted sets.

    Each request is stored as a member with its timestamp as the score.
    Old entries are pruned on every check, giving a true sliding window.
    """

    def __init__(
        self,
        redis_client,
        max_requests: int = 100,
        window_seconds: int = 60,
        burst_size: int = 20,
        burst_window: int = 10,
    ):
        self._redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.burst_size = burst_size
        self.burst_window = burst_window

    @staticmethod
    def _key(identifier: str, window: str) -> str:
        """Build a Redis key for the given identifier and window name."""
        digest = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return f"ratelimit:{window}:{digest}"

    async def check(self, identifier: str) -> tuple[bool, dict]:
        """
        Check whether the request should be allowed.

        Returns:
            (allowed, headers_dict)
            - allowed: True if the request may proceed
            - headers_dict: rate-limit HTTP headers to attach to the response
        """
        now = time.time()
        member = f"{now}"  # unique-ish member per request

        minute_key = self._key(identifier, "minute")
        burst_key = self._key(identifier, "burst")

        minute_floor = now - self.window_seconds
        burst_floor = now - self.burst_window

        pipe = self._redis.pipeline(transaction=False)

        # --- minute window ---
        pipe.zremrangebyscore(minute_key, 0, minute_floor)
        pipe.zadd(minute_key, {member: now})
        pipe.zcard(minute_key)
        pipe.expire(minute_key, self.window_seconds + 1)

        # --- burst window ---
        burst_member = f"{now}:burst"
        pipe.zremrangebyscore(burst_key, 0, burst_floor)
        pipe.zadd(burst_key, {burst_member: now})
        pipe.zcard(burst_key)
        pipe.expire(burst_key, self.burst_window + 1)

        results = await pipe.execute()

        minute_count: int = results[2]
        burst_count: int = results[6]

        minute_remaining = max(0, self.max_requests - minute_count)
        reset_at = int(now) + self.window_seconds

        headers: dict[str, str] = {
            "X-RateLimit-Limit": str(self.max_requests),
            "X-RateLimit-Remaining": str(minute_remaining),
            "X-RateLimit-Reset": str(reset_at),
        }

        # Block if either window is exceeded
        if minute_count > self.max_requests:
            headers["Retry-After"] = str(self.window_seconds)
            return False, headers

        if burst_count > self.burst_size:
            headers["Retry-After"] = str(self.burst_window)
            return False, headers

        return True, headers


# ---------------------------------------------------------------------------
# ASGI Middleware
# ---------------------------------------------------------------------------


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that enforces sliding-window rate limiting.

    Fail-open: if Redis is unreachable the request is allowed through
    with a logged warning, ensuring availability is never degraded by
    the rate-limiter infrastructure itself.
    """

    def __init__(self, app, requests_per_minute: int = 100, burst_size: int = 20):
        super().__init__(app)
        self._requests_per_minute = requests_per_minute
        self._burst_size = burst_size
        self._limiter: Optional[SlidingWindowRateLimiter] = None
        self._redis_init_attempted = False

    async def _ensure_limiter(self) -> Optional[SlidingWindowRateLimiter]:
        """Lazy-init the limiter on first request (needs async Redis)."""
        if self._limiter is not None:
            return self._limiter
        if self._redis_init_attempted:
            return None

        self._redis_init_attempted = True
        try:
            from app.cache import _get_redis

            redis_client = await _get_redis()
            if redis_client is None:
                logger.warning("sliding_rate_limiter_disabled", reason="redis_unavailable")
                return None

            self._limiter = SlidingWindowRateLimiter(
                redis_client=redis_client,
                max_requests=self._requests_per_minute,
                burst_size=self._burst_size,
            )
            logger.info(
                "sliding_rate_limiter_ready",
                max_requests=self._requests_per_minute,
                burst_size=self._burst_size,
            )
            return self._limiter
        except Exception as exc:
            logger.warning("sliding_rate_limiter_init_error", error=str(exc))
            return None

    @staticmethod
    def _get_identifier(request: Request) -> str:
        """
        Derive a stable identifier for the request source.

        Priority:
        1. Authenticated user id (set on request.state by auth middleware)
        2. First IP in X-Forwarded-For header (behind reverse proxy)
        3. Direct client IP
        """
        # Authenticated user
        if hasattr(request.state, "user") and request.state.user:
            user_id = getattr(request.state.user, "id", None)
            if user_id:
                return f"user:{user_id}"

        # Proxy-forwarded IP
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()

        # Direct client
        if request.client and request.client.host:
            return request.client.host

        return "unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Skip exempt paths
        if path in EXEMPT_PATHS:
            return await call_next(request)

        # Skip whitelisted IPs
        client_ip = request.client.host if request.client else None
        if client_ip in WHITELISTED_IPS:
            return await call_next(request)

        # Fail-open: if limiter is unavailable, let the request through
        try:
            limiter = await self._ensure_limiter()
            if limiter is None:
                return await call_next(request)

            identifier = self._get_identifier(request)
            allowed, headers = await limiter.check(identifier)
        except Exception as exc:
            # Fail open on any Redis / runtime error
            logger.warning(
                "sliding_rate_limiter_error",
                path=path,
                error=str(exc),
            )
            return await call_next(request)

        if not allowed:
            logger.warning(
                "sliding_rate_limit_exceeded",
                identifier=identifier,
                path=path,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please slow down.",
                    "retry_after": headers.get("Retry-After", "60"),
                },
                headers=headers,
            )

        # Allowed -- forward and attach rate-limit headers
        response: Response = await call_next(request)
        for hdr_name, hdr_value in headers.items():
            response.headers[hdr_name] = hdr_value
        return response
