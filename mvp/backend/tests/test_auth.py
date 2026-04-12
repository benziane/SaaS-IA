"""
Unit tests for JWT authentication utilities.

Covers:
- Access token creation and claim verification
- Refresh token creation and claim verification
- Password hashing and verification roundtrip
- Expired token handling

All tests run WITHOUT a database, Redis, or any external service.
"""

import time
from datetime import timedelta
from unittest.mock import patch

import pytest
from jose import jwt, JWTError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# We need the test environment variables to be set before importing app code.
# conftest.py handles that via os.environ.setdefault calls at module level.

from app.config import settings
from app.auth import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
)


# ---------------------------------------------------------------------------
# Tests: create_access_token
# ---------------------------------------------------------------------------

class TestCreateAccessToken:
    """Tests for ``create_access_token``."""

    def test_returns_string(self):
        token = create_access_token(data={"sub": "user@example.com"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_contains_sub_claim(self):
        email = "alice@example.com"
        token = create_access_token(data={"sub": email})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == email

    def test_contains_type_access(self):
        token = create_access_token(data={"sub": "user@example.com"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] == "access"

    def test_contains_exp_claim(self):
        token = create_access_token(data={"sub": "user@example.com"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload

    def test_custom_expiry(self):
        delta = timedelta(minutes=5)
        token = create_access_token(data={"sub": "user@example.com"}, expires_delta=delta)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload

    def test_extra_claims_preserved(self):
        token = create_access_token(data={"sub": "user@example.com", "role": "admin"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["role"] == "admin"

    def test_decode_with_wrong_key_fails(self):
        token = create_access_token(data={"sub": "user@example.com"})
        with pytest.raises(JWTError):
            jwt.decode(token, "wrong-secret-key", algorithms=[settings.ALGORITHM])

    def test_expired_token_raises(self):
        """A token with a negative expiry should fail verification."""
        delta = timedelta(seconds=-1)
        token = create_access_token(data={"sub": "user@example.com"}, expires_delta=delta)
        with pytest.raises(JWTError):
            jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ---------------------------------------------------------------------------
# Tests: create_refresh_token
# ---------------------------------------------------------------------------

class TestCreateRefreshToken:
    """Tests for ``create_refresh_token``."""

    def test_returns_string(self):
        token = create_refresh_token(user_id="user@example.com")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_contains_type_refresh(self):
        token = create_refresh_token(user_id="user@example.com")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] == "refresh"

    def test_contains_sub_claim(self):
        email = "bob@example.com"
        token = create_refresh_token(user_id=email)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == email

    def test_contains_exp_claim(self):
        token = create_refresh_token(user_id="user@example.com")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload

    def test_refresh_token_not_usable_as_access(self):
        """Refresh tokens must carry ``type=refresh`` so that the
        ``get_current_user`` dependency rejects them."""
        token = create_refresh_token(user_id="user@example.com")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] != "access"


# ---------------------------------------------------------------------------
# Tests: password hashing
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    """Tests for ``verify_password`` and ``get_password_hash``."""

    def test_hash_returns_string(self):
        hashed = get_password_hash("mypassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_differs_from_plaintext(self):
        password = "mypassword"
        hashed = get_password_hash(password)
        assert hashed != password

    def test_verify_correct_password(self):
        password = "S3cur3P@ssw0rd!"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        hashed = get_password_hash("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_same_password_produces_different_hashes(self):
        """bcrypt uses a random salt, so two hashes of the same password
        must differ."""
        password = "same-password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2

    def test_both_hashes_verify(self):
        """Even though hashes differ, both must verify against the
        original password."""
        password = "same-password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_empty_password_hashes(self):
        """Edge case: empty string is still a valid password for bcrypt."""
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False

    def test_unicode_password(self):
        password = "m\u00f6tDeP\u00e0sse\u2603"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


# ---------------------------------------------------------------------------
# Tests: token / password interaction scenarios
# ---------------------------------------------------------------------------

class TestTokenIntegrationScenarios:
    """Higher-level scenarios combining tokens and passwords."""

    def test_access_and_refresh_tokens_differ(self):
        email = "user@example.com"
        access = create_access_token(data={"sub": email})
        refresh = create_refresh_token(user_id=email)
        assert access != refresh

    def test_access_token_type_is_not_refresh(self):
        access = create_access_token(data={"sub": "u@e.com"})
        payload = jwt.decode(access, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] == "access"

    def test_refresh_token_type_is_not_access(self):
        refresh = create_refresh_token(user_id="u@e.com")
        payload = jwt.decode(refresh, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["type"] == "refresh"


from unittest.mock import AsyncMock, MagicMock

# ---------------------------------------------------------------------------
# Tests: login lockout (_check_login_lockout, _record_failed_login)
# ---------------------------------------------------------------------------

class TestLoginLockout:
    """Tests for account lockout logic after repeated failed login attempts."""

    @pytest.mark.asyncio
    async def test_lockout_returns_none_when_attempts_below_threshold(self):
        """No lockout when failed attempt count is below LOGIN_MAX_ATTEMPTS."""
        from app.auth import _check_login_lockout

        mock_redis = MagicMock()
        # Redis returns "3" attempts (< 5)
        mock_redis.get = AsyncMock(return_value="3")

        with patch("app.auth._get_login_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await _check_login_lockout("user@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_lockout_returns_ttl_when_attempts_at_threshold(self):
        """Returns remaining TTL when failed attempts reach LOGIN_MAX_ATTEMPTS (5)."""
        from app.auth import _check_login_lockout

        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="5")
        mock_redis.ttl = AsyncMock(return_value=720)

        with patch("app.auth._get_login_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await _check_login_lockout("locked@example.com")

        assert result == 720

    @pytest.mark.asyncio
    async def test_lockout_returns_minimum_1_when_ttl_zero(self):
        """TTL of 0 is clamped to 1 to avoid returning a falsy lockout value."""
        from app.auth import _check_login_lockout

        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="10")
        mock_redis.ttl = AsyncMock(return_value=0)

        with patch("app.auth._get_login_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await _check_login_lockout("user@example.com")

        assert result >= 1

    @pytest.mark.asyncio
    async def test_lockout_fails_closed_when_redis_unavailable(self):
        """When Redis is None (down), lockout returns LOGIN_REDIS_FAIL_LOCKOUT (fail-closed)."""
        from app.auth import _check_login_lockout, LOGIN_REDIS_FAIL_LOCKOUT

        with patch("app.auth._get_login_redis", new_callable=AsyncMock, return_value=None):
            result = await _check_login_lockout("user@example.com")

        assert result == LOGIN_REDIS_FAIL_LOCKOUT

    @pytest.mark.asyncio
    async def test_lockout_fails_closed_on_redis_exception(self):
        """If Redis.get raises, lockout returns LOGIN_REDIS_FAIL_LOCKOUT (fail-closed)."""
        from app.auth import _check_login_lockout, LOGIN_REDIS_FAIL_LOCKOUT

        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection error"))

        with patch("app.auth._get_login_redis", new_callable=AsyncMock, return_value=mock_redis):
            result = await _check_login_lockout("user@example.com")

        assert result == LOGIN_REDIS_FAIL_LOCKOUT

    @pytest.mark.asyncio
    async def test_record_failed_login_increments_counter(self):
        """_record_failed_login should INCR the key and set TTL via pipeline."""
        from app.auth import _record_failed_login

        mock_pipeline = MagicMock()
        mock_pipeline.incr = MagicMock()
        mock_pipeline.expire = MagicMock()
        mock_pipeline.execute = AsyncMock()

        mock_redis = MagicMock()
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)

        with patch("app.auth._get_login_redis", new_callable=AsyncMock, return_value=mock_redis):
            await _record_failed_login("user@example.com")

        mock_pipeline.incr.assert_called_once()
        mock_pipeline.expire.assert_called_once()
        mock_pipeline.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_record_failed_login_noop_when_redis_none(self):
        """_record_failed_login is a no-op when Redis is unavailable."""
        from app.auth import _record_failed_login

        with patch("app.auth._get_login_redis", new_callable=AsyncMock, return_value=None):
            # Should not raise
            await _record_failed_login("user@example.com")

    @pytest.mark.asyncio
    async def test_reset_login_attempts_clears_key(self):
        """_reset_login_attempts deletes the Redis key on successful login."""
        from app.auth import _reset_login_attempts

        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock()

        with patch("app.auth._get_login_redis", new_callable=AsyncMock, return_value=mock_redis):
            await _reset_login_attempts("user@example.com")

        mock_redis.delete.assert_awaited_once_with("login_attempts:user@example.com")


# ---------------------------------------------------------------------------
# Tests: get_current_user — token blacklist enforcement
# ---------------------------------------------------------------------------

class TestGetCurrentUserBlacklist:
    """get_current_user must reject blacklisted tokens and user-revoked tokens."""

    @pytest.mark.asyncio
    async def test_blacklisted_jti_raises_401(self):
        """A token whose JTI is in the blacklist should be rejected with 401."""
        from fastapi import HTTPException
        from app.auth import get_current_user
        from unittest.mock import AsyncMock, patch

        # Build a valid token
        token = create_access_token(data={"sub": "user@example.com"})

        mock_session = AsyncMock()
        mock_user = MagicMock()
        mock_user.is_active = True

        with (
            patch("app.auth.is_blacklisted", new_callable=AsyncMock, return_value=True),
            patch("app.auth.is_user_tokens_revoked", new_callable=AsyncMock, return_value=False),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=token, session=mock_session)

        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_user_revoked_tokens_raises_401(self):
        """A token issued before the user's revoked-at timestamp should be rejected."""
        from fastapi import HTTPException
        from app.auth import get_current_user

        token = create_access_token(data={"sub": "user@example.com"})
        mock_session = AsyncMock()

        with (
            patch("app.auth.is_blacklisted", new_callable=AsyncMock, return_value=False),
            patch("app.auth.is_user_tokens_revoked", new_callable=AsyncMock, return_value=True),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=token, session=mock_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_used_as_access_raises_401(self):
        """A refresh token must NOT be accepted as an access token."""
        from fastapi import HTTPException
        from app.auth import get_current_user, create_refresh_token

        # create_refresh_token sets type='refresh'
        token = create_refresh_token(user_id="user@example.com")
        mock_session = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, session=mock_session)

        assert exc_info.value.status_code == 401
