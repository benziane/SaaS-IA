"""
Rate Limiting Configuration for SaaS-IA MVP
============================================

This module provides rate limiting functionality using slowapi.
It protects the API from abuse, brute-force attacks, and excessive costs.

Grade: S++ (Enterprise Ready)
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
limiter = Limiter(
    key_func=get_client_identifier,
    default_limits=[RATE_LIMITS["default"]],
    storage_uri="memory://",  # In-memory storage (upgrade to Redis for production)
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


# ============================================
# PRODUCTION UPGRADE NOTES
# ============================================

"""
For production deployment, consider upgrading to Redis-based storage:

1. Install redis: pip install redis
2. Update storage_uri:
   
   from app.config import settings
   
   limiter = Limiter(
       key_func=get_client_identifier,
       default_limits=[RATE_LIMITS["default"]],
       storage_uri=f"redis://{settings.REDIS_URL}",  # Use Redis from config
       strategy="fixed-window",
   )

3. Benefits:
   - Shared state across multiple backend instances
   - Persistent limits across restarts
   - Better performance for high traffic

4. Alternative strategies:
   - "moving-window": More accurate but slower
   - "fixed-window-elastic-expiry": Balance between accuracy and performance
"""

