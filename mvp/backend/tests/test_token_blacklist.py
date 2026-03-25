"""
Tests for the Redis-backed token blacklist system (CRIT-03).

Covers:
  - blacklist_token: a specific JTI is marked as blacklisted
  - is_blacklisted: returns False for tokens that have not been blacklisted
  - blacklist_user_tokens: all tokens for a user are revoked after a timestamp
  - Graceful fallback when Redis is unavailable (fail-open)
"""

import pytest
from datetime import UTC, datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _fake_redis_store():
    """Return a mock Redis client backed by a plain dict for testing."""
    store: dict[str, str] = {}

    client = AsyncMock()

    async def _set(key, value, ex=None):
        store[key] = value

    async def _get(key):
        return store.get(key)

    client.set = AsyncMock(side_effect=_set)
    client.get = AsyncMock(side_effect=_get)

    return client, store


# --------------------------------------------------------------------------
# test_blacklist_token
# --------------------------------------------------------------------------

async def test_blacklist_token():
    """After blacklisting a JTI, is_blacklisted returns True for that JTI."""
    from app.core.token_blacklist import blacklist_token, is_blacklisted

    mock_client, store = _fake_redis_store()

    with patch("app.core.token_blacklist._get_redis", new_callable=AsyncMock, return_value=mock_client):
        jti = "test-jti-abc-123"
        await blacklist_token(jti, expires_in=300)
        result = await is_blacklisted(jti)

    assert result is True
    assert f"token_blacklist:{jti}" in store


# --------------------------------------------------------------------------
# test_is_not_blacklisted
# --------------------------------------------------------------------------

async def test_is_not_blacklisted():
    """A JTI that was never blacklisted returns False."""
    from app.core.token_blacklist import is_blacklisted

    mock_client, _ = _fake_redis_store()

    with patch("app.core.token_blacklist._get_redis", new_callable=AsyncMock, return_value=mock_client):
        result = await is_blacklisted("never-seen-jti")

    assert result is False


# --------------------------------------------------------------------------
# test_blacklist_user_tokens
# --------------------------------------------------------------------------

async def test_blacklist_user_tokens():
    """After blacklisting user tokens, tokens issued before the revocation
    timestamp are rejected by is_user_tokens_revoked."""
    from app.core.token_blacklist import blacklist_user_tokens, is_user_tokens_revoked

    mock_client, store = _fake_redis_store()

    user_id = "user@example.com"
    # Token was issued 60 seconds ago
    old_iat = int(datetime.now(UTC).timestamp()) - 60

    with patch("app.core.token_blacklist._get_redis", new_callable=AsyncMock, return_value=mock_client):
        # Revoke all tokens for the user
        await blacklist_user_tokens(user_id)

        # A token issued *before* the revocation should be rejected
        assert await is_user_tokens_revoked(user_id, old_iat) is True

        # A token issued *after* the revocation should be accepted
        future_iat = int(datetime.now(UTC).timestamp()) + 60
        assert await is_user_tokens_revoked(user_id, future_iat) is False


# --------------------------------------------------------------------------
# test_blacklist_redis_down
# --------------------------------------------------------------------------

async def test_blacklist_redis_down():
    """When Redis is unavailable, is_blacklisted returns False (fail-open)."""
    from app.core.token_blacklist import is_blacklisted, is_user_tokens_revoked

    with patch("app.core.token_blacklist._get_redis", new_callable=AsyncMock, return_value=None):
        # Both should fail-open (return False) so requests are not blocked
        assert await is_blacklisted("any-jti") is False
        assert await is_user_tokens_revoked("user@example.com", 1234567890) is False
