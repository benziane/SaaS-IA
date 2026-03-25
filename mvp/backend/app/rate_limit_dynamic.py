"""
Dynamic rate limiting based on user billing plan.
=================================================

Provides plan-aware rate limits that scale with the user's subscription tier.
Free users get base limits, Pro users get 3x, and Enterprise users get 10x.

The rate limits are enforced in two layers:
1. SlowAPI rate limiting (per-endpoint, per-user/IP, per time window)
2. Billing quota middleware (per-user, per-month, resource-based)

Architecture:
- A context variable (`_current_plan_name`) is set by PlanResolverMiddleware
  before the request reaches the route handler.
- The `dynamic_limit(endpoint_key)` factory returns a callable that SlowAPI
  invokes to determine the limit string for the current request.
- The callable reads the plan name from the context variable and multiplies
  the base limit accordingly.

Usage in routes::

    from app.rate_limit import limiter
    from app.rate_limit_dynamic import dynamic_limit

    @router.post("/create")
    @limiter.limit(dynamic_limit("transcription_create"))
    async def create_transcription(request: Request, ...):
        ...
"""

from contextvars import ContextVar
from typing import Optional

import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Context variable set by PlanResolverMiddleware
# ---------------------------------------------------------------------------
_current_plan_name: ContextVar[str] = ContextVar("_current_plan_name", default="free")


def set_current_plan(plan_name: str) -> None:
    """Set the current request's plan name (called by middleware)."""
    _current_plan_name.set(plan_name)


def get_current_plan() -> str:
    """Get the current request's plan name."""
    return _current_plan_name.get()


# ---------------------------------------------------------------------------
# Base rate limits (Free plan) - per endpoint key
# ---------------------------------------------------------------------------
BASE_LIMITS = {
    # Transcription endpoints (API cost control)
    "transcription_create": "10/minute",
    "transcription_upload": "5/minute",
    "transcription_list": "30/minute",
    "transcription_get": "30/minute",
    "transcription_delete": "10/minute",
    "transcription_smart": "10/minute",
    "transcription_playlist": "3/minute",
    "transcription_stream_capture": "2/minute",
    "transcription_metadata": "20/minute",
    "transcription_chapters": "5/minute",
    "transcription_download": "3/minute",
    "transcription_analyze": "3/minute",

    # Conversation / Chat endpoints
    "conversation_create": "10/minute",
    "conversation_message": "20/minute",
    "conversation_list": "30/minute",
    "conversation_get": "30/minute",
    "conversation_delete": "10/minute",

    # Compare endpoints
    "compare_run": "5/minute",
    "compare_vote": "10/minute",
    "compare_stats": "20/minute",

    # Pipeline endpoints
    "pipeline_create": "10/minute",
    "pipeline_list": "20/minute",
    "pipeline_get": "30/minute",
    "pipeline_update": "10/minute",
    "pipeline_delete": "10/minute",
    "pipeline_execute": "3/minute",
    "pipeline_executions": "20/minute",
    "pipeline_templates": "30/minute",

    # Knowledge base endpoints
    "knowledge_upload": "5/minute",
    "knowledge_list": "20/minute",
    "knowledge_search": "20/minute",
    "knowledge_ask": "10/minute",
    "knowledge_delete": "10/minute",

    # Agent endpoints
    "agent_run": "5/minute",
    "agent_get": "20/minute",
    "agent_list": "30/minute",
    "agent_steps": "10/minute",

    # Sentiment endpoints
    "sentiment_analyze": "10/minute",
    "sentiment_transcription": "5/minute",

    # Web crawler endpoints
    "crawler_scrape": "10/minute",
    "crawler_vision": "3/minute",
    "crawler_index": "3/minute",

    # Billing endpoints (not plan-scaled — same for all)
    "billing_plans": "30/minute",
    "billing_quota": "30/minute",
    "billing_checkout": "5/minute",
    "billing_portal": "5/minute",

    # API key endpoints
    "api_key_create": "5/minute",
    "api_key_list": "20/minute",
    "api_key_revoke": "10/minute",

    # Workspace endpoints
    "workspace_create": "10/minute",
    "workspace_update": "20/minute",
    "workspace_list": "30/minute",
    "workspace_members": "10/minute",
    "workspace_share": "5/minute",
    "workspace_comments": "20/minute",

    # Cost tracker endpoints
    "cost_summary": "20/minute",
    "cost_daily": "20/minute",
    "cost_export": "5/minute",

    # Default fallback
    "default": "30/minute",
}

# ---------------------------------------------------------------------------
# Plan multipliers
# ---------------------------------------------------------------------------
PLAN_MULTIPLIERS = {
    "free": 1,
    "pro": 3,
    "enterprise": 10,
}

# Endpoints that should NOT be scaled by plan (security / billing related)
_UNSCALED_ENDPOINTS = frozenset({
    "billing_plans",
    "billing_quota",
    "billing_checkout",
    "billing_portal",
})


def get_plan_rate_limit(endpoint_key: str, plan_name: str = "free") -> str:
    """
    Get the rate limit string for an endpoint based on the user's plan.

    Args:
        endpoint_key: key from BASE_LIMITS (e.g. "transcription_create")
        plan_name: billing plan name ("free", "pro", or "enterprise")

    Returns:
        Rate limit string, e.g. "30/minute"

    Example::

        >>> get_plan_rate_limit("transcription_create", "pro")
        '30/minute'
        >>> get_plan_rate_limit("agent_run", "enterprise")
        '50/minute'
    """
    base = BASE_LIMITS.get(endpoint_key, BASE_LIMITS["default"])

    # Some endpoints are not scaled
    if endpoint_key in _UNSCALED_ENDPOINTS:
        return base

    multiplier = PLAN_MULTIPLIERS.get(plan_name.lower(), 1)
    if multiplier == 1:
        return base

    # Parse "N/period" and multiply N
    try:
        parts = base.split("/")
        count = int(parts[0])
        period = parts[1]
        return f"{count * multiplier}/{period}"
    except (ValueError, IndexError):
        logger.warning(
            "rate_limit_parse_error",
            endpoint_key=endpoint_key,
            base_limit=base,
        )
        return base


def dynamic_limit(endpoint_key: str):
    """
    Create a dynamic rate limit callable for SlowAPI.

    Returns a callable (no parameters) that SlowAPI invokes to get the
    rate limit string for the current request. The plan is read from
    the context variable set by PlanResolverMiddleware.

    Usage::

        from app.rate_limit import limiter
        from app.rate_limit_dynamic import dynamic_limit

        @router.post("/run")
        @limiter.limit(dynamic_limit("agent_run"))
        async def run_agent(request: Request, ...):
            ...
    """

    def _limit_func() -> str:
        plan_name = get_current_plan()
        limit_str = get_plan_rate_limit(endpoint_key, plan_name)
        return limit_str

    # Give the function a descriptive name for debugging
    _limit_func.__name__ = f"dynamic_limit_{endpoint_key}"
    _limit_func.__qualname__ = f"dynamic_limit_{endpoint_key}"

    return _limit_func
