"""
Tests for the Transcription module: service layer and API routes.

Covers TranscriptionService (create, list, get, delete, stats, status lifecycle)
and the /api/transcription endpoints via the ASGI client.

All tests run without external services (AssemblyAI, yt-dlp, faster-whisper
are mocked).
"""

import os
import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------


class TestTranscriptionServiceCreateJob:
    """Tests for TranscriptionService.create_job."""

    async def test_create_transcription_youtube_url(self, session, sample_user_id):
        """A valid YouTube URL creates a job with PENDING status."""
        from app.modules.transcription.service import TranscriptionService
        from app.models.transcription import TranscriptionStatus

        svc = TranscriptionService()
        job = await svc.create_job(
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            user_id=sample_user_id,
            language="fr",
            session=session,
        )

        assert job is not None
        assert job.video_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert job.user_id == sample_user_id
        assert job.language == "fr"
        assert job.status == TranscriptionStatus.PENDING
        assert job.source_type == "youtube"
        assert job.id is not None

    async def test_create_transcription_auto_language(self, session, sample_user_id):
        """When language is None, it defaults to 'auto'."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()
        job = await svc.create_job(
            video_url="https://youtu.be/dQw4w9WgXcQ",
            user_id=sample_user_id,
            language=None,
            session=session,
        )

        assert job.language == "auto"

    async def test_create_transcription_upload_source(self, session, sample_user_id):
        """Upload source type and original_filename are persisted."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()
        job = await svc.create_job(
            video_url="upload://interview.mp3",
            user_id=sample_user_id,
            language="en",
            session=session,
            source_type="upload",
            original_filename="interview.mp3",
        )

        assert job.source_type == "upload"
        assert job.original_filename == "interview.mp3"

    async def test_create_transcription_initial_retry_count(self, session, sample_user_id):
        """New job starts with retry_count == 0."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()
        job = await svc.create_job(
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            user_id=sample_user_id,
            language="auto",
            session=session,
        )

        assert job.retry_count == 0


class TestTranscriptionServiceListJobs:
    """Tests for TranscriptionService.list_user_jobs."""

    async def test_list_transcriptions_empty(self, session, sample_user_id):
        """Empty list returned for a user with no transcriptions."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()
        items, total = await svc.list_user_jobs(sample_user_id, session)

        assert items == []
        assert total == 0

    async def test_list_transcriptions_pagination(self, session, sample_user_id):
        """Skip and limit correctly paginate results."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()

        # Create 5 jobs
        for i in range(5):
            await svc.create_job(
                video_url=f"https://www.youtube.com/watch?v=test{i:04d}abcd",
                user_id=sample_user_id,
                language="auto",
                session=session,
            )

        # Get first page of 2
        items, total = await svc.list_user_jobs(
            sample_user_id, session, skip=0, limit=2
        )
        assert len(items) == 2
        assert total == 5

        # Get second page of 2
        items2, total2 = await svc.list_user_jobs(
            sample_user_id, session, skip=2, limit=2
        )
        assert len(items2) == 2
        assert total2 == 5

        # Get last page
        items3, total3 = await svc.list_user_jobs(
            sample_user_id, session, skip=4, limit=2
        )
        assert len(items3) == 1
        assert total3 == 5

    async def test_list_transcriptions_filter_by_status(self, session, sample_user_id):
        """Filtering by status returns only matching jobs."""
        from app.modules.transcription.service import TranscriptionService
        from app.models.transcription import TranscriptionStatus

        svc = TranscriptionService()

        job1 = await svc.create_job(
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            user_id=sample_user_id,
            language="auto",
            session=session,
        )
        # Manually mark one as completed
        job1.status = TranscriptionStatus.COMPLETED
        session.add(job1)
        await session.commit()

        await svc.create_job(
            video_url="https://www.youtube.com/watch?v=abc123efghij",
            user_id=sample_user_id,
            language="auto",
            session=session,
        )

        items, total = await svc.list_user_jobs(
            sample_user_id, session, status=TranscriptionStatus.COMPLETED
        )
        assert total == 1
        assert items[0].status == TranscriptionStatus.COMPLETED

    async def test_list_transcriptions_isolation(self, session):
        """User A cannot see User B's transcriptions."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()
        user_a = uuid4()
        user_b = uuid4()

        await svc.create_job(
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            user_id=user_a,
            language="auto",
            session=session,
        )

        items, total = await svc.list_user_jobs(user_b, session)
        assert total == 0
        assert items == []


class TestTranscriptionServiceGetJob:
    """Tests for TranscriptionService.get_job."""

    async def test_get_transcription_found(self, session, sample_user_id):
        """Getting an existing job returns it."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()
        job = await svc.create_job(
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            user_id=sample_user_id,
            language="fr",
            session=session,
        )

        fetched = await svc.get_job(job.id, session)
        assert fetched is not None
        assert fetched.id == job.id
        assert fetched.video_url == job.video_url

    async def test_get_transcription_not_found(self, session):
        """Getting a non-existent job returns None."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()
        fetched = await svc.get_job(uuid4(), session)
        assert fetched is None


class TestTranscriptionServiceDeleteJob:
    """Tests for TranscriptionService.delete_job."""

    async def test_delete_transcription(self, session, sample_user_id):
        """Deleting an existing job returns True and removes it."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()
        job = await svc.create_job(
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            user_id=sample_user_id,
            language="auto",
            session=session,
        )

        result = await svc.delete_job(job.id, session)
        assert result is True

        # Verify it's gone
        fetched = await svc.get_job(job.id, session)
        assert fetched is None

    async def test_delete_transcription_not_found(self, session):
        """Deleting a non-existent job returns False."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()
        result = await svc.delete_job(uuid4(), session)
        assert result is False


class TestTranscriptionStatusLifecycle:
    """Tests for status transitions and processing logic."""

    async def test_transcription_status_lifecycle(self, session, sample_user_id):
        """A job can transition from PENDING -> PROCESSING -> COMPLETED."""
        from app.modules.transcription.service import TranscriptionService
        from app.models.transcription import Transcription, TranscriptionStatus

        svc = TranscriptionService()
        job = await svc.create_job(
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            user_id=sample_user_id,
            language="auto",
            session=session,
        )
        assert job.status == TranscriptionStatus.PENDING

        # Simulate processing
        job.status = TranscriptionStatus.PROCESSING
        job.updated_at = datetime.now(UTC)
        session.add(job)
        await session.commit()
        await session.refresh(job)
        assert job.status == TranscriptionStatus.PROCESSING

        # Simulate completion
        job.status = TranscriptionStatus.COMPLETED
        job.text = "Transcribed content here."
        job.confidence = 0.92
        job.duration_seconds = 120
        job.completed_at = datetime.now(UTC)
        job.updated_at = datetime.now(UTC)
        session.add(job)
        await session.commit()
        await session.refresh(job)

        assert job.status == TranscriptionStatus.COMPLETED
        assert job.text == "Transcribed content here."
        assert job.confidence == 0.92
        assert job.duration_seconds == 120
        assert job.completed_at is not None

    async def test_transcription_status_failed(self, session, sample_user_id):
        """A job can transition to FAILED with an error message."""
        from app.modules.transcription.service import TranscriptionService
        from app.models.transcription import TranscriptionStatus

        svc = TranscriptionService()
        job = await svc.create_job(
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            user_id=sample_user_id,
            language="auto",
            session=session,
        )

        # Simulate failure
        job.status = TranscriptionStatus.FAILED
        job.error = "API rate limit exceeded"
        job.retry_count = 1
        job.updated_at = datetime.now(UTC)
        session.add(job)
        await session.commit()
        await session.refresh(job)

        assert job.status == TranscriptionStatus.FAILED
        assert job.error == "API rate limit exceeded"
        assert job.retry_count == 1

    async def test_transcription_error_truncated(self, session, sample_user_id):
        """Error messages longer than 1000 chars should be storable (model allows 1000)."""
        from app.modules.transcription.service import TranscriptionService
        from app.models.transcription import TranscriptionStatus

        svc = TranscriptionService()
        job = await svc.create_job(
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            user_id=sample_user_id,
            language="auto",
            session=session,
        )

        long_error = "x" * 1000
        job.status = TranscriptionStatus.FAILED
        job.error = long_error
        session.add(job)
        await session.commit()
        await session.refresh(job)

        assert len(job.error) == 1000


class TestTranscriptionServiceStats:
    """Tests for TranscriptionService.get_user_stats."""

    async def test_stats_empty(self, session, sample_user_id):
        """Stats for a user with no jobs returns zero counts."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()
        stats = await svc.get_user_stats(sample_user_id, session)

        assert stats["total_transcriptions"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
        assert stats["pending"] == 0
        assert stats["processing"] == 0
        assert stats["total_duration_seconds"] == 0
        assert stats["recent_transcriptions"] == []

    async def test_stats_with_completed_jobs(self, session, sample_user_id):
        """Stats correctly aggregate completed jobs."""
        from app.modules.transcription.service import TranscriptionService
        from app.models.transcription import TranscriptionStatus

        svc = TranscriptionService()

        # Create and complete two jobs
        for i in range(2):
            job = await svc.create_job(
                video_url=f"https://www.youtube.com/watch?v=test{i:04d}abcd",
                user_id=sample_user_id,
                language="auto",
                session=session,
            )
            job.status = TranscriptionStatus.COMPLETED
            job.duration_seconds = 100 + i * 50
            job.confidence = 0.90 + i * 0.05
            job.completed_at = datetime.now(UTC)
            session.add(job)
        await session.commit()

        stats = await svc.get_user_stats(sample_user_id, session)

        assert stats["total_transcriptions"] == 2
        assert stats["completed"] == 2
        assert stats["total_duration_seconds"] == 250  # 100 + 150
        assert stats["avg_confidence"] is not None
        assert len(stats["recent_transcriptions"]) == 2


class TestTranscriptionServiceMockTranscribe:
    """Tests for the mock transcription path."""

    async def test_mock_transcribe_returns_result(self):
        """_mock_transcribe returns text, confidence, and duration."""
        from app.modules.transcription.service import TranscriptionService

        svc = TranscriptionService()
        assert svc.mock_mode is True  # in test env, ASSEMBLYAI_API_KEY=MOCK

        result = await svc._mock_transcribe("https://www.youtube.com/watch?v=test1234abcd")

        assert "text" in result
        assert len(result["text"]) > 0
        assert result["confidence"] == 0.95
        assert result["duration_seconds"] == 180
        assert "test1234abcd" in result["text"]


class TestTranscriptionSchemaValidation:
    """Tests for TranscriptionCreate schema validation."""

    def test_schema_valid_youtube_url(self):
        """Standard YouTube URL variants are accepted."""
        from app.schemas.transcription import TranscriptionCreate

        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOei",
        ]
        for url in valid_urls:
            payload = TranscriptionCreate(video_url=url, language="auto")
            assert payload.video_url == url

    def test_schema_invalid_url_rejected(self):
        """Non-YouTube URLs are rejected for source_type='youtube'."""
        from app.schemas.transcription import TranscriptionCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TranscriptionCreate(
                video_url="https://www.google.com",
                language="auto",
            )

    def test_schema_empty_url_rejected(self):
        """Empty URL is rejected."""
        from app.schemas.transcription import TranscriptionCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TranscriptionCreate(video_url="", language="auto")

    def test_schema_generic_url_accepted_for_url_source(self):
        """Any HTTP URL is accepted when source_type='url'."""
        from app.schemas.transcription import TranscriptionCreate

        payload = TranscriptionCreate(
            video_url="https://example.com/video.mp4",
            source_type="url",
        )
        assert payload.video_url == "https://example.com/video.mp4"
        assert payload.source_type == "url"

    def test_schema_invalid_source_type_rejected(self):
        """Invalid source_type raises validation error."""
        from app.schemas.transcription import TranscriptionCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TranscriptionCreate(
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                source_type="invalid",
            )


# ---------------------------------------------------------------------------
# Route-level tests (via ASGI client)
#
# These use app.dependency_overrides to replace FastAPI dependencies, following
# the pattern established in tests/test_auth_flow.py and tests/test_pipelines_service.py.
# ---------------------------------------------------------------------------


class TestTranscriptionRouteAuth:
    """Tests for authentication on transcription endpoints."""

    async def test_create_endpoint_auth_required(self, client):
        """POST /api/transcription/ without token returns 401."""
        resp = await client.post(
            "/api/transcription/",
            json={
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "language": "auto",
            },
        )
        assert resp.status_code == 401

    async def test_list_endpoint_auth_required(self, client):
        """GET /api/transcription/ without token returns 401."""
        resp = await client.get("/api/transcription/")
        assert resp.status_code == 401

    async def test_get_endpoint_auth_required(self, client):
        """GET /api/transcription/{id} without token returns 401."""
        resp = await client.get(f"/api/transcription/{uuid4()}")
        assert resp.status_code == 401

    async def test_delete_endpoint_auth_required(self, client):
        """DELETE /api/transcription/{id} without token returns 401."""
        resp = await client.delete(f"/api/transcription/{uuid4()}")
        assert resp.status_code == 401

    async def test_stats_endpoint_auth_required(self, client):
        """GET /api/transcription/stats without token returns 401."""
        resp = await client.get("/api/transcription/stats")
        assert resp.status_code == 401


class TestTranscriptionRouteCreate:
    """Tests for POST /api/transcription/."""

    async def test_create_endpoint_valid(self, app, auth_headers, test_user):
        """Valid creation request returns 201 with a transcription object."""
        import httpx
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.billing.middleware import require_transcription_quota
        from app.modules.transcription.routes import get_transcription_service

        mock_session = AsyncMock()

        # Build a mock job that the service will return
        mock_job = MagicMock()
        mock_job.id = uuid4()
        mock_job.user_id = test_user.id
        mock_job.video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        mock_job.language = "fr"
        mock_job.source_type = "youtube"
        mock_job.original_filename = None
        mock_job.status = "pending"
        mock_job.text = None
        mock_job.confidence = None
        mock_job.duration_seconds = None
        mock_job.error = None
        mock_job.retry_count = 0
        mock_job.speaker_count = None
        mock_job.sentiment_score = None
        mock_job.created_at = datetime.now(UTC)
        mock_job.updated_at = datetime.now(UTC)
        mock_job.completed_at = None

        mock_service = AsyncMock()
        mock_service.create_job = AsyncMock(return_value=mock_job)
        mock_service.process_transcription = AsyncMock()

        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[require_transcription_quota] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session
        app.dependency_overrides[get_transcription_service] = lambda: mock_service

        try:
            with (
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
                patch("app.modules.billing.service.BillingService.consume_quota", new_callable=AsyncMock),
                patch("app.modules.transcription.routes._celery_available", return_value=False),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.post(
                        "/api/transcription/",
                        json={
                            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                            "language": "fr",
                        },
                        headers=auth_headers,
                    )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 201
        body = resp.json()
        assert body["video_url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert body["language"] == "fr"
        assert body["status"] == "pending"

    async def test_create_endpoint_invalid_url(self, app, auth_headers, test_user):
        """Invalid URL returns 422 validation error."""
        import httpx
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.billing.middleware import require_transcription_quota

        mock_session = AsyncMock()
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[require_transcription_quota] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            with (
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.post(
                        "/api/transcription/",
                        json={
                            "video_url": "https://www.google.com",
                            "language": "auto",
                        },
                        headers=auth_headers,
                    )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 422


class TestTranscriptionRouteList:
    """Tests for GET /api/transcription/."""

    async def test_list_endpoint_paginated(self, app, auth_headers, test_user):
        """List endpoint returns paginated response with correct structure."""
        import httpx
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.transcription.service import TranscriptionService

        mock_session = AsyncMock()
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            with (
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
                patch.object(
                    TranscriptionService,
                    "list_user_jobs",
                    new_callable=AsyncMock,
                    return_value=([], 0),
                ),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.get(
                        "/api/transcription/?skip=0&limit=10",
                        headers=auth_headers,
                    )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "skip" in body
        assert "limit" in body
        assert "has_more" in body
        assert isinstance(body["items"], list)
        assert body["total"] == 0


class TestTranscriptionRouteGetAndDelete:
    """Tests for GET and DELETE /api/transcription/{id}."""

    async def test_get_endpoint_not_found(self, app, auth_headers, test_user):
        """GET with a non-existent ID returns 404."""
        import httpx
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.transcription.service import TranscriptionService

        mock_session = AsyncMock()
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            with (
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
                patch.object(
                    TranscriptionService,
                    "get_job",
                    new_callable=AsyncMock,
                    return_value=None,
                ),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.get(
                        f"/api/transcription/{uuid4()}",
                        headers=auth_headers,
                    )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 404

    async def test_get_endpoint_valid(self, app, auth_headers, test_user):
        """GET an existing transcription returns 200 with data."""
        import httpx
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.transcription.service import TranscriptionService

        mock_session = AsyncMock()
        job_id = uuid4()

        mock_job = MagicMock()
        mock_job.id = job_id
        mock_job.user_id = test_user.id
        mock_job.video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        mock_job.language = "auto"
        mock_job.source_type = "youtube"
        mock_job.original_filename = None
        mock_job.status = "pending"
        mock_job.text = None
        mock_job.confidence = None
        mock_job.duration_seconds = None
        mock_job.error = None
        mock_job.retry_count = 0
        mock_job.speaker_count = None
        mock_job.sentiment_score = None
        mock_job.created_at = datetime.now(UTC)
        mock_job.updated_at = datetime.now(UTC)
        mock_job.completed_at = None

        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            with (
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
                patch.object(
                    TranscriptionService,
                    "get_job",
                    new_callable=AsyncMock,
                    return_value=mock_job,
                ),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.get(
                        f"/api/transcription/{job_id}",
                        headers=auth_headers,
                    )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == str(job_id)

    async def test_delete_endpoint_valid(self, app, auth_headers, test_user):
        """DELETE an existing transcription returns 204."""
        import httpx
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.transcription.service import TranscriptionService

        mock_session = AsyncMock()
        job_id = uuid4()

        mock_job = MagicMock()
        mock_job.id = job_id
        mock_job.user_id = test_user.id

        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            with (
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
                patch.object(
                    TranscriptionService,
                    "get_job",
                    new_callable=AsyncMock,
                    return_value=mock_job,
                ),
                patch.object(
                    TranscriptionService,
                    "delete_job",
                    new_callable=AsyncMock,
                    return_value=True,
                ),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.delete(
                        f"/api/transcription/{job_id}",
                        headers=auth_headers,
                    )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 204

    async def test_delete_endpoint_not_found(self, app, auth_headers, test_user):
        """DELETE with a non-existent ID returns 404."""
        import httpx
        from app.auth import get_current_user
        from app.database import get_session
        from app.modules.transcription.service import TranscriptionService

        mock_session = AsyncMock()
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            with (
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
                patch.object(
                    TranscriptionService,
                    "get_job",
                    new_callable=AsyncMock,
                    return_value=None,
                ),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.delete(
                        f"/api/transcription/{uuid4()}",
                        headers=auth_headers,
                    )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 404
