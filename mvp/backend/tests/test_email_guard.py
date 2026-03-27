"""
Unit tests for the require_verified_email FastAPI dependency.

Both variants (hard block and soft pass-through) are tested without
any database, Redis, or HTTP calls — only the dependency functions
themselves are exercised.
"""

import os

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

# Must be set before any app import so pydantic-settings does not require .env
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_saas_ia")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("ASSEMBLYAI_API_KEY", "MOCK")
os.environ.setdefault("GEMINI_API_KEY", "MOCK")
os.environ.setdefault("CLAUDE_API_KEY", "MOCK")
os.environ.setdefault("GROQ_API_KEY", "MOCK")


@pytest.mark.asyncio
async def test_require_verified_email_passes_when_verified():
    """Verified user passes through without exception."""
    from app.modules.auth_guards.middleware import require_verified_email

    mock_user = MagicMock()
    mock_user.email_verified = True
    result = await require_verified_email(current_user=mock_user)
    assert result is mock_user


@pytest.mark.asyncio
async def test_require_verified_email_blocks_unverified():
    """Unverified user gets 403 with EMAIL_NOT_VERIFIED code."""
    from app.modules.auth_guards.middleware import require_verified_email

    mock_user = MagicMock()
    mock_user.email_verified = False
    with pytest.raises(HTTPException) as exc_info:
        await require_verified_email(current_user=mock_user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "EMAIL_NOT_VERIFIED"


@pytest.mark.asyncio
async def test_require_verified_email_soft_always_passes():
    """Soft variant never blocks — unverified user still passes."""
    from app.modules.auth_guards.middleware import require_verified_email_soft

    mock_user = MagicMock()
    mock_user.email_verified = False
    result = await require_verified_email_soft(current_user=mock_user)
    assert result is mock_user


@pytest.mark.asyncio
async def test_require_verified_email_returns_user():
    """Verified user is returned as-is (not wrapped)."""
    from app.modules.auth_guards.middleware import require_verified_email

    mock_user = MagicMock()
    mock_user.email_verified = True
    mock_user.email = "test@example.com"
    result = await require_verified_email(current_user=mock_user)
    assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_require_verified_email_403_detail_message():
    """The 403 detail contains the expected human-readable message."""
    from app.modules.auth_guards.middleware import require_verified_email

    mock_user = MagicMock()
    mock_user.email_verified = False
    with pytest.raises(HTTPException) as exc_info:
        await require_verified_email(current_user=mock_user)
    detail = exc_info.value.detail
    assert "message" in detail
    assert "verify" in detail["message"].lower()


@pytest.mark.asyncio
async def test_require_verified_email_403_detail_action():
    """The 403 detail contains an 'action' hint for the client."""
    from app.modules.auth_guards.middleware import require_verified_email

    mock_user = MagicMock()
    mock_user.email_verified = False
    with pytest.raises(HTTPException) as exc_info:
        await require_verified_email(current_user=mock_user)
    detail = exc_info.value.detail
    assert "action" in detail
    assert detail["action"] == "resend_verification"


@pytest.mark.asyncio
async def test_require_verified_email_soft_returns_same_object():
    """Soft variant returns the exact same user object passed in."""
    from app.modules.auth_guards.middleware import require_verified_email_soft

    mock_user = MagicMock()
    mock_user.email_verified = True
    mock_user.id = "user-abc-123"
    result = await require_verified_email_soft(current_user=mock_user)
    assert result is mock_user
    assert result.id == "user-abc-123"


@pytest.mark.asyncio
async def test_require_verified_email_soft_verified_user_passes():
    """Soft variant also passes verified users without modification."""
    from app.modules.auth_guards.middleware import require_verified_email_soft

    mock_user = MagicMock()
    mock_user.email_verified = True
    result = await require_verified_email_soft(current_user=mock_user)
    assert result is mock_user


@pytest.mark.asyncio
async def test_require_verified_email_raises_http_exception_not_other():
    """The raised exception is specifically an HTTPException (not ValueError etc.)."""
    from app.modules.auth_guards.middleware import require_verified_email

    mock_user = MagicMock()
    mock_user.email_verified = False
    with pytest.raises(HTTPException):
        await require_verified_email(current_user=mock_user)


@pytest.mark.asyncio
async def test_require_verified_email_detail_is_dict():
    """The HTTPException detail is a dict (not a plain string)."""
    from app.modules.auth_guards.middleware import require_verified_email

    mock_user = MagicMock()
    mock_user.email_verified = False
    with pytest.raises(HTTPException) as exc_info:
        await require_verified_email(current_user=mock_user)
    assert isinstance(exc_info.value.detail, dict)
