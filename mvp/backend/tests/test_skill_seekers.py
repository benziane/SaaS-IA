"""
Tests for the Skill Seekers module.

Covers: model, schemas, service (mock mode), routes, and security validation.
All tests run WITHOUT external services.
"""

import json
import os
import pytest
from datetime import UTC, datetime
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestScrapeJobModel:
    """Test ScrapeJob SQLModel."""

    def test_model_creation_defaults(self):
        from app.models.skill_seekers import ScrapeJob, ScrapeJobStatus

        job = ScrapeJob(user_id=uuid4())
        assert job.status == ScrapeJobStatus.PENDING
        assert job.repos_json == "[]"
        assert job.targets_json == '["claude"]'
        assert job.enhance is False
        assert job.progress == 0
        assert job.current_step == "queued"
        assert job.error is None
        assert job.output_files_json is None

    def test_model_creation_custom(self):
        from app.models.skill_seekers import ScrapeJob, ScrapeJobStatus

        uid = uuid4()
        repos = json.dumps(["owner/repo1", "owner/repo2"])
        targets = json.dumps(["claude", "gemini"])
        job = ScrapeJob(
            user_id=uid,
            repos_json=repos,
            targets_json=targets,
            enhance=True,
        )
        assert job.user_id == uid
        assert json.loads(job.repos_json) == ["owner/repo1", "owner/repo2"]
        assert json.loads(job.targets_json) == ["claude", "gemini"]
        assert job.enhance is True

    def test_status_enum_values(self):
        from app.models.skill_seekers import ScrapeJobStatus

        assert ScrapeJobStatus.PENDING == "pending"
        assert ScrapeJobStatus.RUNNING == "running"
        assert ScrapeJobStatus.COMPLETED == "completed"
        assert ScrapeJobStatus.FAILED == "failed"

    def test_tablename(self):
        from app.models.skill_seekers import ScrapeJob

        assert ScrapeJob.__tablename__ == "scrape_jobs"


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestScrapeJobSchemas:
    """Test Pydantic schemas."""

    def test_create_schema_defaults(self):
        from app.modules.skill_seekers.schemas import ScrapeJobCreate

        data = ScrapeJobCreate(repos=["owner/repo"])
        assert data.repos == ["owner/repo"]
        assert data.targets == ["claude"]
        assert data.enhance is False

    def test_create_schema_custom(self):
        from app.modules.skill_seekers.schemas import ScrapeJobCreate

        data = ScrapeJobCreate(
            repos=["a/b", "c/d"],
            targets=["claude", "gemini"],
            enhance=True,
        )
        assert len(data.repos) == 2
        assert data.enhance is True

    def test_create_schema_empty_repos_rejected(self):
        from app.modules.skill_seekers.schemas import ScrapeJobCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ScrapeJobCreate(repos=[])

    def test_read_schema(self):
        from app.modules.skill_seekers.schemas import ScrapeJobRead

        uid = uuid4()
        now = datetime.now(UTC)
        data = ScrapeJobRead(
            id=uid,
            user_id=uid,
            repos=["owner/repo"],
            targets=["claude"],
            enhance=False,
            status="completed",
            progress=100,
            current_step="done",
            output_files=["file.md"],
            error=None,
            created_at=now,
            updated_at=now,
        )
        assert data.status == "completed"
        assert data.progress == 100

    def test_paginated_jobs_schema(self):
        from app.modules.skill_seekers.schemas import PaginatedJobs

        data = PaginatedJobs(
            items=[],
            total=0,
            skip=0,
            limit=20,
            has_more=False,
        )
        assert data.total == 0
        assert data.has_more is False

    def test_stats_schema(self):
        from app.modules.skill_seekers.schemas import ScrapeJobStats

        data = ScrapeJobStats(
            total_jobs=10,
            completed=7,
            failed=1,
            pending=1,
            running=1,
            total_repos_scraped=15,
            recent_jobs=[],
        )
        assert data.total_jobs == 10
        assert data.completed == 7


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------

class TestSkillSeekersService:
    """Test SkillSeekersService logic (no DB)."""

    def test_mock_mode_when_cli_absent(self):
        with patch("app.modules.skill_seekers.service.HAS_SKILL_SEEKERS", False):
            from app.modules.skill_seekers.service import SkillSeekersService
            service = SkillSeekersService()
            assert service.mock_mode is True

    def test_repo_validation_valid(self):
        from app.modules.skill_seekers.service import SkillSeekersService

        assert SkillSeekersService._validate_repo("owner/repo") is True
        assert SkillSeekersService._validate_repo("my-org/my.repo") is True
        assert SkillSeekersService._validate_repo("a_b/c-d.e") is True

    def test_repo_validation_invalid(self):
        from app.modules.skill_seekers.service import SkillSeekersService

        assert SkillSeekersService._validate_repo("") is False
        assert SkillSeekersService._validate_repo("noslash") is False
        assert SkillSeekersService._validate_repo("owner/repo; rm -rf /") is False
        assert SkillSeekersService._validate_repo("owner/repo && ls") is False
        assert SkillSeekersService._validate_repo("../../../etc/passwd") is False
        assert SkillSeekersService._validate_repo("owner/repo name") is False

    def test_repo_slug(self):
        from app.modules.skill_seekers.service import SkillSeekersService

        assert SkillSeekersService._repo_slug("owner/repo") == "owner_repo"
        assert SkillSeekersService._repo_slug("my.org/my.repo") == "my-org_my-repo"

    def test_is_installed(self):
        from app.modules.skill_seekers.service import SkillSeekersService

        # Should return a boolean (True or False depending on env)
        result = SkillSeekersService.is_installed()
        assert isinstance(result, bool)

    def test_job_to_read(self):
        from app.models.skill_seekers import ScrapeJob, ScrapeJobStatus
        from app.modules.skill_seekers.service import SkillSeekersService

        uid = uuid4()
        job = ScrapeJob(
            user_id=uid,
            repos_json=json.dumps(["owner/repo"]),
            targets_json=json.dumps(["claude"]),
            enhance=False,
            status=ScrapeJobStatus.COMPLETED,
            progress=100,
            current_step="done",
            output_files_json=json.dumps(["/tmp/owner_repo_claude.md"]),
        )
        result = SkillSeekersService.job_to_read(job)

        assert result["repos"] == ["owner/repo"]
        assert result["targets"] == ["claude"]
        assert result["status"] == "completed"
        assert result["progress"] == 100
        assert result["output_files"] == ["owner_repo_claude.md"]

    def test_job_to_read_empty_files(self):
        from app.models.skill_seekers import ScrapeJob, ScrapeJobStatus
        from app.modules.skill_seekers.service import SkillSeekersService

        job = ScrapeJob(
            user_id=uuid4(),
            status=ScrapeJobStatus.PENDING,
        )
        result = SkillSeekersService.job_to_read(job)
        assert result["output_files"] == []
        assert result["repos"] == []

    def test_get_output_file_not_found(self):
        from app.models.skill_seekers import ScrapeJob
        from app.modules.skill_seekers.service import SkillSeekersService

        job = ScrapeJob(user_id=uuid4(), output_files_json=None)
        result = SkillSeekersService.get_output_file(job, "nonexistent.md")
        assert result is None

    def test_get_output_file_with_files(self):
        from app.models.skill_seekers import ScrapeJob
        from app.modules.skill_seekers.service import SkillSeekersService
        import tempfile

        # Create a real temp file
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("test content")
            temp_path = f.name

        try:
            job = ScrapeJob(
                user_id=uuid4(),
                output_files_json=json.dumps([temp_path]),
            )
            filename = os.path.basename(temp_path)
            result = SkillSeekersService.get_output_file(job, filename)
            assert result == temp_path
        finally:
            os.unlink(temp_path)


# ---------------------------------------------------------------------------
# Service async tests (mock mode)
# ---------------------------------------------------------------------------

class TestSkillSeekersServiceAsync:
    """Test async service methods with mock DB."""

    @pytest.mark.asyncio
    async def test_create_job(self, session):
        from app.models.skill_seekers import ScrapeJob, ScrapeJobStatus
        from app.modules.skill_seekers.service import SkillSeekersService

        uid = uuid4()
        job = await SkillSeekersService.create_job(
            user_id=uid,
            repos=["owner/repo"],
            targets=["claude"],
            enhance=False,
            session=session,
        )
        assert job.id is not None
        assert job.user_id == uid
        assert job.status == ScrapeJobStatus.PENDING
        assert json.loads(job.repos_json) == ["owner/repo"]

    @pytest.mark.asyncio
    async def test_create_job_invalid_repo(self, session):
        from app.modules.skill_seekers.service import SkillSeekersService

        with pytest.raises(ValueError, match="Invalid repo name"):
            await SkillSeekersService.create_job(
                user_id=uuid4(),
                repos=["invalid; rm -rf /"],
                targets=["claude"],
                enhance=False,
                session=session,
            )

    @pytest.mark.asyncio
    async def test_get_jobs_empty(self, session):
        from app.modules.skill_seekers.service import SkillSeekersService

        jobs, total = await SkillSeekersService.get_jobs(
            user_id=uuid4(),
            session=session,
        )
        assert jobs == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_jobs_pagination(self, session):
        from app.modules.skill_seekers.service import SkillSeekersService

        uid = uuid4()
        # Create 3 jobs
        for i in range(3):
            await SkillSeekersService.create_job(
                user_id=uid,
                repos=[f"owner/repo{i}"],
                targets=["claude"],
                enhance=False,
                session=session,
            )

        # Get first 2
        jobs, total = await SkillSeekersService.get_jobs(
            user_id=uid, session=session, skip=0, limit=2,
        )
        assert len(jobs) == 2
        assert total == 3

        # Get last 1
        jobs, total = await SkillSeekersService.get_jobs(
            user_id=uid, session=session, skip=2, limit=2,
        )
        assert len(jobs) == 1
        assert total == 3

    @pytest.mark.asyncio
    async def test_get_job_ownership(self, session):
        from app.modules.skill_seekers.service import SkillSeekersService

        uid1 = uuid4()
        uid2 = uuid4()
        job = await SkillSeekersService.create_job(
            user_id=uid1,
            repos=["owner/repo"],
            targets=["claude"],
            enhance=False,
            session=session,
        )

        # Owner can access
        result = await SkillSeekersService.get_job(job.id, uid1, session)
        assert result is not None
        assert result.id == job.id

        # Non-owner cannot
        result = await SkillSeekersService.get_job(job.id, uid2, session)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_job(self, session):
        from app.modules.skill_seekers.service import SkillSeekersService

        uid = uuid4()
        job = await SkillSeekersService.create_job(
            user_id=uid,
            repos=["owner/repo"],
            targets=["claude"],
            enhance=False,
            session=session,
        )

        deleted = await SkillSeekersService.delete_job(job.id, uid, session)
        assert deleted is True

        # Should be gone
        result = await SkillSeekersService.get_job(job.id, uid, session)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_job_wrong_user(self, session):
        from app.modules.skill_seekers.service import SkillSeekersService

        uid = uuid4()
        job = await SkillSeekersService.create_job(
            user_id=uid,
            repos=["owner/repo"],
            targets=["claude"],
            enhance=False,
            session=session,
        )

        deleted = await SkillSeekersService.delete_job(job.id, uuid4(), session)
        assert deleted is False

    @pytest.mark.asyncio
    async def test_get_user_stats(self, session):
        from app.modules.skill_seekers.service import SkillSeekersService
        from app.models.skill_seekers import ScrapeJobStatus

        uid = uuid4()
        # Create jobs with different statuses
        job1 = await SkillSeekersService.create_job(
            user_id=uid, repos=["a/b"], targets=["claude"], enhance=False, session=session,
        )
        job1.status = ScrapeJobStatus.COMPLETED
        session.add(job1)

        job2 = await SkillSeekersService.create_job(
            user_id=uid, repos=["c/d", "e/f"], targets=["claude"], enhance=False, session=session,
        )
        job2.status = ScrapeJobStatus.FAILED
        session.add(job2)
        await session.commit()

        stats = await SkillSeekersService.get_user_stats(uid, session)
        assert stats["total_jobs"] == 2
        assert stats["completed"] == 1
        assert stats["failed"] == 1
        assert stats["total_repos_scraped"] == 1  # Only completed jobs count
        assert len(stats["recent_jobs"]) == 2


# ---------------------------------------------------------------------------
# Mock mode run_job test
# ---------------------------------------------------------------------------

class TestSkillSeekersRunMock:
    """Test the mock mode job execution."""

    @pytest.mark.asyncio
    async def test_run_mock_creates_files(self, session):
        from app.modules.skill_seekers.service import SkillSeekersService
        from app.models.skill_seekers import ScrapeJob, ScrapeJobStatus

        uid = uuid4()
        job = await SkillSeekersService.create_job(
            user_id=uid,
            repos=["owner/repo"],
            targets=["claude"],
            enhance=False,
            session=session,
        )

        service = SkillSeekersService()
        assert service.mock_mode is True  # CLI not installed in test env

        repos = json.loads(job.repos_json)
        targets = json.loads(job.targets_json)
        output_files = await service._run_mock(job, repos, targets, session)

        assert len(output_files) == 1
        assert output_files[0].endswith(".md")
        assert os.path.isfile(output_files[0])

        # Check content
        with open(output_files[0], "r") as f:
            content = f.read()
        assert "owner/repo" in content
        assert "MOCK MODE" in content

        # Cleanup
        import shutil
        parent = os.path.dirname(output_files[0])
        shutil.rmtree(parent, ignore_errors=True)


# ---------------------------------------------------------------------------
# Security validation tests
# ---------------------------------------------------------------------------

class TestSkillSeekersSecurityValidation:
    """Test that repo names are validated to prevent injection."""

    def test_command_injection_semicolon(self):
        from app.modules.skill_seekers.service import SkillSeekersService
        assert SkillSeekersService._validate_repo("owner/repo; cat /etc/passwd") is False

    def test_command_injection_pipe(self):
        from app.modules.skill_seekers.service import SkillSeekersService
        assert SkillSeekersService._validate_repo("owner/repo | ls") is False

    def test_command_injection_backtick(self):
        from app.modules.skill_seekers.service import SkillSeekersService
        assert SkillSeekersService._validate_repo("owner/`whoami`") is False

    def test_command_injection_dollar(self):
        from app.modules.skill_seekers.service import SkillSeekersService
        assert SkillSeekersService._validate_repo("owner/$(id)") is False

    def test_path_traversal(self):
        from app.modules.skill_seekers.service import SkillSeekersService
        assert SkillSeekersService._validate_repo("../../etc/passwd") is False
        assert SkillSeekersService._validate_repo("owner/../../../etc") is False

    def test_whitespace_injection(self):
        from app.modules.skill_seekers.service import SkillSeekersService
        assert SkillSeekersService._validate_repo("owner/repo name") is False
        assert SkillSeekersService._validate_repo("owner/repo\ttab") is False
        assert SkillSeekersService._validate_repo("owner/repo\nnewline") is False

    def test_valid_repos(self):
        from app.modules.skill_seekers.service import SkillSeekersService
        assert SkillSeekersService._validate_repo("anthropics/claude-code") is True
        assert SkillSeekersService._validate_repo("langchain-ai/langchain") is True
        assert SkillSeekersService._validate_repo("my.org/my_repo-v2.0") is True
