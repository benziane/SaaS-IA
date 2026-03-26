"""
Redis-specific integration tests.

Tests cache operations, rate limiting, token blacklist, feature flags,
and session expiry using either real Redis or the MockRedis stub.
"""

import asyncio
import json

import pytest

from tests.integration.conftest import USE_REAL_REDIS


# ---------------------------------------------------------------------------
# Cache operations
# ---------------------------------------------------------------------------

class TestRedisIntegration:
    """Core Redis cache operations."""

    @pytest.mark.asyncio
    async def test_cache_set_get(self, redis_client):
        """Set a key and retrieve it."""
        await redis_client.set("saas_ia:test_key", json.dumps({"value": 42}), ex=60)
        raw = await redis_client.get("saas_ia:test_key")
        assert raw is not None
        data = json.loads(raw)
        assert data["value"] == 42

    @pytest.mark.asyncio
    async def test_cache_get_missing_key(self, redis_client):
        """Getting a non-existent key should return None."""
        result = await redis_client.get("saas_ia:definitely_does_not_exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_delete(self, redis_client):
        """Deleting a key should remove it."""
        await redis_client.set("saas_ia:del_test", "hello", ex=60)
        deleted = await redis_client.delete("saas_ia:del_test")
        assert deleted >= 1
        result = await redis_client.get("saas_ia:del_test")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_overwrite(self, redis_client):
        """Setting the same key twice should overwrite."""
        await redis_client.set("saas_ia:overwrite", "first", ex=60)
        await redis_client.set("saas_ia:overwrite", "second", ex=60)
        result = await redis_client.get("saas_ia:overwrite")
        assert result == "second"

    @pytest.mark.asyncio
    async def test_incr(self, redis_client):
        """INCR should atomically increment a counter."""
        key = "saas_ia:counter_test"
        await redis_client.delete(key)
        val1 = await redis_client.incr(key)
        assert val1 == 1
        val2 = await redis_client.incr(key)
        assert val2 == 2
        val3 = await redis_client.incr(key)
        assert val3 == 3


# ---------------------------------------------------------------------------
# Rate limiting simulation
# ---------------------------------------------------------------------------

class TestRateLimitSlidingWindow:
    """Simulate sliding-window rate limiting using Redis counters."""

    @pytest.mark.asyncio
    async def test_rate_limit_under_threshold(self, redis_client):
        """Requests under the limit should pass."""
        key = "saas_ia:ratelimit:test_user:endpoint"
        limit = 10

        await redis_client.delete(key)
        for i in range(limit):
            count = await redis_client.incr(key)
            await redis_client.expire(key, 60)
            assert count <= limit, f"Should be under limit at iteration {i}"

    @pytest.mark.asyncio
    async def test_rate_limit_over_threshold(self, redis_client):
        """Requests over the limit should be detected."""
        key = "saas_ia:ratelimit:over_test"
        limit = 5

        await redis_client.delete(key)
        for _ in range(limit):
            await redis_client.incr(key)
        await redis_client.expire(key, 60)

        count = await redis_client.incr(key)
        assert count > limit, "Should exceed limit"


# ---------------------------------------------------------------------------
# Token blacklist
# ---------------------------------------------------------------------------

class TestTokenBlacklist:
    """Test token blacklist operations via Redis."""

    @pytest.mark.asyncio
    async def test_blacklist_token(self, redis_client):
        """A blacklisted token JTI should be detectable."""
        jti = "test-jti-12345"
        key = f"token_blacklist:{jti}"

        await redis_client.set(key, "1", ex=1800)
        result = await redis_client.get(key)
        assert result == "1"

    @pytest.mark.asyncio
    async def test_blacklist_not_present(self, redis_client):
        """A non-blacklisted JTI should return None."""
        key = "token_blacklist:not-blacklisted-jti"
        result = await redis_client.get(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_blacklist_user_tokens(self, redis_client):
        """User-level token revocation via timestamp."""
        user_key = "token_blacklist:user:testuser@example.com"
        revoked_at = "2025-01-01T00:00:00+00:00"

        await redis_client.set(user_key, revoked_at, ex=604800)
        result = await redis_client.get(user_key)
        assert result == revoked_at


# ---------------------------------------------------------------------------
# Feature flags
# ---------------------------------------------------------------------------

class TestFeatureFlags:
    """Test feature flag storage/retrieval via Redis."""

    @pytest.mark.asyncio
    async def test_feature_flag_enabled(self, redis_client):
        """An enabled feature flag should return 'true'."""
        key = "saas_ia:feature:new_dashboard"
        await redis_client.set(key, "true", ex=3600)
        result = await redis_client.get(key)
        assert result == "true"

    @pytest.mark.asyncio
    async def test_feature_flag_disabled(self, redis_client):
        """A disabled feature flag should return 'false'."""
        key = "saas_ia:feature:beta_feature"
        await redis_client.set(key, "false", ex=3600)
        result = await redis_client.get(key)
        assert result == "false"

    @pytest.mark.asyncio
    async def test_feature_flag_missing_defaults_to_none(self, redis_client):
        """A non-existent feature flag should return None."""
        result = await redis_client.get("saas_ia:feature:nonexistent")
        assert result is None


# ---------------------------------------------------------------------------
# Session / TTL expiry
# ---------------------------------------------------------------------------

class TestSessionExpiry:
    """Test TTL-based session expiry."""

    @pytest.mark.asyncio
    async def test_key_with_ttl(self, redis_client):
        """A key with a TTL should report positive TTL."""
        key = "saas_ia:session:user123"
        await redis_client.set(key, json.dumps({"user_id": "123"}), ex=300)
        ttl = await redis_client.ttl(key)
        assert ttl > 0
        assert ttl <= 300

    @pytest.mark.asyncio
    @pytest.mark.skipif(not USE_REAL_REDIS, reason="Mock TTL expiry is not time-based")
    async def test_key_expires(self, redis_client):
        """A key with a 1-second TTL should expire after waiting."""
        key = "saas_ia:session:expire_test"
        await redis_client.set(key, "temporary", ex=1)

        # Wait for expiry
        await asyncio.sleep(1.5)

        result = await redis_client.get(key)
        assert result is None

    @pytest.mark.asyncio
    async def test_pipeline_operations(self, redis_client):
        """Pipeline should execute multiple commands atomically."""
        pipe = redis_client.pipeline()
        pipe.set("saas_ia:pipe1", "value1", ex=60)
        pipe.set("saas_ia:pipe2", "value2", ex=60)
        await pipe.execute()

        v1 = await redis_client.get("saas_ia:pipe1")
        v2 = await redis_client.get("saas_ia:pipe2")
        assert v1 == "value1"
        assert v2 == "value2"
