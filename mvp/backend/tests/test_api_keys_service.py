"""
Tests for the API keys module: key generation, verification, rate limiting, and routes.

All tests run without external services (no DB, no Redis).
"""

import hashlib
import json
import os
import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_api_key(user_id, name="Test Key", is_active=True, rate_limit=1000, expires_at=None, key_hash=None):
    """Create a mock APIKey object."""
    from app.models.api_key import APIKey

    raw = f"sk-{'a' * 32}"
    computed_hash = key_hash or hashlib.sha256(raw.encode()).hexdigest()
    return APIKey(
        id=uuid4(),
        user_id=user_id,
        name=name,
        key_hash=computed_hash,
        key_prefix=raw[:8],
        permissions_json='["read", "write"]',
        rate_limit_per_day=rate_limit,
        is_active=is_active,
        last_used_at=None,
        created_at=datetime.now(UTC),
        expires_at=expires_at,
    )


# ---------------------------------------------------------------------------
# Service unit tests
# ---------------------------------------------------------------------------

class TestAPIKeyGeneration:
    """Tests for key generation and hashing."""

    def test_generate_key_format(self):
        """Generated keys start with 'sk-' and have sufficient entropy."""
        from app.modules.api_keys.service import APIKeyService

        key = APIKeyService.generate_key()
        assert key.startswith("sk-")
        assert len(key) > 30  # sk- + 32 bytes url-safe base64

    def test_generate_key_unique(self):
        """Two generated keys should never collide."""
        from app.modules.api_keys.service import APIKeyService

        k1 = APIKeyService.generate_key()
        k2 = APIKeyService.generate_key()
        assert k1 != k2

    def test_key_hash_sha256(self):
        """hash_key should produce a valid SHA-256 hex digest."""
        from app.modules.api_keys.service import APIKeyService

        key = "sk-test-key-for-hashing"
        hashed = APIKeyService.hash_key(key)
        expected = hashlib.sha256(key.encode()).hexdigest()
        assert hashed == expected
        assert len(hashed) == 64  # SHA-256 hex = 64 chars

    def test_hash_deterministic(self):
        """Same key always produces the same hash."""
        from app.modules.api_keys.service import APIKeyService

        key = "sk-deterministic-test"
        assert APIKeyService.hash_key(key) == APIKeyService.hash_key(key)


class TestAPIKeyCreateKey:
    """Tests for APIKeyService.create_key."""

    @pytest.mark.asyncio
    async def test_create_api_key_returns_key_and_model(self):
        """create_key should return (APIKey model, plain-text key)."""
        from app.modules.api_keys.service import APIKeyService

        user_id = uuid4()
        session = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        api_key, raw_key = await APIKeyService.create_key(
            user_id=user_id,
            name="My API Key",
            permissions=["read", "write"],
            rate_limit_per_day=500,
            session=session,
        )

        assert raw_key.startswith("sk-")
        assert api_key.user_id == user_id
        assert api_key.name == "My API Key"
        assert api_key.key_prefix == raw_key[:8]
        assert api_key.rate_limit_per_day == 500
        assert api_key.is_active is True
        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_api_key_stores_hash_not_plain(self):
        """The stored key_hash should NOT be the raw key (it should be a hash)."""
        from app.modules.api_keys.service import APIKeyService

        user_id = uuid4()
        session = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        api_key, raw_key = await APIKeyService.create_key(
            user_id=user_id,
            name="Hash Test",
            permissions=["read"],
            rate_limit_per_day=1000,
            session=session,
        )

        assert api_key.key_hash != raw_key
        assert api_key.key_hash == hashlib.sha256(raw_key.encode()).hexdigest()


class TestAPIKeyListKeys:
    """Tests for APIKeyService.list_keys."""

    @pytest.mark.asyncio
    async def test_list_api_keys_returns_user_keys(self):
        """list_keys should return only the specified user's keys."""
        from app.modules.api_keys.service import APIKeyService

        user_id = uuid4()
        keys = [_make_api_key(user_id, "Key 1"), _make_api_key(user_id, "Key 2")]

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = keys
        session.execute = AsyncMock(return_value=mock_result)

        result = await APIKeyService.list_keys(user_id, session)
        assert len(result) == 2
        assert all(k.user_id == user_id for k in result)


class TestAPIKeyVerification:
    """Tests for APIKeyService.verify_key."""

    @pytest.mark.asyncio
    async def test_verify_valid_key_returns_user_id_and_permissions(self):
        """Valid active key with no rate limit hit returns (user_id, permissions)."""
        from app.modules.api_keys.service import APIKeyService

        user_id = uuid4()
        raw_key = "sk-valid-test-key-for-verification"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = _make_api_key(user_id, key_hash=key_hash)

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = api_key
        session.execute = AsyncMock(return_value=mock_result)
        session.commit = AsyncMock()

        with (
            patch("app.modules.api_keys.service._get_daily_usage", new_callable=AsyncMock, return_value=0),
            patch("app.modules.api_keys.service._increment_daily_usage", new_callable=AsyncMock, return_value=1),
        ):
            result = await APIKeyService.verify_key(raw_key, session)

        assert result is not None
        returned_user_id, permissions = result
        assert returned_user_id == user_id
        assert "read" in permissions
        assert "write" in permissions

    @pytest.mark.asyncio
    async def test_verify_invalid_key_returns_none(self):
        """Invalid key (not found in DB) returns None."""
        from app.modules.api_keys.service import APIKeyService

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        result = await APIKeyService.verify_key("sk-nonexistent", session)
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_inactive_key_returns_none(self):
        """Inactive key should not verify (the DB query filters is_active=True)."""
        from app.modules.api_keys.service import APIKeyService

        session = AsyncMock()
        # The SELECT query filters is_active == True, so inactive keys won't be found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        result = await APIKeyService.verify_key("sk-inactive-key", session)
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_expired_key_returns_none(self):
        """Expired key should return None even if active."""
        from app.modules.api_keys.service import APIKeyService

        user_id = uuid4()
        raw_key = "sk-expired-key-test"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = _make_api_key(
            user_id,
            key_hash=key_hash,
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = api_key
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("app.modules.api_keys.service._get_daily_usage", new_callable=AsyncMock, return_value=0),
        ):
            result = await APIKeyService.verify_key(raw_key, session)

        assert result is None


class TestAPIKeyDailyRateLimit:
    """Tests for Redis-backed daily rate limiting."""

    @pytest.mark.asyncio
    async def test_daily_rate_limit_within_limit_passes(self):
        """Verify passes when daily usage is under the limit."""
        from app.modules.api_keys.service import APIKeyService

        user_id = uuid4()
        raw_key = "sk-rate-limit-ok-key"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = _make_api_key(user_id, key_hash=key_hash, rate_limit=100)

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = api_key
        session.execute = AsyncMock(return_value=mock_result)
        session.commit = AsyncMock()

        with (
            patch("app.modules.api_keys.service._get_daily_usage", new_callable=AsyncMock, return_value=50),
            patch("app.modules.api_keys.service._increment_daily_usage", new_callable=AsyncMock, return_value=51),
        ):
            result = await APIKeyService.verify_key(raw_key, session)

        assert result is not None

    @pytest.mark.asyncio
    async def test_daily_rate_limit_exceeded_raises_429(self):
        """Verify raises HTTPException 429 when daily limit is exceeded."""
        from fastapi import HTTPException
        from app.modules.api_keys.service import APIKeyService

        user_id = uuid4()
        raw_key = "sk-rate-limit-exceeded"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = _make_api_key(user_id, key_hash=key_hash, rate_limit=100)

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = api_key
        session.execute = AsyncMock(return_value=mock_result)

        with (
            patch("app.modules.api_keys.service._get_daily_usage", new_callable=AsyncMock, return_value=100),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await APIKeyService.verify_key(raw_key, session)
            assert exc_info.value.status_code == 429
            assert "rate limit" in exc_info.value.detail.lower()


class TestAPIKeyRevocation:
    """Tests for APIKeyService.revoke_key."""

    @pytest.mark.asyncio
    async def test_revoke_api_key_marks_inactive(self):
        """revoke_key should set is_active=False and return True."""
        from app.modules.api_keys.service import APIKeyService

        user_id = uuid4()
        api_key = _make_api_key(user_id)
        key_id = api_key.id

        session = AsyncMock()
        session.get = AsyncMock(return_value=api_key)
        session.commit = AsyncMock()

        result = await APIKeyService.revoke_key(key_id, user_id, session)
        assert result is True
        assert api_key.is_active is False

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_key_returns_false(self):
        """Revoking a key that doesn't exist returns False."""
        from app.modules.api_keys.service import APIKeyService

        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        result = await APIKeyService.revoke_key(uuid4(), uuid4(), session)
        assert result is False

    @pytest.mark.asyncio
    async def test_revoke_other_users_key_returns_false(self):
        """Cannot revoke another user's key."""
        from app.modules.api_keys.service import APIKeyService

        owner_id = uuid4()
        attacker_id = uuid4()
        api_key = _make_api_key(owner_id)

        session = AsyncMock()
        session.get = AsyncMock(return_value=api_key)

        result = await APIKeyService.revoke_key(api_key.id, attacker_id, session)
        assert result is False
        assert api_key.is_active is True  # unchanged


class TestAPIKeyEndpointAuth:
    """Tests for API key route authentication."""

    @pytest.mark.asyncio
    async def test_list_keys_endpoint_returns_401_without_token(self, client):
        """GET /api/keys/ should return 401 without auth."""
        response = await client.get("/api/keys/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_key_endpoint_returns_401_without_token(self, client):
        """POST /api/keys/ should return 401 without auth."""
        response = await client.post(
            "/api/keys/",
            json={"name": "Test", "permissions": ["read"]},
        )
        assert response.status_code == 401
