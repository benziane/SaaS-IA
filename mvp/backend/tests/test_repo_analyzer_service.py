"""Tests for the repo_analyzer module — London School TDD (mock-first).

The RepoAnalysis SQLModel has a 'sa_type_kwargs' field that is not compatible
with the SQLModel version in this environment. We therefore mock the model import
and test the pure-logic static methods by extracting them from the service
module after patching the broken model.

Covers:
- URL validation (SSRF prevention, allowed hosts)
- URL normalization (short-form, .git suffix)
- Repo name extraction
- create_analysis DB persistence (mocked session)
- run_analysis error path (missing record)
- Service instantiation (mock_mode detection)
"""

import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4


# ---------------------------------------------------------------------------
# Helpers: patch the broken model before importing the service
# ---------------------------------------------------------------------------

def _import_service():
    """Import RepoAnalyzerService with the broken SQLModel class patched out."""
    from enum import Enum

    class _FakeAnalysisStatus(str, Enum):
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"

    # Minimal fake RepoAnalysis that won't crash on instantiation
    class _FakeRepoAnalysis:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    fake_model_module = MagicMock()
    fake_model_module.RepoAnalysis = _FakeRepoAnalysis
    fake_model_module.AnalysisStatus = _FakeAnalysisStatus

    # Remove cached module if already imported
    for key in list(sys.modules.keys()):
        if "repo_analyzer" in key:
            del sys.modules[key]

    with patch.dict(sys.modules, {"app.models.repo_analyzer": fake_model_module}):
        from app.modules.repo_analyzer import service as svc
        return svc, _FakeAnalysisStatus, _FakeRepoAnalysis


# ---------------------------------------------------------------------------
# URL validation (SSRF prevention)
# ---------------------------------------------------------------------------

class TestValidateRepoUrl:
    """_validate_repo_url must block non-HTTPS and disallowed hosts."""

    @pytest.fixture(autouse=True)
    def patch_model(self):
        self.svc, self.Status, self.Model = _import_service()

    def test_valid_github_url_passes(self):
        # Should not raise
        self.svc.RepoAnalyzerService._validate_repo_url("https://github.com/owner/repo")

    def test_valid_gitlab_url_passes(self):
        self.svc.RepoAnalyzerService._validate_repo_url("https://gitlab.com/owner/repo")

    def test_valid_bitbucket_url_passes(self):
        self.svc.RepoAnalyzerService._validate_repo_url("https://bitbucket.org/owner/repo")

    def test_http_scheme_raises(self):
        """Non-HTTPS URLs are rejected (SSRF / downgrade risk)."""
        with pytest.raises(ValueError, match="Only HTTPS"):
            self.svc.RepoAnalyzerService._validate_repo_url("http://github.com/owner/repo")

    def test_ftp_scheme_raises(self):
        with pytest.raises(ValueError, match="Only HTTPS"):
            self.svc.RepoAnalyzerService._validate_repo_url("ftp://github.com/owner/repo")

    def test_disallowed_host_raises(self):
        """Arbitrary HTTPS hosts are rejected to prevent SSRF."""
        with pytest.raises(ValueError, match="not allowed"):
            self.svc.RepoAnalyzerService._validate_repo_url("https://evil.com/owner/repo")

    def test_internal_ip_raises(self):
        """Internal IPs must not pass through."""
        with pytest.raises(ValueError, match="not allowed"):
            self.svc.RepoAnalyzerService._validate_repo_url("https://192.168.1.1/owner/repo")

    def test_localhost_raises(self):
        with pytest.raises(ValueError, match="not allowed"):
            self.svc.RepoAnalyzerService._validate_repo_url("https://localhost/owner/repo")


# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

class TestNormalizeRepoUrl:
    """_normalize_repo_url converts various formats to a clonable HTTPS .git URL."""

    @pytest.fixture(autouse=True)
    def patch_model(self):
        self.svc, self.Status, self.Model = _import_service()

    def test_full_https_github_without_git_suffix(self):
        result = self.svc.RepoAnalyzerService._normalize_repo_url("https://github.com/owner/repo")
        assert result == "https://github.com/owner/repo.git"

    def test_full_https_github_already_has_git_suffix(self):
        result = self.svc.RepoAnalyzerService._normalize_repo_url("https://github.com/owner/repo.git")
        assert result == "https://github.com/owner/repo.git"

    def test_short_form_owner_repo_converted(self):
        result = self.svc.RepoAnalyzerService._normalize_repo_url("owner/repo")
        assert result == "https://github.com/owner/repo.git"

    def test_invalid_short_form_raises(self):
        """Short form without slash is rejected."""
        with pytest.raises(ValueError, match="owner/repo"):
            self.svc.RepoAnalyzerService._normalize_repo_url("justareponame")


# ---------------------------------------------------------------------------
# Repo name extraction
# ---------------------------------------------------------------------------

class TestExtractRepoName:
    """_extract_repo_name parses owner/repo from various URL forms."""

    @pytest.fixture(autouse=True)
    def patch_model(self):
        self.svc, self.Status, self.Model = _import_service()

    def test_full_url_extracts_owner_repo(self):
        result = self.svc.RepoAnalyzerService._extract_repo_name("https://github.com/myorg/myrepo")
        assert result == "myorg/myrepo"

    def test_full_url_with_git_suffix_strips_suffix(self):
        result = self.svc.RepoAnalyzerService._extract_repo_name("https://github.com/myorg/myrepo.git")
        assert result == "myorg/myrepo"

    def test_short_form_returned_as_is(self):
        result = self.svc.RepoAnalyzerService._extract_repo_name("myorg/myrepo")
        assert result == "myorg/myrepo"

    def test_trailing_slash_stripped(self):
        result = self.svc.RepoAnalyzerService._extract_repo_name("https://github.com/myorg/myrepo/")
        assert result == "myorg/myrepo"


# ---------------------------------------------------------------------------
# create_analysis — DB persistence
# ---------------------------------------------------------------------------

class TestCreateAnalysis:
    """create_analysis persists a RepoAnalysis row in the database."""

    @pytest.fixture(autouse=True)
    def patch_model(self):
        self.svc, self.Status, self.Model = _import_service()

    @pytest.mark.asyncio
    async def test_create_analysis_persists_record(self):
        """Should add a RepoAnalysis to the session and commit."""
        user_id = uuid4()

        data = MagicMock()
        data.repo_url = "https://github.com/owner/myrepo"
        data.analysis_types = ["structure", "dependencies"]
        data.depth = "standard"

        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()

        async def set_id(obj):
            obj.id = uuid4()

        session.refresh = AsyncMock(side_effect=set_id)

        result = await self.svc.RepoAnalyzerService.create_analysis(user_id, data, session)

        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once()
        assert result.status == self.Status.PENDING
        assert result.repo_url == "https://github.com/owner/myrepo"
        assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_create_analysis_repo_name_extracted(self):
        """repo_name field should contain 'owner/repo' format."""
        user_id = uuid4()
        data = MagicMock()
        data.repo_url = "https://github.com/acme/awesome-lib"
        data.analysis_types = ["security"]
        data.depth = "shallow"

        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        async def set_id_2(obj):
            obj.id = uuid4()
        session.refresh = AsyncMock(side_effect=set_id_2)

        result = await self.svc.RepoAnalyzerService.create_analysis(user_id, data, session)

        assert result.repo_name == "acme/awesome-lib"


# ---------------------------------------------------------------------------
# run_analysis — error path (missing record)
# ---------------------------------------------------------------------------

class TestRunAnalysisErrorPath:
    """run_analysis should handle missing analysis records gracefully."""

    @pytest.mark.asyncio
    async def test_run_analysis_missing_record_logs_error(self):
        """If the RepoAnalysis record is not found, run_analysis returns without crashing."""
        svc, Status, Model = _import_service()

        analysis_id = uuid4()

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=None)

        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        service = svc.RepoAnalyzerService.__new__(svc.RepoAnalyzerService)
        service.mock_mode = True

        with patch.object(svc, "get_session_context", return_value=mock_ctx):
            await service.run_analysis(analysis_id)

        mock_session.get.assert_awaited_once()


# ---------------------------------------------------------------------------
# Service instantiation — mock_mode detection
# ---------------------------------------------------------------------------

class TestRepoAnalyzerServiceInit:
    """Verify mock_mode detection based on git availability."""

    def test_mock_mode_when_git_unavailable(self):
        """When HAS_GIT is False, the service runs in mock mode."""
        svc, _, _ = _import_service()
        with patch.object(svc, "HAS_GIT", False):
            service = svc.RepoAnalyzerService()
            assert service.mock_mode is True

    def test_git_mode_when_git_available(self):
        """When HAS_GIT is True, mock_mode is False."""
        svc, _, _ = _import_service()
        with patch.object(svc, "HAS_GIT", True):
            service = svc.RepoAnalyzerService()
            assert service.mock_mode is False
