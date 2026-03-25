"""
Tests for Sprint 4: Compare Multi-Model and Pipeline Builder.

All tests run without external services.
"""

import json
import os
import pytest
from datetime import UTC, datetime
from uuid import uuid4


class TestCompareModels:
    """Test ComparisonResult and ComparisonVote models."""

    def test_comparison_result_creation(self):
        from app.models.compare import ComparisonResult
        result = ComparisonResult(
            user_id=uuid4(),
            prompt="Test prompt",
            providers_used="gemini,claude",
            results_json='[{"provider": "gemini"}]',
        )
        assert result.prompt == "Test prompt"
        assert result.providers_used == "gemini,claude"

    def test_comparison_vote_creation(self):
        from app.models.compare import ComparisonVote
        vote = ComparisonVote(
            comparison_id=uuid4(),
            user_id=uuid4(),
            provider_name="gemini",
            quality_score=4,
        )
        assert vote.provider_name == "gemini"
        assert vote.quality_score == 4

    def test_comparison_vote_score_bounds(self):
        from app.models.compare import ComparisonVote
        vote = ComparisonVote(
            comparison_id=uuid4(),
            user_id=uuid4(),
            provider_name="claude",
            quality_score=5,
        )
        assert vote.quality_score == 5


class TestCompareSchemas:
    """Test Compare Pydantic schemas."""

    def test_compare_request_valid(self):
        from app.modules.compare.schemas import CompareRequest
        req = CompareRequest(
            prompt="Test prompt",
            providers=["gemini", "claude"],
        )
        assert req.prompt == "Test prompt"
        assert len(req.providers) == 2

    def test_compare_request_defaults(self):
        from app.modules.compare.schemas import CompareRequest
        req = CompareRequest(prompt="Test")
        assert "gemini" in req.providers
        assert "claude" in req.providers
        assert "groq" in req.providers

    def test_compare_request_empty_prompt_rejected(self):
        from app.modules.compare.schemas import CompareRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CompareRequest(prompt="", providers=["gemini"])

    def test_provider_result_schema(self):
        from app.modules.compare.schemas import ProviderResult
        result = ProviderResult(
            provider="gemini",
            model="gemini-2.5-flash",
            response="Test response",
            response_time_ms=1500,
            error=None,
        )
        assert result.provider == "gemini"
        assert result.response_time_ms == 1500

    def test_vote_request_schema(self):
        from app.modules.compare.schemas import VoteRequest
        vote = VoteRequest(provider_name="claude", quality_score=5)
        assert vote.quality_score == 5

    def test_vote_request_score_range(self):
        from app.modules.compare.schemas import VoteRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            VoteRequest(provider_name="claude", quality_score=6)
        with pytest.raises(ValidationError):
            VoteRequest(provider_name="claude", quality_score=0)

    def test_provider_stats_schema(self):
        from app.modules.compare.schemas import ProviderStats
        stats = ProviderStats(
            provider="gemini",
            total_votes=42,
            avg_score=3.8,
            win_count=15,
        )
        assert stats.avg_score == 3.8


class TestPipelineModels:
    """Test Pipeline and PipelineExecution models."""

    def test_pipeline_creation(self):
        from app.models.pipeline import Pipeline, PipelineStatus
        pipeline = Pipeline(
            user_id=uuid4(),
            name="Test Pipeline",
            description="A test pipeline",
            steps_json='[{"id": "s1", "type": "summarize"}]',
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

    def test_execution_creation(self):
        from app.models.pipeline import PipelineExecution, ExecutionStatus
        execution = PipelineExecution(
            pipeline_id=uuid4(),
            user_id=uuid4(),
            total_steps=3,
        )
        assert execution.current_step == 0
        assert execution.total_steps == 3
        assert execution.status == ExecutionStatus.PENDING

    def test_pipeline_steps_json_parsing(self):
        from app.models.pipeline import Pipeline
        steps = [{"id": "s1", "type": "transcription", "config": {}, "position": 0}]
        pipeline = Pipeline(
            user_id=uuid4(),
            name="JSON test",
            steps_json=json.dumps(steps),
        )
        parsed = json.loads(pipeline.steps_json)
        assert len(parsed) == 1
        assert parsed[0]["type"] == "transcription"


class TestPipelineSchemas:
    """Test Pipeline Pydantic schemas."""

    def test_pipeline_step_schema(self):
        from app.modules.pipelines.schemas import PipelineStep
        step = PipelineStep(
            id="step1",
            type="summarize",
            config={"max_length": 500},
            position=0,
        )
        assert step.type == "summarize"
        assert step.config["max_length"] == 500

    def test_pipeline_create_schema(self):
        from app.modules.pipelines.schemas import PipelineCreate, PipelineStep
        create = PipelineCreate(
            name="My Pipeline",
            steps=[
                PipelineStep(id="s1", type="transcription", config={}, position=0),
                PipelineStep(id="s2", type="summarize", config={}, position=1),
            ],
        )
        assert create.name == "My Pipeline"
        assert len(create.steps) == 2

    def test_pipeline_create_empty_name_rejected(self):
        from app.modules.pipelines.schemas import PipelineCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            PipelineCreate(name="", steps=[])

    def test_pipeline_update_schema(self):
        from app.modules.pipelines.schemas import PipelineUpdate
        update = PipelineUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.steps is None

    def test_pipeline_read_schema(self):
        from app.modules.pipelines.schemas import PipelineRead, PipelineStep
        read = PipelineRead(
            id=uuid4(),
            user_id=uuid4(),
            name="Test",
            description=None,
            steps=[],
            status="draft",
            is_template=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert read.status == "draft"

    def test_execution_read_schema(self):
        from app.modules.pipelines.schemas import ExecutionRead
        execution = ExecutionRead(
            id=uuid4(),
            pipeline_id=uuid4(),
            user_id=uuid4(),
            status="completed",
            current_step=3,
            total_steps=3,
            results=[{"type": "summarize", "output": "test"}],
            error=None,
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
        assert execution.current_step == 3
        assert len(execution.results) == 1


class TestModuleManifests:
    """Test that Sprint 4 module manifests are valid."""

    def test_compare_manifest(self):
        import json
        with open("app/modules/compare/manifest.json") as f:
            manifest = json.load(f)
        assert manifest["name"] == "compare"
        assert manifest["prefix"] == "/api/compare"
        assert manifest["enabled"] is True

    def test_pipelines_manifest(self):
        import json
        with open("app/modules/pipelines/manifest.json") as f:
            manifest = json.load(f)
        assert manifest["name"] == "pipelines"
        assert manifest["prefix"] == "/api/pipelines"
        assert manifest["enabled"] is True
