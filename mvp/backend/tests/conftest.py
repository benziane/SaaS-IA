"""
Shared pytest fixtures for the SaaS-IA backend test suite.

All fixtures are designed to run WITHOUT external services
(no database, no Redis, no API keys).
"""

import os
import pytest
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# Environment-level overrides
# ---------------------------------------------------------------------------
# These must be set BEFORE any application module is imported so that
# pydantic-settings picks them up from the environment instead of
# requiring a .env file or real credentials.

_TEST_ENV = {
    "ENVIRONMENT": "testing",
    "SECRET_KEY": "test-secret-key-for-unit-tests-only-not-for-production",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    "REFRESH_TOKEN_EXPIRE_DAYS": "7",
    # Use a PostgreSQL-compatible URL so that app.database's engine
    # creation with pool_size/max_overflow does not error. The engine
    # is never actually connected during tests.
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_saas_ia",
    "REDIS_URL": "redis://localhost:6379/15",
    "ASSEMBLYAI_API_KEY": "MOCK",
    "GEMINI_API_KEY": "MOCK",
    "CLAUDE_API_KEY": "MOCK",
    "GROQ_API_KEY": "MOCK",
    "DEBUG": "true",
    "LOG_LEVEL": "DEBUG",
}

for key, value in _TEST_ENV.items():
    os.environ.setdefault(key, value)


# ---------------------------------------------------------------------------
# Fixtures: settings
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_settings():
    """Return a Settings instance configured for testing.

    Patches environment variables so that ``Settings()`` can be
    instantiated without a .env file or real credentials.
    """
    with patch.dict(os.environ, _TEST_ENV, clear=False):
        from app.config import Settings
        return Settings()


# ---------------------------------------------------------------------------
# Fixtures: FastAPI app & async client
# ---------------------------------------------------------------------------

@pytest.fixture()
def app():
    """
    Return the FastAPI application instance.

    The app is imported from the real entry point so that all routers,
    middleware, and module discovery are exercised.  Module-level engine
    creation is allowed (PostgreSQL URL in _TEST_ENV) but no real DB
    connection is made.
    """
    with patch.dict(os.environ, _TEST_ENV, clear=False):
        from app.main import app as _app
        yield _app


@pytest.fixture()
async def client(app):
    """
    Provide an httpx.AsyncClient configured for the test app.

    Uses ``httpx.ASGITransport`` so that requests go through the full
    ASGI middleware stack without needing a running server.

    The database ``init_db`` and ``engine.dispose`` calls from the
    lifespan manager are mocked out so that tests do not need a live
    PostgreSQL instance.
    """
    import httpx

    transport = httpx.ASGITransport(app=app)
    with (
        patch("app.database.init_db", new_callable=AsyncMock),
        patch("app.database.engine") as mock_engine,
        patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
    ):
        mock_engine.dispose = AsyncMock()
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as ac:
            yield ac


@pytest.fixture()
def auth_headers():
    """
    Return an Authorization header dict containing a valid JWT for a
    test user.  The token is signed with the test SECRET_KEY.
    """
    from jose import jwt

    secret = _TEST_ENV["SECRET_KEY"]
    algorithm = _TEST_ENV["ALGORITHM"]
    expire = datetime.now(UTC) + timedelta(minutes=30)

    payload = {
        "sub": "testuser@example.com",
        "exp": expire,
        "type": "access",
    }
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def test_user():
    """Return a mock User object suitable for dependency injection."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "testuser@example.com"
    user.full_name = "Test User"
    user.role = "user"
    user.is_active = True
    user.email_verified = True
    user.hashed_password = "$2b$12$mock_hashed_password_for_testing"
    user.created_at = datetime.now(UTC)
    user.updated_at = datetime.now(UTC)
    return user


def override_auth(app, user):
    """Override both ``get_current_user`` and the email-verification guards.

    The ``require_verified_email`` guard resolves its user via
    ``_lazy_get_current_user`` -- a *different* dependency from
    ``app.auth.get_current_user``.  Overriding only ``get_current_user``
    leaves the guard using its own token-parsing path, which returns 403
    for mock users that lack a real JWT.

    Call this helper instead of setting ``get_current_user`` manually::

        override_auth(app, test_user)
        ...
        app.dependency_overrides.clear()
    """
    from app.auth import get_current_user
    from app.modules.auth_guards.middleware import (
        require_verified_email,
        require_verified_email_soft,
    )

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_verified_email] = lambda: user
    app.dependency_overrides[require_verified_email_soft] = lambda: user


@pytest.fixture()
async def session():
    """
    Provide an async in-memory SQLite session.

    This creates all tables in a fresh SQLite database, yields the
    session, and tears down after the test.  No PostgreSQL required.
    """
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlmodel import SQLModel
    from sqlmodel.ext.asyncio.session import AsyncSession

    # Import all models so that SQLModel.metadata knows about every table
    # and create_all can resolve foreign keys (e.g. users -> tenants).
    import app.models.tenant  # noqa: F401
    import app.models.user  # noqa: F401
    import app.models.transcription  # noqa: F401
    import app.models.conversation  # noqa: F401

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as sess:
        yield sess

    await engine.dispose()


# ---------------------------------------------------------------------------
# Fixtures: sample user data
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_user_id():
    """Return a deterministic UUID for a test user."""
    return uuid4()


@pytest.fixture()
def sample_user_email():
    return "testuser@example.com"


@pytest.fixture()
def sample_user_password():
    return "SecureP@ssw0rd123"


@pytest.fixture()
def sample_user_create_payload():
    """Return a dictionary suitable for constructing ``UserCreate``."""
    return {
        "email": "newuser@example.com",
        "password": "Val1dPassw0rd!",
        "full_name": "Test User",
    }


@pytest.fixture()
def sample_user_create_payload_minimal():
    """Return a ``UserCreate`` payload with only required fields."""
    return {
        "email": "minimal@example.com",
        "password": "MinimalP4ss",
    }


# ---------------------------------------------------------------------------
# Fixtures: sample transcription data
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_youtube_urls():
    """Return a list of valid YouTube URL variants."""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
    ]


@pytest.fixture()
def sample_invalid_urls():
    """Return a list of URLs that are NOT valid YouTube URLs."""
    return [
        "https://www.google.com",
        "https://vimeo.com/123456",
        "not-a-url",
        "",
    ]


@pytest.fixture()
def sample_transcription_create_payload():
    """Return a dictionary suitable for constructing ``TranscriptionCreate``."""
    return {
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "language": "fr",
    }


@pytest.fixture()
def sample_transcription_result():
    """Return a mock transcription result dictionary."""
    return {
        "text": "Ceci est une transcription de test.",
        "confidence": 0.95,
        "duration_seconds": 180,
    }


# ---------------------------------------------------------------------------
# Fixtures: sample classification texts
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_religious_text():
    """Return text that should be classified as religious content."""
    return (
        "Le prophète, paix soit sur lui, a transmis un hadith rapporté dans le coran. "
        "Allah a révélé des versets au messager pour guider les croyants dans leur foi. "
        "La prière et le dhikr sont des actes d'adoration essentiels pour le musulman."
    )


@pytest.fixture()
def sample_scientific_text():
    """Return text that should be classified as scientific content."""
    return (
        "Cette étude analyse les données obtenues par observation. "
        "L'hypothèse principale repose sur un modèle statistique validé par "
        "une corrélation significative entre les variables mesurées. "
        "La méthode scientifique et le protocole expérimental ont produit "
        "des résultats cohérents avec la théorie initiale. "
        "L'échantillon de recherche confirme l'analyse."
    )


@pytest.fixture()
def sample_general_text():
    """Return text with no strong domain signal."""
    return "Bonjour, comment allez-vous aujourd'hui ? Il fait beau dehors."


@pytest.fixture()
def sample_medical_text():
    """Return text that should be classified as medical content."""
    return (
        "Le patient a recu un diagnostic de maladie chronique. "
        "Le medecin a prescrit un traitement et un medicament adapte. "
        "Le symptome principal necessite une therapie et un suivi en clinique. "
        "Une ordonnance a ete delivree a l'hopital pour la chirurgie prevue. "
        "La sante du patient reste la priorite."
    )
