"""
Tests for the Content Studio module: multi-format AI content generation,
readability scoring, project management, and routes.

All tests run without external services (no DB, no Redis, no AI providers).
"""

import json
import os
import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_project(user_id, title="Test Project", source_text="Sample source content for testing."):
    """Create a mock ContentProject object."""
    from app.models.content_studio import ContentProject

    return ContentProject(
        id=uuid4(),
        user_id=user_id,
        title=title,
        source_type="text",
        source_text=source_text,
        language="auto",
        tone="professional",
        target_audience=None,
        keywords=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_generated_content(project_id, user_id, fmt="blog_article", content="Generated blog content..."):
    """Create a mock GeneratedContent object."""
    from app.models.content_studio import ContentFormat, ContentStatus, GeneratedContent

    return GeneratedContent(
        id=uuid4(),
        project_id=project_id,
        user_id=user_id,
        format=ContentFormat(fmt),
        title="Test Title",
        content=content,
        metadata_json="{}",
        status=ContentStatus.GENERATED,
        provider="gemini",
        word_count=len(content.split()),
        version=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Content generation (service layer with mocked AI)
# ---------------------------------------------------------------------------

class TestContentGeneration:
    """Tests for ContentStudioService.generate_contents with mocked AI."""

    @pytest.mark.asyncio
    async def test_generate_blog_post(self):
        """generate_contents should produce blog content using AI provider."""
        from app.modules.content_studio.service import ContentStudioService
        from app.models.content_studio import ContentStatus

        user_id = uuid4()
        project = _make_project(user_id, source_text="AI is transforming healthcare. " * 50)

        session = AsyncMock()
        session.get = AsyncMock(return_value=project)
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        mock_ai_result = {
            "processed_text": "# How AI is Transforming Healthcare\n\nArtificial intelligence is revolutionizing...",
            "provider": "gemini",
            "model": "gemini-2.0-flash",
        }

        with patch(
            "app.ai_assistant.service.AIAssistantService.process_text_with_provider",
            new_callable=AsyncMock,
            return_value=mock_ai_result,
        ):
            contents = await ContentStudioService.generate_contents(
                project_id=project.id,
                user_id=user_id,
                formats=["blog_article"],
                session=session,
            )

        assert len(contents) == 1
        assert contents[0].status == ContentStatus.GENERATED
        assert len(contents[0].content) > 0

    @pytest.mark.asyncio
    async def test_generate_tweet(self):
        """generate_contents should produce twitter thread content."""
        from app.modules.content_studio.service import ContentStudioService
        from app.models.content_studio import ContentFormat, ContentStatus

        user_id = uuid4()
        project = _make_project(user_id, source_text="Breaking news about AI regulation.")

        session = AsyncMock()
        session.get = AsyncMock(return_value=project)
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        mock_ai_result = {
            "processed_text": "1/ AI regulation is here. Thread.\n---\n2/ The EU AI Act...",
            "provider": "gemini",
            "model": "gemini-2.0-flash",
        }

        with patch(
            "app.ai_assistant.service.AIAssistantService.process_text_with_provider",
            new_callable=AsyncMock,
            return_value=mock_ai_result,
        ):
            contents = await ContentStudioService.generate_contents(
                project_id=project.id,
                user_id=user_id,
                formats=["twitter_thread"],
                session=session,
            )

        assert len(contents) == 1
        assert contents[0].format == ContentFormat.TWITTER_THREAD
        assert contents[0].status == ContentStatus.GENERATED

    @pytest.mark.asyncio
    async def test_generate_linkedin(self):
        """generate_contents should produce LinkedIn post content."""
        from app.modules.content_studio.service import ContentStudioService
        from app.models.content_studio import ContentFormat, ContentStatus

        user_id = uuid4()
        project = _make_project(user_id, source_text="Leadership lessons from running a startup.")

        session = AsyncMock()
        session.get = AsyncMock(return_value=project)
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        mock_ai_result = {
            "processed_text": "I learned something important this week.\n\nRunning a startup teaches you...\n\n#leadership #startup",
            "provider": "gemini",
            "model": "gemini-2.0-flash",
        }

        with patch(
            "app.ai_assistant.service.AIAssistantService.process_text_with_provider",
            new_callable=AsyncMock,
            return_value=mock_ai_result,
        ):
            contents = await ContentStudioService.generate_contents(
                project_id=project.id,
                user_id=user_id,
                formats=["linkedin_post"],
                session=session,
            )

        assert len(contents) == 1
        assert contents[0].format == ContentFormat.LINKEDIN_POST

    @pytest.mark.asyncio
    async def test_generate_multiple_formats(self):
        """Should generate multiple formats in one call."""
        from app.modules.content_studio.service import ContentStudioService

        user_id = uuid4()
        project = _make_project(user_id, source_text="Content about machine learning.")

        session = AsyncMock()
        session.get = AsyncMock(return_value=project)
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        mock_ai_result = {
            "processed_text": "# Generated Content\n\nSome content here...",
            "provider": "gemini",
            "model": "gemini-2.0-flash",
        }

        with patch(
            "app.ai_assistant.service.AIAssistantService.process_text_with_provider",
            new_callable=AsyncMock,
            return_value=mock_ai_result,
        ):
            contents = await ContentStudioService.generate_contents(
                project_id=project.id,
                user_id=user_id,
                formats=["blog_article", "twitter_thread", "linkedin_post"],
                session=session,
            )

        assert len(contents) == 3

    @pytest.mark.asyncio
    async def test_generate_invalid_format_skipped(self):
        """Invalid format names should be skipped without error."""
        from app.modules.content_studio.service import ContentStudioService

        user_id = uuid4()
        project = _make_project(user_id, source_text="Some content.")

        session = AsyncMock()
        session.get = AsyncMock(return_value=project)
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        mock_ai_result = {
            "processed_text": "Generated content",
            "provider": "gemini",
        }

        with patch(
            "app.ai_assistant.service.AIAssistantService.process_text_with_provider",
            new_callable=AsyncMock,
            return_value=mock_ai_result,
        ):
            contents = await ContentStudioService.generate_contents(
                project_id=project.id,
                user_id=user_id,
                formats=["blog_article", "nonexistent_format"],
                session=session,
            )

        # Only blog_article should be generated; nonexistent_format is skipped
        assert len(contents) == 1


# ---------------------------------------------------------------------------
# Project management
# ---------------------------------------------------------------------------

class TestProjectManagement:
    """Tests for project listing, content retrieval, and deletion."""

    @pytest.mark.asyncio
    async def test_list_projects_paginated(self):
        """list_projects should return projects with total count."""
        from app.modules.content_studio.service import ContentStudioService

        user_id = uuid4()
        projects = [_make_project(user_id, f"Project {i}") for i in range(3)]

        session = AsyncMock()
        # Count query
        count_result = MagicMock()
        count_result.scalar_one.return_value = 3
        # Projects query
        proj_result = MagicMock()
        proj_result.scalars.return_value.all.return_value = projects

        session.execute = AsyncMock(side_effect=[count_result, proj_result])

        result_projects, total = await ContentStudioService.list_projects(
            user_id, session, skip=0, limit=20
        )

        assert total == 3
        assert len(result_projects) == 3

    @pytest.mark.asyncio
    async def test_get_project_contents(self):
        """get_project_contents should return all content for a project."""
        from app.modules.content_studio.service import ContentStudioService

        user_id = uuid4()
        project_id = uuid4()
        contents = [
            _make_generated_content(project_id, user_id, "blog_article"),
            _make_generated_content(project_id, user_id, "twitter_thread"),
        ]

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = contents
        session.execute = AsyncMock(return_value=mock_result)

        result = await ContentStudioService.get_project_contents(
            project_id, user_id, session
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete_project(self):
        """delete_project should remove project and its contents."""
        from app.modules.content_studio.service import ContentStudioService

        user_id = uuid4()
        project = _make_project(user_id)

        session = AsyncMock()
        session.get = AsyncMock(return_value=project)
        # Contents query for deletion
        mock_contents_result = MagicMock()
        mock_contents_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_contents_result)
        session.delete = AsyncMock()
        session.commit = AsyncMock()

        result = await ContentStudioService.delete_project(
            project.id, user_id, session
        )

        assert result is True
        session.delete.assert_awaited()

    @pytest.mark.asyncio
    async def test_delete_project_wrong_user(self):
        """Deleting another user's project should return False."""
        from app.modules.content_studio.service import ContentStudioService

        owner_id = uuid4()
        attacker_id = uuid4()
        project = _make_project(owner_id)

        session = AsyncMock()
        session.get = AsyncMock(return_value=project)

        result = await ContentStudioService.delete_project(
            project.id, attacker_id, session
        )

        assert result is False


# ---------------------------------------------------------------------------
# Readability scoring
# ---------------------------------------------------------------------------

class TestReadabilityScore:
    """Tests for ContentStudioService._compute_readability."""

    def test_readability_basic_fallback(self):
        """When textstat is not available, returns basic word count."""
        from app.modules.content_studio.service import ContentStudioService

        text = "This is a sample sentence for testing readability scoring."

        with patch("app.modules.content_studio.service.HAS_TEXTSTAT", False):
            result = ContentStudioService._compute_readability(text)

        assert result["source"] == "basic"
        assert result["word_count"] == len(text.split())
        assert "reading_time_minutes" in result

    def test_readability_with_textstat(self):
        """When textstat is available, returns comprehensive metrics."""
        import sys
        import app.modules.content_studio.service as svc
        from app.modules.content_studio.service import ContentStudioService

        long_text = (
            "This is a comprehensive test of readability scoring. "
            "The function should compute multiple readability metrics including "
            "Flesch Reading Ease, Flesch-Kincaid Grade Level, Gunning Fog index, "
            "SMOG index, Automated Readability Index, and Coleman-Liau index. "
            "These are standard metrics used in computational linguistics."
        ) * 3

        mock_textstat = MagicMock()
        mock_textstat.flesch_reading_ease.return_value = 65.0
        mock_textstat.flesch_kincaid_grade.return_value = 8.5
        mock_textstat.gunning_fog.return_value = 10.2
        mock_textstat.smog_index.return_value = 9.0
        mock_textstat.automated_readability_index.return_value = 8.1
        mock_textstat.coleman_liau_index.return_value = 9.5

        original_has = svc.HAS_TEXTSTAT
        original_textstat = getattr(svc, "textstat", None)
        try:
            svc.HAS_TEXTSTAT = True
            svc.textstat = mock_textstat
            result = ContentStudioService._compute_readability(long_text)
        finally:
            svc.HAS_TEXTSTAT = original_has
            if original_textstat is not None:
                svc.textstat = original_textstat
            elif hasattr(svc, "textstat"):
                delattr(svc, "textstat")

        assert result["source"] == "textstat"
        assert result["flesch_reading_ease"] == 65.0
        assert result["difficulty_level"] == "easy"
        assert "word_count" in result

    def test_readability_difficulty_levels(self):
        """Difficulty level categorization based on Flesch score."""
        import app.modules.content_studio.service as svc
        from app.modules.content_studio.service import ContentStudioService

        mock_textstat = MagicMock()
        mock_textstat.flesch_reading_ease.return_value = 75.0
        mock_textstat.flesch_kincaid_grade.return_value = 6.0
        mock_textstat.gunning_fog.return_value = 8.0
        mock_textstat.smog_index.return_value = 7.0
        mock_textstat.automated_readability_index.return_value = 6.0
        mock_textstat.coleman_liau_index.return_value = 7.0

        original_has = svc.HAS_TEXTSTAT
        original_textstat = getattr(svc, "textstat", None)
        try:
            svc.HAS_TEXTSTAT = True
            svc.textstat = mock_textstat

            # Easy (>= 60)
            result = ContentStudioService._compute_readability("Easy text.")
            assert result["difficulty_level"] == "easy"

            # Hard (< 30)
            mock_textstat.flesch_reading_ease.return_value = 20.0
            result = ContentStudioService._compute_readability("Hard text.")
            assert result["difficulty_level"] == "hard"
        finally:
            svc.HAS_TEXTSTAT = original_has
            if original_textstat is not None:
                svc.textstat = original_textstat
            elif hasattr(svc, "textstat"):
                delattr(svc, "textstat")


# ---------------------------------------------------------------------------
# Available formats
# ---------------------------------------------------------------------------

class TestAvailableFormats:
    """Tests for format enumeration."""

    def test_content_format_enum_has_10_formats(self):
        """ContentFormat enum should have exactly 10 formats."""
        from app.models.content_studio import ContentFormat

        assert len(ContentFormat) == 10

    def test_expected_formats_present(self):
        """All expected format IDs should be in the enum."""
        from app.models.content_studio import ContentFormat

        expected = [
            "blog_article", "twitter_thread", "linkedin_post", "newsletter",
            "instagram_carousel", "youtube_description", "seo_meta",
            "press_release", "email_campaign", "podcast_notes",
        ]
        actual = [f.value for f in ContentFormat]
        for fmt in expected:
            assert fmt in actual, f"Missing format: {fmt}"

    def test_format_prompts_cover_all_formats(self):
        """FORMAT_PROMPTS dict should have a prompt for every ContentFormat."""
        from app.models.content_studio import ContentFormat
        from app.modules.content_studio.service import FORMAT_PROMPTS

        for fmt in ContentFormat:
            assert fmt in FORMAT_PROMPTS, f"Missing prompt for format: {fmt.value}"


# ---------------------------------------------------------------------------
# Route / endpoint auth tests
# ---------------------------------------------------------------------------

class TestContentStudioEndpointAuth:
    """Tests for content studio route authentication."""

    @pytest.mark.asyncio
    async def test_create_project_endpoint_returns_401_without_token(self, client):
        """POST /api/content-studio/projects should return 401 without auth."""
        response = await client.post(
            "/api/content-studio/projects",
            json={
                "title": "Test Project",
                "source_type": "text",
                "source_text": "Sample text",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_projects_endpoint_returns_401_without_token(self, client):
        """GET /api/content-studio/projects should return 401 without auth."""
        response = await client.get("/api/content-studio/projects")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_formats_endpoint_is_public(self, client):
        """GET /api/content-studio/formats should be accessible without auth (no Depends(get_current_user))."""
        response = await client.get("/api/content-studio/formats")
        # This endpoint has no auth dependency, so it should return 200
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert len(data["formats"]) == 10

    @pytest.mark.asyncio
    async def test_formats_endpoint_returns_correct_ids(self, client):
        """The /formats endpoint should return all 10 format IDs."""
        response = await client.get("/api/content-studio/formats")
        assert response.status_code == 200
        format_ids = [f["id"] for f in response.json()["formats"]]
        expected = [
            "blog_article", "twitter_thread", "linkedin_post", "newsletter",
            "instagram_carousel", "youtube_description", "seo_meta",
            "press_release", "email_campaign", "podcast_notes",
        ]
        for fmt in expected:
            assert fmt in format_ids


# ---------------------------------------------------------------------------
# Project creation
# ---------------------------------------------------------------------------

class TestProjectCreation:
    """Tests for ContentStudioService.create_project."""

    @pytest.mark.asyncio
    async def test_create_project_from_text(self):
        """create_project with source_type='text' stores the text directly."""
        from app.modules.content_studio.service import ContentStudioService

        user_id = uuid4()
        session = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        project = await ContentStudioService.create_project(
            user_id=user_id,
            title="My Article",
            source_type="text",
            source_text="This is the source material for content generation.",
            source_id=None,
            session=session,
            language="en",
            tone="engaging",
            target_audience="developers",
            keywords=["AI", "coding"],
        )

        assert project.title == "My Article"
        assert project.source_type == "text"
        assert project.tone == "engaging"
        assert project.language == "en"
        assert project.target_audience == "developers"
        session.commit.assert_awaited_once()
