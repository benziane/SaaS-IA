"""
Pipeline API routes - CRUD pipelines and execution management.
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
from app.modules.pipelines.schemas import (
    ExecutionRead,
    PipelineCreate,
    PipelineRead,
    PipelineStep,
    PipelineUpdate,
)
from app.modules.pipelines.service import PipelineService
from app.rate_limit import limiter

router = APIRouter()


def _pipeline_to_read(pipeline) -> PipelineRead:
    """Convert a Pipeline model to PipelineRead schema."""
    steps_data = json.loads(pipeline.steps_json) if pipeline.steps_json else []
    return PipelineRead(
        id=pipeline.id,
        user_id=pipeline.user_id,
        name=pipeline.name,
        description=pipeline.description,
        steps=[PipelineStep(**s) for s in steps_data],
        status=pipeline.status.value if hasattr(pipeline.status, 'value') else pipeline.status,
        is_template=pipeline.is_template,
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
    )


def _execution_to_read(execution) -> ExecutionRead:
    """Convert a PipelineExecution model to ExecutionRead schema."""
    results_data = json.loads(execution.results_json) if execution.results_json else []
    return ExecutionRead(
        id=execution.id,
        pipeline_id=execution.pipeline_id,
        user_id=execution.user_id,
        status=execution.status.value if hasattr(execution.status, 'value') else execution.status,
        current_step=execution.current_step,
        total_steps=execution.total_steps,
        results=results_data,
        error=execution.error,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        created_at=execution.created_at,
    )


@router.post("/", response_model=PipelineRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_pipeline(
    request: Request,
    body: PipelineCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new AI pipeline.

    Rate limit: 10 requests/minute
    """
    steps_dicts = [s.model_dump() for s in body.steps]
    pipeline = await PipelineService.create_pipeline(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        steps=steps_dicts,
        is_template=body.is_template,
        session=session,
    )
    return _pipeline_to_read(pipeline)


@router.get("/", response_model=list[PipelineRead])
@limiter.limit("20/minute")
async def list_pipelines(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List user's pipelines.

    Rate limit: 20 requests/minute
    """
    pipelines, _ = await PipelineService.list_pipelines(
        user_id=current_user.id,
        session=session,
        skip=skip,
        limit=limit,
    )
    return [_pipeline_to_read(p) for p in pipelines]


@router.get("/{pipeline_id}", response_model=PipelineRead)
@limiter.limit("30/minute")
async def get_pipeline(
    request: Request,
    pipeline_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a pipeline by ID.

    Rate limit: 30 requests/minute
    """
    pipeline = await PipelineService.get_pipeline(
        pipeline_id, current_user.id, session
    )
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )
    return _pipeline_to_read(pipeline)


@router.put("/{pipeline_id}", response_model=PipelineRead)
@limiter.limit("10/minute")
async def update_pipeline(
    request: Request,
    pipeline_id: UUID,
    body: PipelineUpdate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a pipeline.

    Rate limit: 10 requests/minute
    """
    updates = body.model_dump(exclude_unset=True)
    pipeline = await PipelineService.update_pipeline(
        pipeline_id, current_user.id, updates, session
    )
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )
    return _pipeline_to_read(pipeline)


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_pipeline(
    request: Request,
    pipeline_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a pipeline and its executions.

    Rate limit: 10 requests/minute
    """
    deleted = await PipelineService.delete_pipeline(
        pipeline_id, current_user.id, session
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )
    return None


@router.post("/{pipeline_id}/execute", response_model=ExecutionRead)
@limiter.limit("3/minute")
async def execute_pipeline(
    request: Request,
    pipeline_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Execute a pipeline.

    Processes all steps sequentially, passing output from one step as input to the next.

    Rate limit: 3 requests/minute
    """
    execution = await PipelineService.execute_pipeline(
        pipeline_id, current_user.id, session
    )
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pipeline not found",
        )
    return _execution_to_read(execution)


@router.get("/{pipeline_id}/executions", response_model=list[ExecutionRead])
@limiter.limit("20/minute")
async def list_executions(
    request: Request,
    pipeline_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List executions for a pipeline.

    Rate limit: 20 requests/minute
    """
    executions = await PipelineService.list_executions(
        pipeline_id, current_user.id, session
    )
    return [_execution_to_read(e) for e in executions]


@router.get("/executions/{execution_id}", response_model=ExecutionRead)
@limiter.limit("30/minute")
async def get_execution(
    request: Request,
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a pipeline execution by ID.

    Rate limit: 30 requests/minute
    """
    execution = await PipelineService.get_execution(
        execution_id, current_user.id, session
    )
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )
    return _execution_to_read(execution)
