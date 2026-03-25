"""
Tests for the compare module: multi-provider comparison, voting, stats, and API routes.

All tests run without external services (no database, no Redis, no AI providers).
"""

import json
import os
import pytest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


class TestCompareSchemas:
    """Test compare Pydantic schemas."""

    def test_compare_request_default_providers(self):
        from app.modules.compare.schemas import CompareRequest

        req = CompareRequest(prompt="Explain AI")
        assert req.prompt == "Explain AI"
        assert req.providers == ["gemini", "claude", "groq"]

    def test_compare_request_custom_providers(self):
        from app.modules.compare.schemas import CompareRequest

        req = CompareRequest(prompt="Test", providers=["gemini", "claude"])
        assert len(req.providers) == 2

    def test_compare_request_prompt_min_length(self):
        from pydantic import ValidationError
        from app.modules.compare.schemas import CompareRequest

        with pytest.raises(ValidationError):
            CompareRequest(prompt="")

    def test_provider_result_schema(self):
        from app.modules.compare.schemas import ProviderResult

        result = ProviderResult(
            provider="gemini",
            model="gemini-2.0-flash",
            response="AI is artificial intelligence.",
            response_time_ms=150,
            error=None,
        )
        assert result.provider == "gemini"
        assert result.response_time_ms == 150
        assert result.error is None

    def test_provider_result_with_error(self):
        from app.modules.compare.schemas import ProviderResult

        result = ProviderResult(
            provider="claude",
            model="claude",
            response="",
            response_time_ms=5000,
            error="Timeout",
        )
        assert result.error == "Timeout"
        assert result.response == ""

    def test_vote_request_schema(self):
        from app.modules.compare.schemas import VoteRequest

        vote = VoteRequest(provider_name="gemini", quality_score=5)
        assert vote.provider_name == "gemini"
        assert vote.quality_score == 5

    def test_vote_request_score_range(self):
        from pydantic import ValidationError
        from app.modules.compare.schemas import VoteRequest

        with pytest.raises(ValidationError):
            VoteRequest(provider_name="gemini", quality_score=0)

        with pytest.raises(ValidationError):
            VoteRequest(provider_name="gemini", quality_score=6)

    def test_vote_response_schema(self):
        from app.modules.compare.schemas import VoteResponse

        resp = VoteResponse(
            id=uuid4(),
            comparison_id=uuid4(),
            provider_name="groq",
            quality_score=4,
        )
        assert resp.provider_name == "groq"
        assert resp.quality_score == 4

    def test_provider_stats_schema(self):
        from app.modules.compare.schemas import ProviderStats

        stats = ProviderStats(
            provider="gemini",
            total_votes=100,
            avg_score=4.2,
            win_count=45,
        )
        assert stats.total_votes == 100
        assert stats.avg_score == 4.2

    def test_compare_response_schema(self):
        from app.modules.compare.schemas import CompareResponse, ProviderResult

        resp = CompareResponse(
            id=uuid4(),
            prompt="Test prompt",
            results=[
                ProviderResult(
                    provider="gemini",
                    model="gemini-2.0-flash",
                    response="Response A",
                    response_time_ms=100,
                ),
                ProviderResult(
                    provider="claude",
                    model="claude-sonnet",
                    response="Response B",
                    response_time_ms=200,
                ),
            ],
            created_at=datetime.now(UTC),
        )
        assert len(resp.results) == 2


# ---------------------------------------------------------------------------
# Service-level tests (CompareService)
# ---------------------------------------------------------------------------


class TestCallProvider:
    """Test CompareService._call_provider."""

    @pytest.mark.asyncio
    async def test_call_provider_success(self):
        from app.modules.compare.service import CompareService

        mock_result = {
            "processed_text": "AI is a field of computer science.",
            "model": "gemini-2.0-flash",
            "provider": "gemini",
        }

        with patch(
            "app.ai_assistant.service.AIAssistantService.process_text_with_provider",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await CompareService._call_provider(
                "gemini", "What is AI?", user_id=uuid4()
            )

        assert result["provider"] == "gemini"
        assert result["response"] == "AI is a field of computer science."
        assert result["error"] is None
        assert result["response_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_call_provider_failure(self):
        from app.modules.compare.service import CompareService

        with patch(
            "app.ai_assistant.service.AIAssistantService.process_text_with_provider",
            new_callable=AsyncMock,
            side_effect=Exception("API timeout"),
        ):
            result = await CompareService._call_provider(
                "claude", "What is AI?", user_id=uuid4()
            )

        assert result["provider"] == "claude"
        assert result["response"] == ""
        assert result["error"] is not None
        assert "timeout" in result["error"].lower()


class TestRunComparison:
    """Test CompareService.run_comparison."""

    @pytest.mark.asyncio
    async def test_run_comparison_multi_provider(self):
        from app.modules.compare.service import CompareService

        user_id = uuid4()
        providers = ["gemini", "claude", "groq"]

        async def mock_call_provider(provider_name, prompt, user_id=None):
            return {
                "provider": provider_name,
                "model": f"{provider_name}-model",
                "response": f"Response from {provider_name}",
                "response_time_ms": 100,
                "error": None,
            }

        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        with (
            patch.object(
                CompareService,
                "_call_provider",
                side_effect=mock_call_provider,
            ),
            patch("app.modules.cost_tracker.tracker.track_ai_usage", new_callable=AsyncMock),
            patch("app.modules.compare.eval_engine.evaluate_responses", new_callable=AsyncMock, side_effect=Exception("skip")),
        ):
            comparison, results = await CompareService.run_comparison(
                user_id=user_id,
                prompt="What is AI?",
                providers=providers,
                session=session,
            )

        assert len(results) == 3
        assert all(r["error"] is None for r in results)
        provider_names = {r["provider"] for r in results}
        assert provider_names == {"gemini", "claude", "groq"}
        # Comparison record was persisted
        session.add.assert_called()
        session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_run_comparison_stores_results(self):
        from app.modules.compare.service import CompareService

        user_id = uuid4()
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        async def mock_call_provider(provider_name, prompt, user_id=None):
            return {
                "provider": provider_name,
                "model": provider_name,
                "response": f"Answer from {provider_name}",
                "response_time_ms": 50,
                "error": None,
            }

        with (
            patch.object(CompareService, "_call_provider", side_effect=mock_call_provider),
            patch("app.modules.cost_tracker.tracker.track_ai_usage", new_callable=AsyncMock),
            patch("app.modules.compare.eval_engine.evaluate_responses", new_callable=AsyncMock, side_effect=Exception("skip")),
        ):
            comparison, results = await CompareService.run_comparison(
                user_id=user_id,
                prompt="Test",
                providers=["gemini"],
                session=session,
            )

        assert comparison is not None
        assert comparison.prompt == "Test"
        assert comparison.user_id == user_id


class TestRecordVote:
    """Test CompareService.record_vote."""

    @pytest.mark.asyncio
    async def test_vote_on_result(self):
        from app.modules.compare.service import CompareService

        comparison_id = uuid4()
        user_id = uuid4()
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        vote = await CompareService.record_vote(
            comparison_id=comparison_id,
            user_id=user_id,
            provider_name="gemini",
            quality_score=5,
            session=session,
        )

        assert vote is not None
        assert vote.provider_name == "gemini"
        assert vote.quality_score == 5
        assert vote.comparison_id == comparison_id
        session.add.assert_called()
        session.commit.assert_called()


class TestGetStats:
    """Test CompareService.get_stats."""

    @pytest.mark.asyncio
    async def test_comparison_stats_returns_list(self):
        from app.modules.compare.service import CompareService

        mock_row = MagicMock()
        mock_row.provider_name = "gemini"
        mock_row.total_votes = 50
        mock_row.avg_score = 4.2

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        session.execute = AsyncMock(return_value=mock_result)

        stats = await CompareService.get_stats(session)
        assert len(stats) == 1
        assert stats[0]["provider"] == "gemini"
        assert stats[0]["total_votes"] == 50
        assert stats[0]["avg_score"] == 4.2

    @pytest.mark.asyncio
    async def test_comparison_stats_empty(self):
        from app.modules.compare.service import CompareService

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        stats = await CompareService.get_stats(session)
        assert stats == []


# ---------------------------------------------------------------------------
# Route-level tests (API endpoints via httpx)
# ---------------------------------------------------------------------------


class TestCompareEndpointAuth:
    """Test that compare endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_run_requires_auth(self, client):
        resp = await client.post(
            "/api/compare/run",
            json={"prompt": "test", "providers": ["gemini"]},
        )
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_vote_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.post(
            f"/api/compare/{fake_id}/vote",
            json={"provider_name": "gemini", "quality_score": 5},
        )
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_stats_requires_auth(self, client):
        resp = await client.get("/api/compare/stats")
        assert resp.status_code == 401 or resp.status_code == 403


class TestCompareNotFound:
    """Test 404 responses for missing comparisons."""

    @pytest.mark.asyncio
    async def test_vote_comparison_not_found(self, app, auth_headers, test_user):
        from app.auth import get_current_user
        from app.database import get_session

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=None)
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            import httpx

            fake_id = str(uuid4())
            with (
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.post(
                        f"/api/compare/{fake_id}/vote",
                        json={"provider_name": "gemini", "quality_score": 5},
                        headers=auth_headers,
                    )
                assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestCompareModels:
    """Test compare DB models."""

    def test_comparison_result_creation(self):
        from app.models.compare import ComparisonResult

        user_id = uuid4()
        comparison = ComparisonResult(
            user_id=user_id,
            prompt="Test prompt",
            providers_used="gemini,claude",
            results_json=json.dumps([{"provider": "gemini", "response": "test"}]),
        )
        assert comparison.user_id == user_id
        assert comparison.prompt == "Test prompt"
        assert "gemini" in comparison.providers_used

    def test_comparison_vote_creation(self):
        from app.models.compare import ComparisonVote

        vote = ComparisonVote(
            comparison_id=uuid4(),
            user_id=uuid4(),
            provider_name="claude",
            quality_score=4,
        )
        assert vote.provider_name == "claude"
        assert vote.quality_score == 4
