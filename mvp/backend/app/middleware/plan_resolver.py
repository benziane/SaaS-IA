"""
Plan Resolver Middleware
========================

Lightweight ASGI middleware that extracts the user's billing plan from the
JWT token and sets it on a context variable before the request reaches
the route handler and SlowAPI rate limiting.

This allows dynamic rate limits to scale based on the user's plan without
needing a database lookup on every request:

1. Decode the JWT token (without verifying the user still exists -- that
   is handled later by the auth dependency).
2. Look up the plan from a short-lived in-memory cache keyed by user email.
3. On cache miss, query the database and cache the result for 5 minutes.
4. Set the plan name on the ``_current_plan_name`` context variable.

The cache ensures that the vast majority of requests incur no extra DB cost.
"""

import time
from typing import Dict, Optional, Tuple

import structlog
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.rate_limit_dynamic import set_current_plan

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Lightweight in-memory plan cache: email -> (plan_name, expiry_timestamp)
# TTL = 5 minutes.  The cache is bounded -- entries are evicted on access
# if expired, and the entire cache is cleared if it grows beyond 10 000
# entries (a safety valve for very large deployments).
# ---------------------------------------------------------------------------
_CACHE_TTL = 300  # seconds
_CACHE_MAX = 10_000

_plan_cache: Dict[str, Tuple[str, float]] = {}


def _cache_get(email: str) -> Optional[str]:
    """Return cached plan name if still valid, else None."""
    entry = _plan_cache.get(email)
    if entry is None:
        return None
    plan_name, expires_at = entry
    if time.monotonic() > expires_at:
        _plan_cache.pop(email, None)
        return None
    return plan_name


def _cache_set(email: str, plan_name: str) -> None:
    """Store plan name in cache with TTL."""
    if len(_plan_cache) >= _CACHE_MAX:
        _plan_cache.clear()
    _plan_cache[email] = (plan_name, time.monotonic() + _CACHE_TTL)


def invalidate_plan_cache(email: Optional[str] = None) -> None:
    """
    Invalidate the plan cache for a specific user or all users.

    Call this when a user upgrades/downgrades their plan so the new
    rate limits take effect immediately.
    """
    if email:
        _plan_cache.pop(email, None)
    else:
        _plan_cache.clear()


class PlanResolverMiddleware(BaseHTTPMiddleware):
    """
    Resolve the authenticated user's billing plan and set it on the
    context variable used by dynamic rate limiting.

    This middleware is intentionally lightweight:
    - JWT decoding is fast (no DB hit).
    - Plan lookup is cached in memory for 5 minutes.
    - On any failure, defaults to "free" (most restrictive limits).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        plan_name = "free"

        try:
            plan_name = await self._resolve_plan(request)
        except Exception:
            # Never let plan resolution break the request
            pass

        # Set on context variable (read by dynamic_limit callables)
        set_current_plan(plan_name)

        # Also set on request.state for downstream use
        request.state.plan_name = plan_name

        response = await call_next(request)
        return response

    async def _resolve_plan(self, request: Request) -> str:
        """Extract plan name from JWT + cache, falling back to 'free'."""
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return "free"

        token = auth_header[7:]  # strip "Bearer "

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except JWTError:
            return "free"

        # Reject refresh tokens
        if payload.get("type") == "refresh":
            return "free"

        email = payload.get("sub")
        if not email:
            return "free"

        # Check cache first
        cached = _cache_get(email)
        if cached is not None:
            return cached

        # Cache miss -- look up in DB
        plan_name = await self._lookup_plan(email)
        _cache_set(email, plan_name)

        return plan_name

    async def _lookup_plan(self, email: str) -> str:
        """Query the database for the user's current plan name."""
        try:
            from app.database import get_session_context
            from app.models.user import User
            from app.modules.billing.service import BillingService
            from sqlmodel import select

            async with get_session_context() as session:
                result = await session.execute(
                    select(User).where(User.email == email)
                )
                user = result.scalar_one_or_none()
                if not user:
                    return "free"

                _quota, plan = await BillingService.get_user_quota(
                    user.id, session
                )
                return plan.name.value if plan and plan.name else "free"

        except Exception as exc:
            logger.debug(
                "plan_lookup_failed",
                email=email,
                error=str(exc),
            )
            return "free"
