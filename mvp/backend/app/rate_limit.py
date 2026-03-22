"""
Rate Limiting Configuration for SaaS-IA MVP
============================================

This module provides rate limiting functionality using slowapi.
It protects the API from abuse, brute-force attacks, and excessive costs.

Storage backend:
  - Redis (when REDIS_URL is configured and reachable) -- shared across instances
  - In-memory fallback (local development or when Redis is unavailable)
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()

# ============================================
# RATE LIMIT CONFIGURATION
# ============================================

# Rate limits by endpoint category
RATE_LIMITS = {
    # Authentication endpoints (strict - anti-brute force)
    "auth_register": "5/minute",
    "auth_login": "5/minute",
    "auth_me": "20/minute",

    # Transcription endpoints (moderate - API cost control)
    "transcription_create": "10/minute",
    "transcription_upload": "5/minute",
    "transcription_get": "30/minute",
    "transcription_list": "20/minute",
    "transcription_delete": "10/minute",

    # Public endpoints (permissive - monitoring)
    "health": "100/minute",
    "docs": "50/minute",

    # Default global limit
    "default": "100/minute",
}

# ============================================
# STORAGE BACKEND SELECTION
# ============================================

def _resolve_storage_uri() -> str:
    """
    Determine the storage URI for the rate limiter.

    Returns a Redis URI when REDIS_URL is configured and the redis package
    is importable, otherwise falls back to in-memory storage.
    """
    from app.config import settings

    redis_url = (settings.REDIS_URL or "").strip()
    if not redis_url:
        logger.info("rate_limit_storage", backend="memory", reason="REDIS_URL not configured")
        return "memory://"

    # Verify the redis package is installed
    try:
        import redis  # noqa: F401
    except ImportError:
        logger.warning(
            "rate_limit_storage",
            backend="memory",
            reason="redis package not installed; falling back to in-memory storage",
        )
        return "memory://"

    # Validate basic connectivity so we fail fast at startup rather than
    # on the first request.
    try:
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=3)
        client.ping()
        client.close()
    except Exception as exc:
        logger.warning(
            "rate_limit_storage",
            backend="memory",
            reason="Redis is unreachable; falling back to in-memory storage",
            error=str(exc),
        )
        return "memory://"

    logger.info("rate_limit_storage", backend="redis", url=redis_url)
    return redis_url


# ============================================
# LIMITER INSTANCE
# ============================================

def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting.

    Priority:
    1. User ID (if authenticated)
    2. IP Address (fallback)

    This ensures authenticated users have separate limits from their IP.
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        user_id = getattr(request.state.user, "id", None)
        if user_id:
            return f"user:{user_id}"

    # Fallback to IP address
    return get_remote_address(request)


# Initialize limiter with custom key function
_storage_uri = _resolve_storage_uri()

limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[RATE_LIMITS["default"]],
    storage_uri=_storage_uri,
    strategy="fixed-window",  # Simple and fast
)

# ============================================
# ERROR HANDLER
# ============================================

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors.
    
    Returns a clear JSON response with retry information.
    """
    # Extract rate limit info
    limit = exc.detail.split(":")[0] if ":" in exc.detail else "Unknown"
    
    # Log the rate limit event
    logger.warning(
        "rate_limit_exceeded",
        client=get_client_identifier(request),
        path=request.url.path,
        limit=limit,
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded: {limit}",
            "detail": "Too many requests. Please wait before trying again.",
            "retry_after": "60 seconds",  # Fixed window = 1 minute
        },
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": limit,
        },
    )

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_rate_limit(category: str) -> str:
    """
    Get rate limit for a specific category.
    
    Args:
        category: Rate limit category (e.g., "auth_login", "transcription_create")
    
    Returns:
        Rate limit string (e.g., "5/minute")
    """
    return RATE_LIMITS.get(category, RATE_LIMITS["default"])



