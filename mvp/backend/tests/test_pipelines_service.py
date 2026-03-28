"""
Tests for the pipelines module: CRUD, execution, step processing, and API routes.

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


class TestPipelineSchemas:
    """Test pipeline Pydantic schemas."""

    def test_pipeline_step_schema(self):
        from app.modules.pipelines.schemas import PipelineStep

        step = PipelineStep(
            id="step1",
            type="summarize",
            config={"max_length": 500},
            position=0,
        )
        assert step.id == "step1"
        assert step.type == "summarize"
        assert step.config["max_length"] == 500
        assert step.position == 0

    def test_pipeline_create_schema(self):
        from app.modules.pipelines.schemas import PipelineCreate, PipelineStep

        create = PipelineCreate(
            name="My Pipeline",
            description="A test pipeline",
            steps=[
                PipelineStep(id="s1", type="transcription", config={}, position=0),
                PipelineStep(id="s2", type="summarize", config={}, position=1),
            ],
            is_template=False,
        )
        assert create.name == "My Pipeline"
        assert len(create.steps) == 2
        assert create.is_template is False

    def test_pipeline_create_name_min_length(self):
        from pydantic import ValidationError
        from app.modules.pipelines.schemas import PipelineCreate

        with pytest.raises(ValidationError):
            PipelineCreate(name="", steps=[])

    def test_pipeline_update_schema(self):
        from app.modules.pipelines.schemas import PipelineUpdate

        update = PipelineUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.description is None
        assert update.steps is None

    def test_pipeline_read_schema(self):
        from app.modules.pipelines.schemas import PipelineRead, PipelineStep

        read = PipelineRead(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            description="Desc",
            steps=[PipelineStep(id="s1", type="summarize", config={}, position=0)],
            status="draft",
            is_template=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert read.name == "Test"
        assert read.status == "draft"
        assert len(read.steps) == 1

    def test_execution_read_schema(self):
        from app.modules.pipelines.schemas import ExecutionRead

        execution = ExecutionRead(
            id=uuid4(),
            pipeline_id=uuid4(),
            user_id=uuid4(),
            status="completed",
            current_step=3,
            total_steps=3,
            results=[{"type": "summarize", "output": "Summary text"}],
            error=None,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        assert execution.status == "completed"
        assert execution.current_step == 3
        assert len(execution.results) == 1


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestPipelineModels:
    """Test pipeline DB models."""

    def test_pipeline_creation(self):
        from app.models.pipeline import Pipeline, PipelineStatus

        pipeline = Pipeline(
            user_id=uuid4(),
            name="Test Pipeline",
            description="A test",
            steps_json=json.dumps([{"id": "s1", "type": "summarize", "config": {}, "position": 0}]),
            status=PipelineStatus.DRAFT,
        )
        assert pipeline.name == "Test Pipeline"
        assert pipeline.status == PipelineStatus.DRAFT
        assert pipeline.is_template is False

    def test_pipeline_status_enum(self):
        from app.models.pipeline import PipelineStatus

        assert PipelineStatus.DRAFT == "draft"
        assert PipelineStatus.ACTIVE == "active"
        assert PipelineStatus.ARCHIVED == "archived"

    def test_execution_status_enum(self):
        from app.models.pipeline import ExecutionStatus

        assert ExecutionStatus.PENDING == "pending"
        assert ExecutionStatus.RUNNING == "running"
        assert ExecutionStatus.COMPLETED == "completed"
        assert ExecutionStatus.FAILED == "failed"

    def test_pipeline_execution_creation(self):
        from app.models.pipeline import PipelineExecution, ExecutionStatus

        execution = PipelineExecution(
            pipeline_id=uuid4(),
            user_id=uuid4(),
            status=ExecutionStatus.RUNNING,
            current_step=1,
            total_steps=3,
        )
        assert execution.status == ExecutionStatus.RUNNING
        assert execution.current_step == 1
        assert execution.total_steps == 3
        assert execution.error is None


# ---------------------------------------------------------------------------
# Service-level tests (PipelineService)
# ---------------------------------------------------------------------------


class TestCreatePipeline:
    """Test PipelineService.create_pipeline."""

    @pytest.mark.asyncio
    async def test_create_pipeline(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        steps = [
            {"id": "s1", "type": "transcription", "config": {}, "position": 0},
            {"id": "s2", "type": "summarize", "config": {}, "position": 1},
        ]

        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        pipeline = await PipelineService.create_pipeline(
            user_id=user_id,
            name="YouTube to Summary",
            description="Transcribe and summarize",
            steps=steps,
            is_template=False,
            session=session,
        )

        assert pipeline is not None
        assert pipeline.name == "YouTube to Summary"
        assert pipeline.user_id == user_id
        parsed_steps = json.loads(pipeline.steps_json)
        assert len(parsed_steps) == 2
        session.add.assert_called()
        session.commit.assert_called()


class TestGetPipeline:
    """Test PipelineService.get_pipeline."""

    @pytest.mark.asyncio
    async def test_get_pipeline_owned(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        pipeline_id = uuid4()
        mock_pipeline = MagicMock()
        mock_pipeline.id = pipeline_id
        mock_pipeline.user_id = user_id

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_pipeline)

        result = await PipelineService.get_pipeline(pipeline_id, user_id, session)
        assert result is not None
        assert result.id == pipeline_id

    @pytest.mark.asyncio
    async def test_get_pipeline_wrong_user(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        other_user_id = uuid4()
        pipeline_id = uuid4()
        mock_pipeline = MagicMock()
        mock_pipeline.user_id = other_user_id

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_pipeline)

        result = await PipelineService.get_pipeline(pipeline_id, user_id, session)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_pipeline_not_found(self):
        from app.modules.pipelines.service import PipelineService

        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        result = await PipelineService.get_pipeline(uuid4(), uuid4(), session)
        assert result is None


class TestListPipelines:
    """Test PipelineService.list_pipelines."""

    @pytest.mark.asyncio
    async def test_list_pipelines_paginated(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        mock_p1 = MagicMock()
        mock_p1.name = "Pipeline 1"
        mock_p2 = MagicMock()
        mock_p2.name = "Pipeline 2"

        session = AsyncMock()
        # count query
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2
        # list query
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = [mock_p1, mock_p2]

        session.execute = AsyncMock(side_effect=[count_result, list_result])

        pipelines, total = await PipelineService.list_pipelines(
            user_id, session, skip=0, limit=20
        )
        assert total == 2
        assert len(pipelines) == 2

    @pytest.mark.asyncio
    async def test_list_pipelines_empty(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        session = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        list_result = MagicMock()
        list_result.scalars.return_value.all.return_value = []

        session.execute = AsyncMock(side_effect=[count_result, list_result])

        pipelines, total = await PipelineService.list_pipelines(
            user_id, session, skip=0, limit=20
        )
        assert total == 0
        assert pipelines == []


class TestDeletePipeline:
    """Test PipelineService.delete_pipeline."""

    @pytest.mark.asyncio
    async def test_delete_pipeline_success(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        pipeline_id = uuid4()
        mock_pipeline = MagicMock()
        mock_pipeline.user_id = user_id

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_pipeline)
        mock_exec_result = MagicMock()
        mock_exec_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_exec_result)
        session.delete = AsyncMock()
        session.commit = AsyncMock()

        result = await PipelineService.delete_pipeline(pipeline_id, user_id, session)
        assert result is True
        session.delete.assert_called_with(mock_pipeline)

    @pytest.mark.asyncio
    async def test_delete_pipeline_not_found(self):
        from app.modules.pipelines.service import PipelineService

        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        result = await PipelineService.delete_pipeline(uuid4(), uuid4(), session)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_pipeline_wrong_user(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        other_user_id = uuid4()
        mock_pipeline = MagicMock()
        mock_pipeline.user_id = other_user_id

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_pipeline)

        result = await PipelineService.delete_pipeline(uuid4(), user_id, session)
        assert result is False


# ---------------------------------------------------------------------------
# Step execution tests
# ---------------------------------------------------------------------------


class TestExecuteStepSummarize:
    """Test PipelineService._execute_step for summarize type."""

    @pytest.mark.asyncio
    async def test_execute_step_summarize(self):
        from app.modules.pipelines.service import PipelineService

        mock_ai_result = {
            "processed_text": "This is a summary.",
            "provider": "gemini",
        }

        with patch(
            "app.ai_assistant.service.AIAssistantService.process_text_with_provider",
            new_callable=AsyncMock,
            return_value=mock_ai_result,
        ):
            result = await PipelineService._execute_step(
                {"type": "summarize", "config": {}},
                previous_output="Long text to summarize...",
            )

        assert result["type"] == "summarize"
        assert result["output"] == "This is a summary."

    @pytest.mark.asyncio
    async def test_execute_step_summarize_no_input(self):
        from app.modules.pipelines.service import PipelineService

        result = await PipelineService._execute_step(
            {"type": "summarize", "config": {}},
            previous_output=None,
        )

        assert result["type"] == "summarize"
        assert "error" in result or result["output"] == ""


class TestExecuteStepTranslate:
    """Test PipelineService._execute_step for translate type."""

    @pytest.mark.asyncio
    async def test_execute_step_translate(self):
        from app.modules.pipelines.service import PipelineService

        mock_ai_result = {
            "processed_text": "Translated text in English.",
            "provider": "gemini",
        }

        with patch(
            "app.ai_assistant.service.AIAssistantService.process_text_with_provider",
            new_callable=AsyncMock,
            return_value=mock_ai_result,
        ):
            result = await PipelineService._execute_step(
                {"type": "translate", "config": {"target_language": "en"}},
                previous_output="Texte en francais.",
            )

        assert result["type"] == "translate"
        assert result["output"] == "Translated text in English."
        assert result["target_language"] == "en"


class TestExecuteStepTranscription:
    """Test PipelineService._execute_step for transcription type."""

    @pytest.mark.asyncio
    async def test_execute_step_transcription(self):
        from app.modules.pipelines.service import PipelineService

        result = await PipelineService._execute_step(
            {"type": "transcription", "config": {}},
            previous_output="transcribed text content",
        )

        assert result["type"] == "transcription"
        assert result["output"] == "transcribed text content"


class TestExecuteStepSentiment:
    """Test PipelineService._execute_step for sentiment type."""

    @pytest.mark.asyncio
    async def test_execute_step_analyze_sentiment(self):
        from app.modules.pipelines.service import PipelineService

        mock_sentiment_result = {
            "overall_sentiment": "positive",
            "overall_score": 0.85,
            "positive_percent": 80,
            "negative_percent": 5,
            "emotion_summary": {"joy": 0.7},
        }

        with patch(
            "app.modules.sentiment.service.SentimentService.analyze_text",
            new_callable=AsyncMock,
            return_value=mock_sentiment_result,
        ):
            result = await PipelineService._execute_step(
                {"type": "sentiment", "config": {}},
                previous_output="I love this product!",
            )

        assert result["type"] == "sentiment"
        assert "positive" in result["output"]
        assert "80" in result["output"]

    @pytest.mark.asyncio
    async def test_execute_step_sentiment_no_text(self):
        from app.modules.pipelines.service import PipelineService

        result = await PipelineService._execute_step(
            {"type": "sentiment", "config": {}},
            previous_output=None,
        )

        assert result["type"] == "sentiment"
        assert "No text" in result["output"]


class TestExecuteStepUnknown:
    """Test PipelineService._execute_step for unknown step type."""

    @pytest.mark.asyncio
    async def test_execute_step_unknown_type(self):
        from app.modules.pipelines.service import PipelineService

        result = await PipelineService._execute_step(
            {"type": "nonexistent_step", "config": {}},
            previous_output="some input",
        )

        assert result["type"] == "nonexistent_step"
        assert "Unknown step type" in result.get("note", "")


class TestExecuteStepExport:
    """Test PipelineService._execute_step for export type."""

    @pytest.mark.asyncio
    async def test_execute_step_export(self):
        from app.modules.pipelines.service import PipelineService

        result = await PipelineService._execute_step(
            {"type": "export", "config": {"format": "json"}},
            previous_output="Final output text",
        )

        assert result["type"] == "export"
        assert result["output"] == "Final output text"
        assert result["format"] == "json"


# ---------------------------------------------------------------------------
# Pipeline execution tests
# ---------------------------------------------------------------------------


class TestExecutePipeline:
    """Test PipelineService.execute_pipeline end-to-end."""

    @pytest.mark.asyncio
    async def test_execute_pipeline_success(self):
        from app.modules.pipelines.service import PipelineService
        from app.models.pipeline import ExecutionStatus

        user_id = uuid4()
        pipeline_id = uuid4()

        mock_pipeline = MagicMock()
        mock_pipeline.id = pipeline_id
        mock_pipeline.user_id = user_id
        mock_pipeline.steps_json = json.dumps([
            {"type": "transcription", "config": {}, "id": "s1", "position": 0},
            {"type": "summarize", "config": {}, "id": "s2", "position": 1},
        ])

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_pipeline)
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()

        mock_ai_result = {"processed_text": "Summary of content.", "provider": "gemini"}

        with patch(
            "app.ai_assistant.service.AIAssistantService.process_text_with_provider",
            new_callable=AsyncMock,
            return_value=mock_ai_result,
        ):
            execution = await PipelineService.execute_pipeline(
                pipeline_id, user_id, session
            )

        assert execution is not None
        assert execution.status == ExecutionStatus.COMPLETED
        assert execution.total_steps == 2

    @pytest.mark.asyncio
    async def test_execute_pipeline_not_found(self):
        from app.modules.pipelines.service import PipelineService

        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        result = await PipelineService.execute_pipeline(uuid4(), uuid4(), session)
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_pipeline_wrong_user(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        other_user_id = uuid4()
        mock_pipeline = MagicMock()
        mock_pipeline.user_id = other_user_id

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_pipeline)

        result = await PipelineService.execute_pipeline(uuid4(), user_id, session)
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_pipeline_step_failure_marks_failed(self):
        from app.modules.pipelines.service import PipelineService
        from app.models.pipeline import ExecutionStatus

        user_id = uuid4()
        pipeline_id = uuid4()

        mock_pipeline = MagicMock()
        mock_pipeline.id = pipeline_id
        mock_pipeline.user_id = user_id
        mock_pipeline.steps_json = json.dumps([
            {"type": "summarize", "config": {}, "id": "s1", "position": 0},
        ])

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_pipeline)
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()

        with patch.object(
            PipelineService,
            "_execute_step",
            new_callable=AsyncMock,
            side_effect=Exception("Step processing error"),
        ):
            execution = await PipelineService.execute_pipeline(
                pipeline_id, user_id, session
            )

        assert execution is not None
        assert execution.status == ExecutionStatus.FAILED
        assert "Step processing error" in execution.error

    @pytest.mark.asyncio
    async def test_execute_pipeline_step_output_chaining(self):
        """Verify that output from step N becomes input to step N+1."""
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        pipeline_id = uuid4()

        mock_pipeline = MagicMock()
        mock_pipeline.id = pipeline_id
        mock_pipeline.user_id = user_id
        mock_pipeline.steps_json = json.dumps([
            {"type": "transcription", "config": {}, "id": "s1", "position": 0},
            {"type": "summarize", "config": {}, "id": "s2", "position": 1},
            {"type": "translate", "config": {"target_language": "en"}, "id": "s3", "position": 2},
        ])

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_pipeline)
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()

        call_args_collector = []

        async def mock_execute_step(step, previous_output, pipeline=None, session=None):
            call_args_collector.append({"step_type": step["type"], "previous_output": previous_output})
            return {"type": step["type"], "output": f"output_of_{step['type']}"}

        with patch.object(PipelineService, "_execute_step", side_effect=mock_execute_step):
            await PipelineService.execute_pipeline(pipeline_id, user_id, session)

        # Step 1 (transcription): no previous output
        assert call_args_collector[0]["previous_output"] is None
        # Step 2 (summarize): gets output from step 1
        assert call_args_collector[1]["previous_output"] == "output_of_transcription"
        # Step 3 (translate): gets output from step 2
        assert call_args_collector[2]["previous_output"] == "output_of_summarize"


# ---------------------------------------------------------------------------
# Route-level tests (API endpoints via httpx)
# ---------------------------------------------------------------------------


class TestPipelineEndpointAuth:
    """Test that pipeline endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_create_requires_auth(self, client):
        resp = await client.post(
            "/api/pipelines/",
            json={
                "name": "Test",
                "steps": [{"id": "s1", "type": "summarize", "config": {}, "position": 0}],
            },
        )
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_requires_auth(self, client):
        resp = await client.get("/api/pipelines/")
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.get(f"/api/pipelines/{fake_id}")
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.delete(f"/api/pipelines/{fake_id}")
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_execute_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.post(f"/api/pipelines/{fake_id}/execute")
        assert resp.status_code == 401 or resp.status_code == 403


class TestPipelineNotFound:
    """Test 404 responses for missing pipelines."""

    @pytest.mark.asyncio
    async def test_get_pipeline_not_found(self, app, auth_headers, test_user):
        from app.auth import get_current_user
        from app.modules.auth_guards.middleware import require_verified_email
        from app.database import get_session

        mock_session = AsyncMock()
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[require_verified_email] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            import httpx

            fake_id = str(uuid4())
            with (
                patch(
                    "app.modules.pipelines.service.PipelineService.get_pipeline",
                    new_callable=AsyncMock,
                    return_value=None,
                ),
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.get(
                        f"/api/pipelines/{fake_id}",
                        headers=auth_headers,
                    )
                assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_pipeline_not_found(self, app, auth_headers, test_user):
        from app.auth import get_current_user
        from app.modules.auth_guards.middleware import require_verified_email
        from app.database import get_session

        mock_session = AsyncMock()
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[require_verified_email] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            import httpx

            fake_id = str(uuid4())
            with (
                patch(
                    "app.modules.pipelines.service.PipelineService.delete_pipeline",
                    new_callable=AsyncMock,
                    return_value=False,
                ),
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.delete(
                        f"/api/pipelines/{fake_id}",
                        headers=auth_headers,
                    )
                assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_execute_pipeline_not_found(self, app, auth_headers, test_user):
        from app.auth import get_current_user
        from app.modules.auth_guards.middleware import require_verified_email
        from app.database import get_session

        mock_session = AsyncMock()
        app.dependency_overrides[get_current_user] = lambda: test_user
        app.dependency_overrides[require_verified_email] = lambda: test_user
        app.dependency_overrides[get_session] = lambda: mock_session

        try:
            import httpx

            fake_id = str(uuid4())
            with (
                patch(
                    "app.modules.pipelines.service.PipelineService.execute_pipeline",
                    new_callable=AsyncMock,
                    return_value=None,
                ),
                patch("app.database.init_db", new_callable=AsyncMock),
                patch("app.database.engine") as mock_engine,
                patch("app.cache._get_redis", new_callable=AsyncMock, return_value=None),
            ):
                mock_engine.dispose = AsyncMock()
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                    resp = await ac.post(
                        f"/api/pipelines/{fake_id}/execute",
                        headers=auth_headers,
                    )
                assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()


class TestPipelineUpdateService:
    """Test PipelineService.update_pipeline."""

    @pytest.mark.asyncio
    async def test_update_pipeline_name(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        pipeline_id = uuid4()
        mock_pipeline = MagicMock()
        mock_pipeline.user_id = user_id
        mock_pipeline.name = "Old Name"

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_pipeline)
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()

        result = await PipelineService.update_pipeline(
            pipeline_id, user_id, {"name": "New Name"}, session
        )

        assert result is not None
        assert result.name == "New Name"

    @pytest.mark.asyncio
    async def test_update_pipeline_not_found(self):
        from app.modules.pipelines.service import PipelineService

        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        result = await PipelineService.update_pipeline(
            uuid4(), uuid4(), {"name": "X"}, session
        )
        assert result is None


class TestGetExecution:
    """Test PipelineService.get_execution."""

    @pytest.mark.asyncio
    async def test_get_execution_owned(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        exec_id = uuid4()
        mock_exec = MagicMock()
        mock_exec.user_id = user_id

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_exec)

        result = await PipelineService.get_execution(exec_id, user_id, session)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_execution_wrong_user(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        other_user_id = uuid4()
        mock_exec = MagicMock()
        mock_exec.user_id = other_user_id

        session = AsyncMock()
        session.get = AsyncMock(return_value=mock_exec)

        result = await PipelineService.get_execution(uuid4(), user_id, session)
        assert result is None


class TestListExecutions:
    """Test PipelineService.list_executions."""

    @pytest.mark.asyncio
    async def test_list_executions(self):
        from app.modules.pipelines.service import PipelineService

        user_id = uuid4()
        pipeline_id = uuid4()
        mock_exec = MagicMock()

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_exec]
        session.execute = AsyncMock(return_value=mock_result)

        executions = await PipelineService.list_executions(
            pipeline_id, user_id, session
        )
        assert len(executions) == 1
