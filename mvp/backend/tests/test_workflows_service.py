"""
Tests for the AI Workflows module - service, DAG validation, templates, and routes.

All tests mock DB and AI providers. Uses pytest-asyncio.
"""

import json
from datetime import UTC, datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.workflow import Workflow, WorkflowRun, WorkflowStatus, RunStatus, TriggerType


# ---------------------------------------------------------------------------
# DAG Validator tests
# ---------------------------------------------------------------------------


class TestDagValidator:
    """Tests for the workflow DAG validator."""

    def test_validate_empty_workflow(self):
        from app.modules.ai_workflows.dag_validator import validate_dag

        result = validate_dag([], [])
        assert result["valid"] is True
        assert "Empty workflow" in result["warnings"]

    def test_validate_simple_chain(self):
        from app.modules.ai_workflows.dag_validator import validate_dag

        nodes = [
            {"id": "n1", "type": "action", "action": "transcribe"},
            {"id": "n2", "type": "action", "action": "summarize"},
            {"id": "n3", "type": "action", "action": "generate"},
        ]
        edges = [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
        ]
        result = validate_dag(nodes, edges)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_detects_cycle(self):
        from app.modules.ai_workflows.dag_validator import validate_dag

        nodes = [
            {"id": "n1", "type": "action", "action": "summarize"},
            {"id": "n2", "type": "action", "action": "translate"},
            {"id": "n3", "type": "action", "action": "generate"},
        ]
        edges = [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n1"},  # cycle!
        ]
        result = validate_dag(nodes, edges)
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_validate_invalid_edge_reference(self):
        from app.modules.ai_workflows.dag_validator import validate_dag

        nodes = [
            {"id": "n1", "type": "action", "action": "summarize"},
        ]
        edges = [
            {"id": "e1", "source": "n1", "target": "n99"},  # n99 does not exist
        ]
        result = validate_dag(nodes, edges)
        assert result["valid"] is False
        assert any("n99" in e for e in result["errors"])

    def test_validate_parallel_branches(self):
        from app.modules.ai_workflows.dag_validator import validate_dag

        nodes = [
            {"id": "n1", "type": "action", "action": "summarize"},
            {"id": "n2", "type": "action", "action": "translate"},
            {"id": "n3", "type": "action", "action": "sentiment"},
            {"id": "n4", "type": "action", "action": "generate"},
        ]
        edges = [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n1", "target": "n3"},
            {"id": "e3", "source": "n2", "target": "n4"},
            {"id": "e4", "source": "n3", "target": "n4"},
        ]
        result = validate_dag(nodes, edges)
        assert result["valid"] is True

    def test_get_execution_order(self):
        from app.modules.ai_workflows.dag_validator import get_execution_order

        nodes = [
            {"id": "n1", "type": "action", "action": "transcribe"},
            {"id": "n2", "type": "action", "action": "summarize"},
        ]
        edges = [
            {"id": "e1", "source": "n1", "target": "n2"},
        ]
        order = get_execution_order(nodes, edges)
        assert order.index("n1") < order.index("n2")


# ---------------------------------------------------------------------------
# Templates tests
# ---------------------------------------------------------------------------


class TestWorkflowTemplates:
    """Tests for the workflow templates feature."""

    def test_get_all_templates(self):
        from app.modules.ai_workflows.service import WorkflowService

        templates = WorkflowService.get_templates()
        assert len(templates) == 5
        ids = [t["id"] for t in templates]
        assert "youtube_to_blog" in ids
        assert "social_media_pack" in ids
        assert "competitive_intel" in ids
        assert "knowledge_enrichment" in ids
        assert "multilingual_content" in ids

    def test_get_templates_by_category_content(self):
        from app.modules.ai_workflows.service import WorkflowService

        templates = WorkflowService.get_templates("content")
        assert len(templates) >= 2
        for t in templates:
            assert t["category"] == "content"

    def test_get_templates_by_category_research(self):
        from app.modules.ai_workflows.service import WorkflowService

        templates = WorkflowService.get_templates("research")
        assert len(templates) >= 1
        for t in templates:
            assert t["category"] == "research"

    def test_get_templates_by_nonexistent_category(self):
        from app.modules.ai_workflows.service import WorkflowService

        templates = WorkflowService.get_templates("nonexistent_category")
        assert templates == []

    def test_template_structure(self):
        from app.modules.ai_workflows.service import WorkflowService

        templates = WorkflowService.get_templates()
        for t in templates:
            assert "id" in t
            assert "name" in t
            assert "description" in t
            assert "category" in t
            assert "trigger_type" in t
            assert "nodes" in t
            assert "edges" in t
            assert len(t["nodes"]) > 0


# ---------------------------------------------------------------------------
# WorkflowService CRUD tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestWorkflowService:
    """Tests for WorkflowService CRUD operations."""

    async def test_create_workflow(self, session):
        from app.modules.ai_workflows.service import WorkflowService

        user_id = uuid4()
        nodes = [
            {"id": "n1", "type": "action", "action": "summarize", "label": "Summarize", "config": {}},
        ]
        edges = []

        workflow = await WorkflowService.create_workflow(
            user_id=user_id,
            name="Test Workflow",
            description="A test workflow",
            trigger_type="manual",
            trigger_config={},
            nodes=nodes,
            edges=edges,
            session=session,
        )

        assert workflow.name == "Test Workflow"
        assert workflow.user_id == user_id
        assert workflow.status == WorkflowStatus.DRAFT
        parsed_nodes = json.loads(workflow.nodes_json)
        assert len(parsed_nodes) == 1

    async def test_list_workflows_paginated(self, session):
        from app.modules.ai_workflows.service import WorkflowService

        user_id = uuid4()
        for i in range(5):
            w = Workflow(
                user_id=user_id,
                name=f"Workflow {i}",
                trigger_type=TriggerType.MANUAL,
                nodes_json="[]",
                edges_json="[]",
                trigger_config_json="{}",
            )
            session.add(w)
        await session.commit()

        workflows, total = await WorkflowService.list_workflows(user_id, session, skip=0, limit=3)
        assert len(workflows) == 3
        assert total == 5

    async def test_get_workflow_found(self, session):
        from app.modules.ai_workflows.service import WorkflowService

        user_id = uuid4()
        w = Workflow(
            user_id=user_id,
            name="Get Me",
            trigger_type=TriggerType.MANUAL,
            nodes_json="[]",
            edges_json="[]",
            trigger_config_json="{}",
        )
        session.add(w)
        await session.commit()
        await session.refresh(w)

        result = await WorkflowService.get_workflow(w.id, user_id, session)
        assert result is not None
        assert result.name == "Get Me"

    async def test_get_workflow_wrong_user(self, session):
        from app.modules.ai_workflows.service import WorkflowService

        user_id = uuid4()
        w = Workflow(
            user_id=user_id,
            name="Private",
            trigger_type=TriggerType.MANUAL,
            nodes_json="[]",
            edges_json="[]",
            trigger_config_json="{}",
        )
        session.add(w)
        await session.commit()
        await session.refresh(w)

        result = await WorkflowService.get_workflow(w.id, uuid4(), session)
        assert result is None

    async def test_update_workflow(self, session):
        from app.modules.ai_workflows.service import WorkflowService

        user_id = uuid4()
        w = Workflow(
            user_id=user_id,
            name="Original",
            trigger_type=TriggerType.MANUAL,
            nodes_json="[]",
            edges_json="[]",
            trigger_config_json="{}",
        )
        session.add(w)
        await session.commit()
        await session.refresh(w)

        updated = await WorkflowService.update_workflow(
            w.id, user_id, {"name": "Updated Name"}, session
        )
        assert updated is not None
        assert updated.name == "Updated Name"

    async def test_delete_workflow(self, session):
        from app.modules.ai_workflows.service import WorkflowService

        user_id = uuid4()
        w = Workflow(
            user_id=user_id,
            name="To Delete",
            trigger_type=TriggerType.MANUAL,
            nodes_json="[]",
            edges_json="[]",
            trigger_config_json="{}",
        )
        session.add(w)
        await session.commit()
        await session.refresh(w)

        deleted = await WorkflowService.delete_workflow(w.id, user_id, session)
        assert deleted is True

        # Verify it's gone
        result = await WorkflowService.get_workflow(w.id, user_id, session)
        assert result is None

    async def test_create_from_template(self, session):
        from app.modules.ai_workflows.service import WorkflowService

        user_id = uuid4()
        workflow = await WorkflowService.create_from_template(
            "youtube_to_blog", user_id, None, session
        )
        assert workflow is not None
        assert workflow.name == "YouTube to Blog Post"
        nodes = json.loads(workflow.nodes_json)
        assert len(nodes) == 3
        assert workflow.template_category == "content"

    async def test_create_from_template_not_found(self, session):
        from app.modules.ai_workflows.service import WorkflowService

        user_id = uuid4()
        workflow = await WorkflowService.create_from_template(
            "nonexistent_template", user_id, None, session
        )
        assert workflow is None

    async def test_execute_workflow_simple(self, session):
        from app.modules.ai_workflows.service import WorkflowService

        user_id = uuid4()
        nodes = [
            {"id": "n1", "type": "action", "action": "summarize", "label": "Summarize", "config": {"max_length": 500}},
        ]
        edges = []

        w = Workflow(
            user_id=user_id,
            name="Exec Test",
            trigger_type=TriggerType.MANUAL,
            nodes_json=json.dumps(nodes),
            edges_json=json.dumps(edges),
            trigger_config_json="{}",
        )
        session.add(w)
        await session.commit()
        await session.refresh(w)

        with patch.object(
            WorkflowService, "_execute_node", new_callable=AsyncMock
        ) as mock_node:
            mock_node.return_value = {"output": "Summarized text", "action": "summarize"}

            run = await WorkflowService.execute_workflow(w.id, user_id, session)

        assert run is not None
        assert run.status == RunStatus.COMPLETED
        results = json.loads(run.results_json)
        assert len(results) == 1

    async def test_execute_workflow_not_found(self, session):
        from app.modules.ai_workflows.service import WorkflowService

        result = await WorkflowService.execute_workflow(uuid4(), uuid4(), session)
        assert result is None

    async def test_execute_workflow_node_failure(self, session):
        from app.modules.ai_workflows.service import WorkflowService

        user_id = uuid4()
        nodes = [
            {"id": "n1", "type": "action", "action": "summarize", "label": "Sum", "config": {}},
        ]
        w = Workflow(
            user_id=user_id,
            name="Fail Test",
            trigger_type=TriggerType.MANUAL,
            nodes_json=json.dumps(nodes),
            edges_json="[]",
            trigger_config_json="{}",
        )
        session.add(w)
        await session.commit()
        await session.refresh(w)

        with patch.object(
            WorkflowService, "_execute_node", new_callable=AsyncMock
        ) as mock_node:
            mock_node.side_effect = Exception("Node execution failed")

            run = await WorkflowService.execute_workflow(w.id, user_id, session)

        assert run is not None
        assert run.status == RunStatus.FAILED
        assert "Node execution failed" in run.error


# ---------------------------------------------------------------------------
# Route-level auth tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestWorkflowRoutesAuth:
    """Test that authenticated workflow endpoints require authentication."""

    async def test_create_workflow_requires_auth(self, client):
        resp = await client.post("/api/workflows/", json={"name": "test"})
        assert resp.status_code in (401, 403, 422)

    async def test_list_workflows_requires_auth(self, client):
        resp = await client.get("/api/workflows/")
        assert resp.status_code in (401, 403)

    async def test_get_workflow_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.get(f"/api/workflows/{fake_id}")
        assert resp.status_code in (401, 403)

    async def test_trigger_workflow_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.post(f"/api/workflows/{fake_id}/run")
        assert resp.status_code in (401, 403)
