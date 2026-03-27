"""
AI Workflows API routes - No-code automation workflow management and execution.
"""

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.ai_workflows.schemas import (
    RunRead,
    TriggerRequest,
    WorkflowCreate,
    WorkflowEdge,
    WorkflowNode,
    WorkflowRead,
    WorkflowTemplate,
    WorkflowUpdate,
)
from app.modules.ai_workflows.service import WorkflowService
from app.rate_limit import limiter

router = APIRouter()


def _workflow_to_read(workflow) -> WorkflowRead:
    """Convert a Workflow model to WorkflowRead schema."""
    nodes_data = json.loads(workflow.nodes_json) if workflow.nodes_json else []
    edges_data = json.loads(workflow.edges_json) if workflow.edges_json else []
    trigger_config = json.loads(workflow.trigger_config_json) if workflow.trigger_config_json else {}
    return WorkflowRead(
        id=workflow.id,
        user_id=workflow.user_id,
        name=workflow.name,
        description=workflow.description,
        trigger_type=workflow.trigger_type if isinstance(workflow.trigger_type, str) else workflow.trigger_type.value,
        trigger_config=trigger_config,
        nodes=[WorkflowNode(**n) for n in nodes_data],
        edges=[WorkflowEdge(**e) for e in edges_data],
        status=workflow.status.value if hasattr(workflow.status, "value") else workflow.status,
        is_template=workflow.is_template,
        template_category=workflow.template_category,
        run_count=workflow.run_count,
        last_run_at=workflow.last_run_at,
        schedule_cron=workflow.schedule_cron,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


def _run_to_read(run) -> RunRead:
    """Convert a WorkflowRun model to RunRead schema."""
    results_data = json.loads(run.results_json) if run.results_json else []
    return RunRead(
        id=run.id,
        workflow_id=run.workflow_id,
        user_id=run.user_id,
        status=run.status.value if hasattr(run.status, "value") else run.status,
        trigger_type=run.trigger_type,
        current_node=run.current_node,
        total_nodes=run.total_nodes,
        results=results_data,
        error=run.error,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_ms=run.duration_ms,
        created_at=run.created_at,
    )


@router.post("/", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_workflow(
    request: Request,
    body: WorkflowCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new AI workflow.

    Rate limit: 10 requests/minute
    """
    nodes_dicts = [n.model_dump() for n in body.nodes]
    edges_dicts = [e.model_dump() for e in body.edges]

    # Validate DAG before creating (networkx if available, basic otherwise)
    if nodes_dicts and edges_dicts:
        try:
            from app.modules.ai_workflows.dag_validator import validate_dag
            validation = validate_dag(nodes_dicts, edges_dicts)
            if not validation["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid workflow graph: {'; '.join(validation['errors'])}",
                )
        except HTTPException:
            raise
        except Exception:
            pass  # Validation is best-effort

    workflow = await WorkflowService.create_workflow(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        trigger_type=body.trigger_type,
        trigger_config=body.trigger_config,
        nodes=nodes_dicts,
        edges=edges_dicts,
        session=session,
        schedule_cron=body.schedule_cron,
    )
    return _workflow_to_read(workflow)


@router.get("/", response_model=list[WorkflowRead])
@limiter.limit("20/minute")
async def list_workflows(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List user's workflows.

    Rate limit: 20 requests/minute
    """
    workflows, _ = await WorkflowService.list_workflows(
        current_user.id, session, skip, limit
    )
    return [_workflow_to_read(w) for w in workflows]


@router.get("/templates", response_model=list[WorkflowTemplate])
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category: content, research, knowledge"),
):
    """
    List available workflow templates.
    """
    templates = WorkflowService.get_templates(category)
    return [
        WorkflowTemplate(
            id=t["id"],
            name=t["name"],
            description=t["description"],
            category=t["category"],
            trigger_type=t["trigger_type"],
            nodes=[WorkflowNode(**n) for n in t["nodes"]],
            edges=[WorkflowEdge(**e) for e in t["edges"]],
            icon=t.get("icon", "AutoFixHigh"),
        )
        for t in templates
    ]


@router.post("/from-template/{template_id}", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_from_template(
    request: Request,
    template_id: str,
    name: Optional[str] = Query(None),
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a workflow from a pre-built template.

    Rate limit: 10 requests/minute
    """
    workflow = await WorkflowService.create_from_template(
        template_id, current_user.id, name, session
    )
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found",
        )
    return _workflow_to_read(workflow)


@router.get("/{workflow_id}", response_model=WorkflowRead)
@limiter.limit("30/minute")
async def get_workflow(
    request: Request,
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a workflow by ID.

    Rate limit: 30 requests/minute
    """
    workflow = await WorkflowService.get_workflow(
        workflow_id, current_user.id, session
    )
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return _workflow_to_read(workflow)


@router.put("/{workflow_id}", response_model=WorkflowRead)
@limiter.limit("10/minute")
async def update_workflow(
    request: Request,
    workflow_id: UUID,
    body: WorkflowUpdate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a workflow.

    Rate limit: 10 requests/minute
    """
    updates = body.model_dump(exclude_unset=True)
    workflow = await WorkflowService.update_workflow(
        workflow_id, current_user.id, updates, session
    )
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return _workflow_to_read(workflow)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_workflow(
    request: Request,
    workflow_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a workflow and its run history.

    Rate limit: 10 requests/minute
    """
    deleted = await WorkflowService.delete_workflow(
        workflow_id, current_user.id, session
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return None


@router.post("/{workflow_id}/run", response_model=RunRead)
@limiter.limit("3/minute")
async def trigger_workflow(
    request: Request,
    workflow_id: UUID,
    body: TriggerRequest = TriggerRequest(),
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Trigger a workflow execution with optional input data.

    Rate limit: 3 requests/minute
    """
    run = await WorkflowService.execute_workflow(
        workflow_id, current_user.id, session,
        input_data=body.input_data,
    )
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return _run_to_read(run)


@router.post("/validate")
async def validate_workflow_graph(body: WorkflowCreate):
    """Validate a workflow DAG before saving (cycle detection, connectivity)."""
    from app.modules.ai_workflows.dag_validator import validate_dag
    nodes_dicts = [n.model_dump() for n in body.nodes]
    edges_dicts = [e.model_dump() for e in body.edges]
    return validate_dag(nodes_dicts, edges_dicts)


@router.get("/{workflow_id}/runs", response_model=list[RunRead])
@limiter.limit("20/minute")
async def list_runs(
    request: Request,
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List execution history for a workflow.

    Rate limit: 20 requests/minute
    """
    runs = await WorkflowService.list_runs(
        workflow_id, current_user.id, session
    )
    return [_run_to_read(r) for r in runs]


@router.get("/runs/{run_id}", response_model=RunRead)
@limiter.limit("30/minute")
async def get_run(
    request: Request,
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a workflow run by ID.

    Rate limit: 30 requests/minute
    """
    run = await WorkflowService.get_run(run_id, current_user.id, session)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )
    return _run_to_read(run)
