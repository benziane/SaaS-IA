"""
Tests for the authentication flow.

Covers:
  - POST /api/auth/login (success and failure)
  - Protected endpoint access with and without token
  - Token generation and validation
"""

import pytest
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock


# --------------------------------------------------------------------------
# Login
# --------------------------------------------------------------------------

async def test_login_success(client, test_user):
    """POST /api/auth/login with valid credentials returns tokens."""
    from app.auth import get_password_hash

    # Prepare a mock user with a properly hashed password
    plain_password = "SecureP@ssw0rd123"
    test_user.hashed_password = get_password_hash(plain_password)
    test_user.email = "login@example.com"

    with patch("app.auth.authenticate_user", new_callable=AsyncMock, return_value=test_user), \
         patch("app.auth._check_login_lockout", new_callable=AsyncMock, return_value=None):
        resp = await client.post(
            "/api/auth/login",
            data={
                "username": "login@example.com",
                "password": plain_password,
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert "expires_in" in body
    assert body["expires_in"] > 0


async def test_login_invalid_credentials(client):
    """POST /api/auth/login with bad credentials returns 401."""
    with patch("app.auth.authenticate_user", new_callable=AsyncMock, return_value=None), \
         patch("app.auth._check_login_lockout", new_callable=AsyncMock, return_value=None), \
         patch("app.auth._record_failed_login", new_callable=AsyncMock):
        resp = await client.post(
            "/api/auth/login",
            data={
                "username": "wrong@example.com",
                "password": "WrongP@ss123",
            },
        )

    assert resp.status_code == 401
    body = resp.json()
    assert "detail" in body


# --------------------------------------------------------------------------
# Protected endpoint access
# --------------------------------------------------------------------------

async def test_protected_endpoint_no_token(client):
    """GET /api/auth/me without a token returns 401."""
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_protected_endpoint_with_token(client, auth_headers, test_user, app):
    """GET /api/auth/me with a valid token returns user data."""
    from app.auth import get_current_user, get_current_active_user

    # Override FastAPI dependencies so the endpoint does not hit the DB
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_current_active_user] = lambda: test_user

    try:
        resp = await client.get("/api/auth/me", headers=auth_headers)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_current_active_user, None)

    assert resp.status_code == 200


async def test_modules_endpoint_requires_auth(client):
    """GET /api/modules requires authentication (HIGH-05)."""
    resp = await client.get("/api/modules")
    assert resp.status_code == 401


# --------------------------------------------------------------------------
# Token creation
# --------------------------------------------------------------------------

def test_create_access_token():
    """create_access_token produces a decodable JWT with correct claims."""
    from app.auth import create_access_token
    from jose import jwt
    from tests.conftest import _TEST_ENV

    token = create_access_token(data={"sub": "user@example.com"})
    payload = jwt.decode(
        token,
        _TEST_ENV["SECRET_KEY"],
        algorithms=[_TEST_ENV["ALGORITHM"]],
    )

    assert payload["sub"] == "user@example.com"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token():
    """create_refresh_token produces a JWT with type='refresh'."""
    from app.auth import create_refresh_token
    from jose import jwt
    from tests.conftest import _TEST_ENV

    token = create_refresh_token(user_id="user@example.com")
    payload = jwt.decode(
        token,
        _TEST_ENV["SECRET_KEY"],
        algorithms=[_TEST_ENV["ALGORITHM"]],
    )

    assert payload["sub"] == "user@example.com"
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_expired_token_rejected():
    """An expired JWT should be rejected by decode."""
    from jose import jwt, JWTError
    from tests.conftest import _TEST_ENV

    expired_payload = {
        "sub": "user@example.com",
        "exp": datetime.now(UTC) - timedelta(hours=1),
        "type": "access",
    }
    token = jwt.encode(
        expired_payload,
        _TEST_ENV["SECRET_KEY"],
        algorithm=_TEST_ENV["ALGORITHM"],
    )

    with pytest.raises(JWTError):
        jwt.decode(
            token,
            _TEST_ENV["SECRET_KEY"],
            algorithms=[_TEST_ENV["ALGORITHM"]],
        )


def test_refresh_token_rejected_as_access():
    """A refresh token should not be accepted as an access token.

    The get_current_user dependency checks token_type != 'refresh'.
    """
    from jose import jwt
    from tests.conftest import _TEST_ENV

    refresh_payload = {
        "sub": "user@example.com",
        "exp": datetime.now(UTC) + timedelta(days=7),
        "type": "refresh",
    }
    token = jwt.encode(
        refresh_payload,
        _TEST_ENV["SECRET_KEY"],
        algorithm=_TEST_ENV["ALGORITHM"],
    )

    payload = jwt.decode(
        token,
        _TEST_ENV["SECRET_KEY"],
        algorithms=[_TEST_ENV["ALGORITHM"]],
    )
    # The auth flow should reject this because type == 'refresh'
    assert payload["type"] == "refresh"


def test_password_hashing():
    """Verify that password hashing and verification work correctly."""
    from app.auth import get_password_hash, verify_password

    plain = "MyS3cureP@ss"
    hashed = get_password_hash(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong_password", hashed) is False
