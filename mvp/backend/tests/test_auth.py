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
