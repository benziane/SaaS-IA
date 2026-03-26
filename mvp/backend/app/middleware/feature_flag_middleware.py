"""
Feature Flag Middleware
=======================

Checks module-level feature flags before routing requests.
If a module is disabled via its feature flag, returns 503.
Flag values are cached in-memory for 10 seconds to avoid
Redis calls on every request.
"""

import re
import time
from typing import Any

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = structlog.get_logger()

# Paths that should never be blocked by feature flags
_SKIP_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics",
    "/api/auth",
    "/api/feature-flags",
    "/",
)

_SKIP_EXACT = frozenset({
    "/",
    "/health",
    "/health/live",
    "/health/ready",
    "/health/startup",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics",
})

# Pattern to extract module name from /api/<module_name>/...
_MODULE_PATTERN = re.compile(r"^/api/([a-z][a-z0-9_-]+)")

# Module name normalization: URL uses hyphens, flags use underscores
_URL_TO_FLAG: dict[str, str] = {
    "ai-assistant": "ai_assistant",
    "ai-workflows": "ai_workflows",
    "ai-chatbot-builder": "ai_chatbot_builder",
    "ai-forms": "ai_forms",
    "ai-memory": "ai_memory",
    "ai-monitoring": "ai_monitoring",
    "audio-studio": "audio_studio",
    "code-sandbox": "code_sandbox",
    "content-studio": "content_studio",
    "cost-tracker": "cost_tracker",
    "data-analyst": "data_analyst",
    "fine-tuning": "fine_tuning",
    "image-gen": "image_gen",
    "integration-hub": "integration_hub",
    "multi-agent-crew": "multi_agent_crew",
    "pdf-processor": "pdf_processor",
    "presentation-gen": "presentation_gen",
    "realtime-ai": "realtime_ai",
    "repo-analyzer": "repo_analyzer",
    "security-guardian": "security_guardian",
    "skill-seekers": "skill_seekers",
    "social-publisher": "social_publisher",
    "unified-search": "unified_search",
    "video-gen": "video_gen",
    "voice-clone": "voice_clone",
    "web-crawler": "web_crawler",
    "feature-flags": "feature_flags",
}

# In-memory flag cache: {flag_name: (is_enabled, timestamp)}
_module_flag_cache: dict[str, tuple[bool, float]] = {}
_CACHE_TTL = 10  # seconds


class FeatureFlagMiddleware(BaseHTTPMiddleware):
    """Block requests to disabled modules with 503 Service Unavailable."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # Skip infrastructure paths
        if path in _SKIP_EXACT:
            return await call_next(request)

        # Skip auth, docs, feature-flags admin paths
        for prefix in ("/api/auth", "/api/feature-flags", "/docs", "/redoc",
                        "/openapi.json", "/metrics", "/health", "/v1"):
            if path.startswith(prefix):
                return await call_next(request)

        # Extract module name from path
        match = _MODULE_PATTERN.match(path)
        if not match:
            return await call_next(request)

        url_module = match.group(1)

        # Normalize: URL hyphens -> flag underscores
        module_name = _URL_TO_FLAG.get(url_module, url_module.replace("-", "_"))
        flag_name = f"{module_name}_enabled"

        # Check cache first
        now = time.monotonic()
        if flag_name in _module_flag_cache:
            cached_enabled, cached_at = _module_flag_cache[flag_name]
            if now - cached_at < _CACHE_TTL:
                if not cached_enabled:
                    return self._disabled_response(module_name)
                return await call_next(request)

        # Check flag via FeatureFlagService
        try:
            from app.core.feature_flags import FeatureFlagService
            enabled = await FeatureFlagService.is_enabled(flag_name)
            _module_flag_cache[flag_name] = (enabled, now)
        except Exception as e:
            logger.debug("feature_flag_middleware_error", flag=flag_name, error=str(e))
            # Fail-open: if we can't check, allow the request
            enabled = True

        if not enabled:
            return self._disabled_response(module_name)

        return await call_next(request)

    @staticmethod
    def _disabled_response(module_name: str) -> JSONResponse:
        """Return 503 when a feature/module is disabled."""
        return JSONResponse(
            status_code=503,
            content={
                "detail": "This feature is currently disabled",
                "feature": module_name,
            },
            headers={"Retry-After": "60"},
        )

    @staticmethod
    def clear_cache() -> None:
        """Clear the middleware flag cache."""
        _module_flag_cache.clear()
