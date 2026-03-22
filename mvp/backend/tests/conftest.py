"""
Shared pytest fixtures for the SaaS-IA backend test suite.

All fixtures are designed to run WITHOUT external services
(no database, no Redis, no API keys).
"""

import os
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch


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
    "DATABASE_URL": "sqlite+aiosqlite:///test.db",
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
