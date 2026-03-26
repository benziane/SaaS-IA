"""
Feature Flags -- runtime control without redeployment.

Redis-backed feature flags with percentage rollout, user whitelist,
and boolean toggle support. Falls back gracefully to defaults when
Redis is unavailable.
"""

import hashlib
import time
from typing import Any

import structlog

logger = structlog.get_logger()

# In-memory cache: {flag_name: (value, timestamp)}
_flag_cache: dict[str, tuple[Any, float]] = {}
_CACHE_TTL = 10  # seconds


class FeatureFlagService:
    """Redis-backed feature flags with percentage rollout support."""

    # Default flags (used if Redis is down or flag not set)
    DEFAULTS: dict[str, bool] = {
        # Core modules (12)
        "transcription_enabled": True,
        "conversation_enabled": True,
        "knowledge_enabled": True,
        "compare_enabled": True,
        "pipelines_enabled": True,
        "agents_enabled": True,
        "sentiment_enabled": True,
        "web_crawler_enabled": True,
        "workspaces_enabled": True,
        "billing_enabled": True,
        "api_keys_enabled": True,
        "cost_tracker_enabled": True,
        # P0 - Content & Automation (2)
        "content_studio_enabled": True,
        "ai_workflows_enabled": True,
        # P1 - Intelligence & Safety (4)
        "multi_agent_crew_enabled": True,
        "voice_clone_enabled": True,
        "realtime_ai_enabled": True,
        "security_guardian_enabled": True,
        # P2 - Media & Intelligence (3)
        "image_gen_enabled": True,
        "data_analyst_enabled": True,
        "video_gen_enabled": True,
        # P3 - Custom Models (1)
        "fine_tuning_enabled": True,
        # Platform (3)
        "ai_monitoring_enabled": True,
        "unified_search_enabled": True,
        "ai_memory_enabled": True,
        # Extra modules
        "ai_chatbot_builder_enabled": True,
        "ai_forms_enabled": True,
        "audio_studio_enabled": True,
        "code_sandbox_enabled": True,
        "integration_hub_enabled": True,
        "marketplace_enabled": True,
        "pdf_processor_enabled": True,
        "presentation_gen_enabled": True,
        "repo_analyzer_enabled": True,
        "skill_seekers_enabled": True,
        "social_publisher_enabled": True,
        "tenants_enabled": True,
        "feature_flags_enabled": True,
        # Enterprise features
        "websocket_enabled": True,
        "multi_tenant_enabled": True,
        "audit_log_enabled": True,
    }

    REDIS_PREFIX = "feature_flag:"

    @staticmethod
    async def _get_redis():
        """Get Redis client, returns None if unavailable."""
        from app.cache import _get_redis
        return await _get_redis()

    @staticmethod
    def _hash_percentage(user_id: str, flag_name: str) -> float:
        """Deterministic percentage 0-100 for a user+flag combo."""
        combined = f"{user_id}:{flag_name}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        # Use first 4 bytes as unsigned int, mod 10000 for 2 decimal precision
        value = int.from_bytes(hash_bytes[:4], "big")
        return (value % 10000) / 100.0

    @staticmethod
    def _parse_value(raw: str | None) -> str | bool | None:
        """Parse a raw Redis string into a typed value."""
        if raw is None:
            return None
        lower = raw.strip().lower()
        if lower == "true":
            return True
        if lower == "false":
            return False
        # Return as-is for percentage ("30%") or user list ("users:uuid1,uuid2")
        return raw.strip()

    @staticmethod
    async def _get_raw(flag_name: str) -> str | None:
        """Get raw flag value from Redis with in-memory caching."""
        now = time.monotonic()

        # Check in-memory cache
        if flag_name in _flag_cache:
            cached_val, cached_at = _flag_cache[flag_name]
            if now - cached_at < _CACHE_TTL:
                return cached_val

        try:
            client = await FeatureFlagService._get_redis()
            if client is None:
                return None
            raw = await client.get(f"{FeatureFlagService.REDIS_PREFIX}{flag_name}")
            _flag_cache[flag_name] = (raw, now)
            return raw
        except Exception as e:
            logger.debug("feature_flag_redis_error", flag=flag_name, error=str(e))
            return None

    @staticmethod
    async def is_enabled(flag_name: str, user_id: str | None = None) -> bool:
        """Check if a feature flag is enabled.

        Supports:
        - Boolean flags: "transcription_enabled" = true/false
        - Percentage rollout: "new_feature" = "30%" (30% of users get it, based on user_id hash)
        - User whitelist: "beta_feature" = "users:uuid1,uuid2,uuid3"
        """
        raw = await FeatureFlagService._get_raw(flag_name)
        parsed = FeatureFlagService._parse_value(raw)

        # No override in Redis -> use default
        if parsed is None:
            return FeatureFlagService.DEFAULTS.get(flag_name, True)

        # Boolean
        if isinstance(parsed, bool):
            return parsed

        # Percentage rollout: "30%"
        if isinstance(parsed, str) and parsed.endswith("%"):
            try:
                pct = float(parsed[:-1])
            except ValueError:
                return FeatureFlagService.DEFAULTS.get(flag_name, True)
            if user_id is None:
                # No user context -> treat as enabled if >= 50%
                return pct >= 50.0
            user_pct = FeatureFlagService._hash_percentage(user_id, flag_name)
            return user_pct < pct

        # User whitelist: "users:uuid1,uuid2,uuid3"
        if isinstance(parsed, str) and parsed.startswith("users:"):
            if user_id is None:
                return False
            allowed = {u.strip() for u in parsed[6:].split(",") if u.strip()}
            return user_id in allowed

        # Unknown format -> default
        return FeatureFlagService.DEFAULTS.get(flag_name, True)

    @staticmethod
    async def set_flag(flag_name: str, value: str | bool) -> None:
        """Set a feature flag value in Redis. Takes effect immediately."""
        try:
            client = await FeatureFlagService._get_redis()
            if client is None:
                logger.warning("feature_flag_set_no_redis", flag=flag_name)
                return
            str_value = str(value).lower() if isinstance(value, bool) else str(value)
            await client.set(
                f"{FeatureFlagService.REDIS_PREFIX}{flag_name}",
                str_value,
            )
            # Invalidate cache
            _flag_cache.pop(flag_name, None)
            logger.info("feature_flag_set", flag=flag_name, value=str_value)
        except Exception as e:
            logger.error("feature_flag_set_error", flag=flag_name, error=str(e))

    @staticmethod
    async def delete_flag(flag_name: str) -> None:
        """Delete a flag (reverts to default)."""
        try:
            client = await FeatureFlagService._get_redis()
            if client is None:
                return
            await client.delete(f"{FeatureFlagService.REDIS_PREFIX}{flag_name}")
            _flag_cache.pop(flag_name, None)
            logger.info("feature_flag_deleted", flag=flag_name)
        except Exception as e:
            logger.error("feature_flag_delete_error", flag=flag_name, error=str(e))

    @staticmethod
    async def get_all_flags() -> dict[str, dict]:
        """Get all flags with current values, defaults, and overrides."""
        result: dict[str, dict] = {}

        # Start with all defaults
        for flag_name, default_val in FeatureFlagService.DEFAULTS.items():
            result[flag_name] = {
                "name": flag_name,
                "default": default_val,
                "override": None,
                "effective": default_val,
            }

        # Fetch overrides from Redis
        try:
            client = await FeatureFlagService._get_redis()
            if client is not None:
                prefix = FeatureFlagService.REDIS_PREFIX
                async for key in client.scan_iter(f"{prefix}*"):
                    flag_name = key[len(prefix):] if isinstance(key, str) else key.decode()[len(prefix):]
                    raw = await client.get(key)
                    parsed = FeatureFlagService._parse_value(raw)

                    if flag_name in result:
                        result[flag_name]["override"] = raw
                        if isinstance(parsed, bool):
                            result[flag_name]["effective"] = parsed
                        else:
                            result[flag_name]["effective"] = raw
                    else:
                        # Flag exists in Redis but not in defaults
                        result[flag_name] = {
                            "name": flag_name,
                            "default": None,
                            "override": raw,
                            "effective": raw,
                        }
        except Exception as e:
            logger.debug("feature_flag_scan_error", error=str(e))

        return result

    @staticmethod
    async def get_flags_for_user(user_id: str) -> dict[str, bool]:
        """Get all resolved flag values for a specific user."""
        result: dict[str, bool] = {}
        for flag_name in FeatureFlagService.DEFAULTS:
            result[flag_name] = await FeatureFlagService.is_enabled(flag_name, user_id)
        return result

    @staticmethod
    def clear_cache() -> None:
        """Clear the in-memory flag cache (useful after bulk updates)."""
        _flag_cache.clear()
