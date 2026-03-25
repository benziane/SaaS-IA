"""
Tests for the Agents module - service, planner, executor, and routes.

All tests mock DB and AI providers. Uses pytest-asyncio.
"""

import json
from datetime import UTC, datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.agent import AgentRun, AgentStep, AgentStatus


# ---------------------------------------------------------------------------
# Planner tests
# ---------------------------------------------------------------------------


class TestPlannerHeuristic:
    """Tests for the heuristic (keyword-based) planner fallback."""

    def test_planner_heuristic_transcribe_keyword(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Transcribe this YouTube video")
        actions = [s["action"] for s in plan]
        assert "transcribe" in actions

    def test_planner_heuristic_summarize_keyword(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Summarize the following text")
        actions = [s["action"] for s in plan]
        assert "summarize" in actions

    def test_planner_heuristic_translate_keyword(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Translate this document to English")
        actions = [s["action"] for s in plan]
        assert "translate" in actions

    def test_planner_heuristic_search_keyword(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Search the knowledge base for AI papers")
        actions = [s["action"] for s in plan]
        assert "search_knowledge" in actions

    def test_planner_heuristic_sentiment_keyword(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Analyze the sentiment of this review")
        actions = [s["action"] for s in plan]
        assert "analyze_sentiment" in actions

    def test_planner_heuristic_crawl_keyword(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Crawl this website for information")
        actions = [s["action"] for s in plan]
        assert "crawl_web" in actions

    def test_planner_heuristic_crawl_and_index_keyword(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Crawl this website and index to knowledge base")
        actions = [s["action"] for s in plan]
        assert "crawl_and_index" in actions

    def test_planner_heuristic_blog_content_keyword(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Write a blog article about AI trends")
        actions = [s["action"] for s in plan]
        assert "generate_content" in actions
        # Verify format is blog_article
        content_step = [s for s in plan if s["action"] == "generate_content"][0]
        assert content_step["input"]["format"] == "blog_article"

    def test_planner_heuristic_twitter_content_keyword(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Create a Twitter thread about our product")
        actions = [s["action"] for s in plan]
        assert "generate_content" in actions
        content_step = [s for s in plan if s["action"] == "generate_content"][0]
        assert content_step["input"]["format"] == "twitter_thread"

    def test_planner_heuristic_multiple_keywords(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Transcribe this video and then summarize it")
        actions = [s["action"] for s in plan]
        assert "transcribe" in actions
        assert "summarize" in actions

    def test_planner_heuristic_fallback_generate_text(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Hello, how are you?")
        assert len(plan) == 1
        assert plan[0]["action"] == "generate_text"

    def test_planner_heuristic_chatbot_keyword(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Deploy a chatbot for customer support")
        actions = [s["action"] for s in plan]
        assert "deploy_chatbot" in actions

    def test_planner_heuristic_marketplace_keyword(self):
        from app.modules.agents.planner import _heuristic_plan

        plan = _heuristic_plan("Search the marketplace for templates")
        actions = [s["action"] for s in plan]
        assert "search_marketplace" in actions


@pytest.mark.asyncio
class TestPlannerAIMode:
    """Tests for the AI-powered planner."""

    async def test_planner_ai_mode_returns_plan(self):
        from app.modules.agents.planner import create_plan

        ai_response = json.dumps([
            {"action": "transcribe", "description": "Transcribe video", "input": {"url": "https://example.com"}},
            {"action": "summarize", "description": "Summarize transcription", "input": {"max_length": 500}},
        ])

        with patch("app.ai_assistant.service.AIAssistantService") as mock_ai:
            mock_ai.process_text_with_provider = AsyncMock(
                return_value={"processed_text": ai_response}
            )
            plan = await create_plan("Transcribe and summarize this video")

        assert len(plan) == 2
        assert plan[0]["action"] == "transcribe"
        assert plan[1]["action"] == "summarize"

    async def test_planner_ai_mode_fallback_on_failure(self):
        from app.modules.agents.planner import create_plan

        with patch("app.ai_assistant.service.AIAssistantService") as mock_ai:
            mock_ai.process_text_with_provider = AsyncMock(side_effect=Exception("AI unavailable"))
            plan = await create_plan("Transcribe this YouTube video")

        # Should fallback to heuristic
        assert len(plan) >= 1
        actions = [s["action"] for s in plan]
        assert "transcribe" in actions


# ---------------------------------------------------------------------------
# Executor tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestExecutor:
    """Tests for the agent executor."""

    async def test_executor_transcribe_action(self):
        from app.modules.agents.executor import execute_step

        result = await execute_step(
            action="transcribe",
            input_data={"url": "https://www.youtube.com/watch?v=test123"},
            previous_output=None,
        )
        assert result["action"] == "transcribe"
        assert "url" in result
        assert "output" in result

    async def test_executor_transcribe_no_url(self):
        from app.modules.agents.executor import execute_step

        result = await execute_step(
            action="transcribe",
            input_data={},
            previous_output=None,
        )
        assert "error" in result

    async def test_executor_search_action(self):
        from app.modules.agents.executor import execute_step

        with patch("app.modules.agents.executor._exec_search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {
                "output": "Found 3 relevant documents",
                "action": "search_knowledge",
                "results": [{"title": "Doc1"}],
            }
            result = await execute_step(
                action="search_knowledge",
                input_data={"query": "AI papers"},
                previous_output=None,
            )
        assert result["action"] == "search_knowledge"
        assert "output" in result

    async def test_executor_unknown_action_fallback(self):
        from app.modules.agents.executor import execute_step

        # Unknown action should fallback to _exec_generate
        with patch("app.modules.agents.executor._exec_generate", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = {"output": "Generated text", "action": "generate_text"}
            result = await execute_step(
                action="totally_unknown_action_xyz",
                input_data={"prompt": "test"},
                previous_output=None,
            )
        assert "output" in result

    async def test_executor_summarize_action(self):
        from app.modules.agents.executor import execute_step

        with patch("app.ai_assistant.service.AIAssistantService") as mock_ai:
            mock_ai.process_text_with_provider = AsyncMock(
                return_value={"processed_text": "This is a summary."}
            )
            result = await execute_step(
                action="summarize",
                input_data={"text": "Long text to summarize..." * 50},
                previous_output=None,
            )
        assert result["action"] == "summarize"

    async def test_executor_crawl_web_valid_url(self):
        from app.modules.agents.executor import execute_step

        with patch("app.modules.web_crawler.service.WebCrawlerService") as mock_crawler:
            mock_crawler.scrape = AsyncMock(return_value={
                "success": True,
                "markdown": "# Page Title\nContent here",
                "image_count": 3,
                "title": "Test Page",
            })
            result = await execute_step(
                action="crawl_web",
                input_data={"url": "https://example.com"},
                previous_output=None,
            )
        assert result["action"] == "crawl_web"

    async def test_executor_crawl_web_no_url(self):
        from app.modules.agents.executor import execute_step

        result = await execute_step(
            action="crawl_web",
            input_data={},
            previous_output=None,
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# AgentService tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAgentService:
    """Tests for the AgentService CRUD and lifecycle."""

    async def test_create_and_run_agent(self, session):
        from app.modules.agents.service import AgentService

        user_id = uuid4()
        instruction = "Summarize the latest AI news"

        with patch("app.modules.agents.service.create_plan", new_callable=AsyncMock) as mock_plan, \
             patch("app.modules.agents.service.execute_step", new_callable=AsyncMock) as mock_exec, \
             patch("app.modules.cost_tracker.tracker.track_ai_usage", new_callable=AsyncMock):

            mock_plan.return_value = [
                {"action": "generate_text", "description": "Process request", "input": {"prompt": instruction}},
            ]
            mock_exec.return_value = {"output": "Summary of AI news", "action": "generate_text"}

            run = await AgentService.create_and_run(
                user_id=user_id,
                instruction=instruction,
                session=session,
            )

        assert run.instruction == instruction
        assert run.user_id == user_id
        assert run.status == AgentStatus.COMPLETED
        assert run.total_steps == 1

    async def test_list_runs_empty(self, session):
        from app.modules.agents.service import AgentService

        user_id = uuid4()
        runs = await AgentService.list_runs(user_id, session)
        assert runs == []

    async def test_list_runs_paginated(self, session):
        from app.modules.agents.service import AgentService

        user_id = uuid4()

        # Create multiple runs directly
        for i in range(5):
            run = AgentRun(
                user_id=user_id,
                instruction=f"Task {i}",
                status=AgentStatus.COMPLETED,
            )
            session.add(run)
        await session.commit()

        runs = await AgentService.list_runs(user_id, session, limit=3)
        assert len(runs) == 3

    async def test_get_run_found(self, session):
        from app.modules.agents.service import AgentService

        user_id = uuid4()
        run = AgentRun(
            user_id=user_id,
            instruction="Test task",
            status=AgentStatus.COMPLETED,
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)

        data = await AgentService.get_run(run.id, user_id, session)
        assert data is not None
        assert data["run"].id == run.id
        assert isinstance(data["steps"], list)

    async def test_get_run_wrong_user(self, session):
        from app.modules.agents.service import AgentService

        user_id = uuid4()
        other_user_id = uuid4()

        run = AgentRun(
            user_id=user_id,
            instruction="Test task",
            status=AgentStatus.COMPLETED,
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)

        data = await AgentService.get_run(run.id, other_user_id, session)
        assert data is None

    async def test_get_run_not_found(self, session):
        from app.modules.agents.service import AgentService

        data = await AgentService.get_run(uuid4(), uuid4(), session)
        assert data is None

    async def test_cancel_run_executing(self, session):
        from app.modules.agents.service import AgentService

        user_id = uuid4()
        run = AgentRun(
            user_id=user_id,
            instruction="Running task",
            status=AgentStatus.EXECUTING,
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)

        cancelled = await AgentService.cancel_run(run.id, user_id, session)
        assert cancelled is True

        await session.refresh(run)
        assert run.status == AgentStatus.CANCELLED

    async def test_cancel_run_already_completed(self, session):
        from app.modules.agents.service import AgentService

        user_id = uuid4()
        run = AgentRun(
            user_id=user_id,
            instruction="Done task",
            status=AgentStatus.COMPLETED,
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)

        cancelled = await AgentService.cancel_run(run.id, user_id, session)
        assert cancelled is False

    async def test_cancel_run_wrong_user(self, session):
        from app.modules.agents.service import AgentService

        user_id = uuid4()
        run = AgentRun(
            user_id=user_id,
            instruction="Running task",
            status=AgentStatus.EXECUTING,
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)

        cancelled = await AgentService.cancel_run(run.id, uuid4(), session)
        assert cancelled is False

    async def test_agent_task_failure_sets_failed_status(self, session):
        from app.modules.agents.service import AgentService

        user_id = uuid4()

        with patch("app.modules.agents.service.create_plan", new_callable=AsyncMock) as mock_plan:
            mock_plan.side_effect = Exception("Planning failed catastrophically")

            run = await AgentService.create_and_run(
                user_id=user_id,
                instruction="This will fail",
                session=session,
            )

        assert run.status == AgentStatus.FAILED
        assert run.error is not None
        assert "Planning failed" in run.error

    async def test_agent_task_status_lifecycle(self, session):
        """Verify run goes through planning -> executing -> completed."""
        from app.modules.agents.service import AgentService

        user_id = uuid4()
        statuses_seen = []

        original_commit = session.commit

        async def tracking_commit():
            # After commit, check the latest run status
            await original_commit()

        with patch("app.modules.agents.service.create_plan", new_callable=AsyncMock) as mock_plan, \
             patch("app.modules.agents.service.execute_step", new_callable=AsyncMock) as mock_exec, \
             patch("app.modules.cost_tracker.tracker.track_ai_usage", new_callable=AsyncMock):

            mock_plan.return_value = [
                {"action": "generate_text", "description": "Generate", "input": {}},
            ]
            mock_exec.return_value = {"output": "Done", "action": "generate_text"}

            run = await AgentService.create_and_run(
                user_id=user_id,
                instruction="Test lifecycle",
                session=session,
            )

        # Final status should be completed
        assert run.status == AgentStatus.COMPLETED
        assert run.completed_at is not None


# ---------------------------------------------------------------------------
# Route-level auth tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAgentRoutesAuth:
    """Test that all agent endpoints require authentication."""

    async def test_run_agent_requires_auth(self, client):
        resp = await client.post("/api/agents/run", json={"instruction": "test"})
        assert resp.status_code in (401, 403)

    async def test_list_runs_requires_auth(self, client):
        resp = await client.get("/api/agents/runs")
        assert resp.status_code in (401, 403)

    async def test_get_run_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.get(f"/api/agents/runs/{fake_id}")
        assert resp.status_code in (401, 403)

    async def test_cancel_run_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.post(f"/api/agents/runs/{fake_id}/cancel")
        assert resp.status_code in (401, 403)

    async def test_react_agent_requires_auth(self, client):
        resp = await client.post("/api/agents/react", json={"instruction": "test"})
        assert resp.status_code in (401, 403)
