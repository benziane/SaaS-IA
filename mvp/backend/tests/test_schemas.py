"""
Unit tests for Pydantic request/response schemas.

Covers:
- TranscriptionCreate: valid/invalid YouTube URLs, language field
- UserCreate: email validation, password length requirements
- PaginatedResponse: structural correctness
- PasswordChange: field constraints

All tests run WITHOUT a database, Redis, or any external service.
"""

import pytest
from pydantic import ValidationError

from app.schemas.transcription import (
    TranscriptionCreate,
    PaginatedResponse,
    TranscriptionRead,
)
from app.schemas.user import (
    UserCreate,
    PasswordChange,
    UserUpdateProfile,
    TokenResponse,
)


# ---------------------------------------------------------------------------
# Tests: TranscriptionCreate
# ---------------------------------------------------------------------------

class TestTranscriptionCreate:
    """Validation rules for ``TranscriptionCreate``."""

    # -- valid URLs ----------------------------------------------------------

    @pytest.mark.parametrize("url", [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOe",
    ])
    def test_accepts_valid_youtube_urls(self, url):
        obj = TranscriptionCreate(video_url=url)
        assert obj.video_url == url

    def test_default_language_is_auto(self):
        obj = TranscriptionCreate(video_url="https://youtu.be/dQw4w9WgXcQ")
        assert obj.language == "auto"

    def test_explicit_language(self):
        obj = TranscriptionCreate(
            video_url="https://youtu.be/dQw4w9WgXcQ",
            language="fr",
        )
        assert obj.language == "fr"

    # -- invalid inputs ------------------------------------------------------

    def test_rejects_missing_video_url(self):
        with pytest.raises(ValidationError):
            TranscriptionCreate()

    def test_rejects_url_exceeding_max_length(self):
        """video_url has max_length=2048."""
        long_url = "https://www.youtube.com/watch?v=" + "a" * 2048
        with pytest.raises(ValidationError):
            TranscriptionCreate(video_url=long_url)

    def test_rejects_language_exceeding_max_length(self):
        """language has max_length=10."""
        with pytest.raises(ValidationError):
            TranscriptionCreate(
                video_url="https://youtu.be/dQw4w9WgXcQ",
                language="a" * 11,
            )

    # The schema validates that video_url matches known YouTube URL patterns
    # via a field_validator.  Non-YouTube URLs are rejected at the schema level.

    @pytest.mark.parametrize("bad_url", [
        "https://vimeo.com/123",
        "https://www.google.com",
        "not-a-url",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",  # m.youtube.com not in allowed patterns
    ])
    def test_rejects_non_youtube_urls(self, bad_url):
        with pytest.raises(ValidationError):
            TranscriptionCreate(video_url=bad_url)

    def test_rejects_empty_video_url(self):
        with pytest.raises(ValidationError):
            TranscriptionCreate(video_url="")


# ---------------------------------------------------------------------------
# Tests: UserCreate
# ---------------------------------------------------------------------------

class TestUserCreate:
    """Validation rules for ``UserCreate``."""

    def test_valid_user(self):
        user = UserCreate(
            email="user@example.com",
            password="SecureP@ss1",
            full_name="Test User",
        )
        assert user.email == "user@example.com"
        assert user.password == "SecureP@ss1"
        assert user.full_name == "Test User"

    def test_valid_user_without_full_name(self):
        user = UserCreate(email="user@example.com", password="SecureP@ss1")
        assert user.full_name is None

    # -- email validation ----------------------------------------------------

    @pytest.mark.parametrize("bad_email", [
        "not-an-email",
        "@missing-local.com",
        "missing-domain@",
        "spaces in@email.com",
        "",
    ])
    def test_rejects_invalid_email(self, bad_email):
        with pytest.raises(ValidationError):
            UserCreate(email=bad_email, password="ValidP@ss1")

    @pytest.mark.parametrize("good_email", [
        "a@b.com",
        "user.name@domain.co",
        "user+tag@example.org",
    ])
    def test_accepts_valid_email_formats(self, good_email):
        user = UserCreate(email=good_email, password="ValidP@ss1")
        assert user.email is not None

    # -- password validation -------------------------------------------------

    def test_rejects_short_password(self):
        """Password min_length is 8."""
        with pytest.raises(ValidationError):
            UserCreate(email="u@e.com", password="short")

    def test_rejects_too_long_password(self):
        """Password max_length is 100."""
        with pytest.raises(ValidationError):
            UserCreate(email="u@e.com", password="x" * 101)

    def test_accepts_exactly_8_char_password(self):
        """Password must be >= 8 chars and contain a letter + digit."""
        user = UserCreate(email="u@e.com", password="abcdef12")
        assert len(user.password) == 8

    def test_accepts_exactly_100_char_password(self):
        user = UserCreate(email="u@e.com", password="a1" + "x" * 98)
        assert len(user.password) == 100

    def test_rejects_password_without_digit(self):
        with pytest.raises(ValidationError):
            UserCreate(email="u@e.com", password="onlyletters")

    def test_rejects_password_without_letter(self):
        with pytest.raises(ValidationError):
            UserCreate(email="u@e.com", password="12345678")

    # -- missing fields ------------------------------------------------------

    def test_rejects_missing_email(self):
        with pytest.raises(ValidationError):
            UserCreate(password="ValidP@ss1")

    def test_rejects_missing_password(self):
        with pytest.raises(ValidationError):
            UserCreate(email="u@e.com")


# ---------------------------------------------------------------------------
# Tests: PasswordChange
# ---------------------------------------------------------------------------

class TestPasswordChange:
    """Validation rules for ``PasswordChange``."""

    def test_valid_password_change(self):
        pc = PasswordChange(
            current_password="oldPassword1",
            new_password="newPassword1",
        )
        assert pc.current_password == "oldPassword1"
        assert pc.new_password == "newPassword1"

    def test_rejects_empty_current_password(self):
        """current_password min_length is 1."""
        with pytest.raises(ValidationError):
            PasswordChange(current_password="", new_password="newPassword1")

    def test_rejects_short_new_password(self):
        """new_password min_length is 8."""
        with pytest.raises(ValidationError):
            PasswordChange(current_password="old", new_password="short")

    def test_rejects_too_long_new_password(self):
        """new_password max_length is 100."""
        with pytest.raises(ValidationError):
            PasswordChange(current_password="old", new_password="x" * 101)

    def test_rejects_missing_fields(self):
        with pytest.raises(ValidationError):
            PasswordChange()


# ---------------------------------------------------------------------------
# Tests: UserUpdateProfile
# ---------------------------------------------------------------------------

class TestUserUpdateProfile:
    """Validation rules for ``UserUpdateProfile``."""

    def test_valid_update(self):
        up = UserUpdateProfile(full_name="Jane Doe")
        assert up.full_name == "Jane Doe"

    def test_rejects_empty_full_name(self):
        """full_name min_length is 1."""
        with pytest.raises(ValidationError):
            UserUpdateProfile(full_name="")

    def test_rejects_too_long_full_name(self):
        """full_name max_length is 255."""
        with pytest.raises(ValidationError):
            UserUpdateProfile(full_name="x" * 256)


# ---------------------------------------------------------------------------
# Tests: PaginatedResponse
# ---------------------------------------------------------------------------

class TestPaginatedResponse:
    """Structural validation for ``PaginatedResponse``."""

    def test_valid_paginated_response(self):
        resp = PaginatedResponse[str](
            items=["a", "b"],
            total=10,
            skip=0,
            limit=2,
            has_more=True,
        )
        assert resp.items == ["a", "b"]
        assert resp.total == 10
        assert resp.skip == 0
        assert resp.limit == 2
        assert resp.has_more is True

    def test_empty_items(self):
        resp = PaginatedResponse[str](
            items=[],
            total=0,
            skip=0,
            limit=10,
            has_more=False,
        )
        assert resp.items == []
        assert resp.total == 0
        assert resp.has_more is False

    def test_rejects_missing_required_fields(self):
        with pytest.raises(ValidationError):
            PaginatedResponse[str](items=["a"])

    def test_generic_with_int_items(self):
        resp = PaginatedResponse[int](
            items=[1, 2, 3],
            total=100,
            skip=0,
            limit=3,
            has_more=True,
        )
        assert resp.items == [1, 2, 3]


# ---------------------------------------------------------------------------
# Tests: TokenResponse
# ---------------------------------------------------------------------------

class TestTokenResponse:
    """Structural validation for ``TokenResponse``."""

    def test_valid_token_response(self):
        tr = TokenResponse(
            access_token="abc.def.ghi",
            refresh_token="jkl.mno.pqr",
            token_type="bearer",
            expires_in=1800,
        )
        assert tr.access_token == "abc.def.ghi"
        assert tr.token_type == "bearer"
        assert tr.expires_in == 1800

    def test_rejects_missing_access_token(self):
        with pytest.raises(ValidationError):
            TokenResponse(
                refresh_token="jkl.mno.pqr",
                expires_in=1800,
            )
