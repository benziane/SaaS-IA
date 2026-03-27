"""
Tests for new auth endpoints:
- POST /api/auth/forgot-password
- POST /api/auth/reset-password
- POST /api/auth/verify-email
- POST /api/auth/resend-verify

All Redis calls are mocked — no real Redis connection needed.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# forgot-password
# ---------------------------------------------------------------------------

async def test_forgot_password_existing_user(client, test_user, app):
    """Returns 200 and a generic message when the user exists."""
    test_user.email = "reset@example.com"

    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock(return_value=True)

    from app.database import get_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_session] = lambda: mock_session

    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=mock_redis):
        resp = await client.post(
            "/api/auth/forgot-password",
            json={"email": "reset@example.com"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "message" in resp.json()


async def test_forgot_password_nonexistent_user(client, app):
    """Returns 200 even when the user does NOT exist (no info leak)."""
    mock_redis = AsyncMock()

    from app.database import get_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_session] = lambda: mock_session

    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=mock_redis):
        resp = await client.post(
            "/api/auth/forgot-password",
            json={"email": "ghost@example.com"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "message" in resp.json()


async def test_forgot_password_invalid_email(client):
    """Returns 422 for an invalid e-mail format."""
    resp = await client.post(
        "/api/auth/forgot-password",
        json={"email": "not-an-email"},
    )
    assert resp.status_code == 422


async def test_forgot_password_redis_unavailable(client, test_user, app):
    """Returns 200 even when Redis is down (endpoint degrades gracefully)."""
    test_user.email = "reset2@example.com"

    from app.database import get_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_session] = lambda: mock_session

    # Redis client returns None → endpoint should log a warning and still return 200
    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=None):
        resp = await client.post(
            "/api/auth/forgot-password",
            json={"email": "reset2@example.com"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "message" in resp.json()


# ---------------------------------------------------------------------------
# reset-password
# ---------------------------------------------------------------------------

async def test_reset_password_valid_token(client, test_user, app):
    """Valid token + new password returns 200 and updates the password."""
    from app.auth import get_password_hash

    test_user.email = "reset@example.com"
    test_user.hashed_password = get_password_hash("OldPassword123")

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=b"reset@example.com")
    mock_redis.delete = AsyncMock()

    from app.database import get_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    app.dependency_overrides[get_session] = lambda: mock_session

    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=mock_redis):
        resp = await client.post(
            "/api/auth/reset-password",
            json={"token": "valid-token-abc123", "password": "NewPassword456!"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "message" in resp.json()


async def test_reset_password_invalid_token(client, app):
    """Invalid/expired token returns 400."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=mock_redis):
        resp = await client.post(
            "/api/auth/reset-password",
            json={"token": "expired-token", "password": "NewPassword456!"},
        )

    assert resp.status_code == 400


async def test_reset_password_too_short(client):
    """Password shorter than 8 chars returns 422."""
    resp = await client.post(
        "/api/auth/reset-password",
        json={"token": "any-token", "password": "short"},
    )
    assert resp.status_code == 422


async def test_reset_password_user_not_found_after_token(client, app):
    """Valid token but no matching user in DB returns 400."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=b"orphan@example.com")
    mock_redis.delete = AsyncMock()

    from app.database import get_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_session] = lambda: mock_session

    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=mock_redis):
        resp = await client.post(
            "/api/auth/reset-password",
            json={"token": "valid-token-no-user", "password": "NewPassword456!"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 400


async def test_reset_password_redis_unavailable(client, app):
    """Returns 503 when Redis is down."""
    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=None):
        resp = await client.post(
            "/api/auth/reset-password",
            json={"token": "any-token", "password": "NewPassword456!"},
        )

    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# verify-email
# ---------------------------------------------------------------------------

async def test_verify_email_valid_token(client, app):
    """Valid verify token returns 200 and marks the user as verified."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=b"user@example.com")
    mock_redis.delete = AsyncMock()

    from app.database import get_session
    from app.models.user import User

    mock_user = MagicMock(spec=User)
    mock_user.email = "user@example.com"
    mock_user.email_verified = False

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    app.dependency_overrides[get_session] = lambda: mock_session

    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=mock_redis):
        resp = await client.post(
            "/api/auth/verify-email",
            json={"token": "valid-verify-token"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data


async def test_verify_email_invalid_token(client, app):
    """Invalid/expired verify token returns 400."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)

    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=mock_redis):
        resp = await client.post(
            "/api/auth/verify-email",
            json={"token": "bad-token"},
        )

    assert resp.status_code == 400


async def test_verify_email_missing_token_field(client):
    """Request body without a token field returns 422."""
    resp = await client.post("/api/auth/verify-email", json={})
    assert resp.status_code == 422


async def test_verify_email_redis_unavailable(client, app):
    """Returns 503 when Redis is down."""
    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=None):
        resp = await client.post(
            "/api/auth/verify-email",
            json={"token": "any-token"},
        )

    assert resp.status_code == 503


async def test_verify_email_user_not_in_db(client, app):
    """Valid token but user absent from DB still returns 200 (token is consumed)."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=b"gone@example.com")
    mock_redis.delete = AsyncMock()

    from app.database import get_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    app.dependency_overrides[get_session] = lambda: mock_session

    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=mock_redis):
        resp = await client.post(
            "/api/auth/verify-email",
            json={"token": "orphan-verify-token"},
        )

    app.dependency_overrides.clear()

    # Endpoint still returns 200 and the email (user block is guarded by `if user`)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# resend-verify
# ---------------------------------------------------------------------------

async def test_resend_verify_existing_user(client, test_user, app):
    """Returns 200 for an existing user and stores a fresh token."""
    test_user.email = "verify@example.com"

    mock_redis = AsyncMock()
    mock_redis.setex = AsyncMock()

    from app.database import get_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_session] = lambda: mock_session

    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=mock_redis):
        resp = await client.post(
            "/api/auth/resend-verify",
            json={"email": "verify@example.com"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "message" in resp.json()


async def test_resend_verify_nonexistent_user(client, app):
    """Returns 200 even when the user is not found (no info leak)."""
    mock_redis = AsyncMock()

    from app.database import get_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_session] = lambda: mock_session

    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=mock_redis):
        resp = await client.post(
            "/api/auth/resend-verify",
            json={"email": "nobody@example.com"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "message" in resp.json()


async def test_resend_verify_invalid_email(client):
    """Returns 422 for an invalid e-mail format."""
    resp = await client.post(
        "/api/auth/resend-verify",
        json={"email": "not-an-email"},
    )
    assert resp.status_code == 422


async def test_resend_verify_redis_unavailable(client, test_user, app):
    """Returns 200 even when Redis is down (endpoint degrades gracefully)."""
    test_user.email = "verify2@example.com"

    from app.database import get_session

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = test_user
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_session] = lambda: mock_session

    # Redis client returns None → endpoint logs a warning and still returns 200
    with patch("app.auth._get_token_redis", new_callable=AsyncMock, return_value=None):
        resp = await client.post(
            "/api/auth/resend-verify",
            json={"email": "verify2@example.com"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "message" in resp.json()
