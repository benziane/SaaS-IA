"""
Agent API routes - Autonomous AI task execution.
"""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.agents.schemas import AgentRunRead, AgentRunRequest, AgentStepRead
from app.modules.agents.service import AgentService
from app.modules.billing.middleware import require_ai_call_quota
from app.modules.billing.service import BillingService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/run", response_model=AgentRunRead)
@limiter.limit("5/minute")
async def run_agent(
    request: Request,
    body: AgentRunRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Execute an autonomous AI agent.

    The agent decomposes the instruction into steps and executes them
    sequentially using platform capabilities.

    Rate limit: 5 requests/minute
    """
    run = await AgentService.create_and_run(
        user_id=current_user.id,
        instruction=body.instruction,
        session=session,
    )

    # Consume AI quota (1 per step executed)
    await BillingService.consume_quota(
        current_user.id, "ai_call", max(run.total_steps, 1), session
    )

    # Fetch steps for response
    data = await AgentService.get_run(run.id, current_user.id, session)
    steps = []
    if data:
        for s in data["steps"]:
            steps.append(AgentStepRead(
                id=s.id, step_index=s.step_index, action=s.action,
                description=s.description, status=s.status.value if hasattr(s.status, 'value') else s.status,
                error=s.error, output_json=s.output_json, started_at=s.started_at, completed_at=s.completed_at,
            ))

    return AgentRunRead(
        id=run.id, instruction=run.instruction,
        status=run.status.value if hasattr(run.status, 'value') else run.status,
        current_step=run.current_step, total_steps=run.total_steps,
        steps=steps, error=run.error,
        created_at=run.created_at, completed_at=run.completed_at,
    )


@router.get("/runs", response_model=list[AgentRunRead])
@limiter.limit("20/minute")
async def list_runs(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List agent runs for the current user."""
    runs = await AgentService.list_runs(current_user.id, session)
    result = []
    for run in runs:
        result.append(AgentRunRead(
            id=run.id, instruction=run.instruction,
            status=run.status.value if hasattr(run.status, 'value') else run.status,
            current_step=run.current_step, total_steps=run.total_steps,
            steps=[], error=run.error,
            created_at=run.created_at, completed_at=run.completed_at,
        ))
    return result


@router.get("/runs/{run_id}", response_model=AgentRunRead)
@limiter.limit("30/minute")
async def get_run(
    request: Request,
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get details of an agent run with all steps."""
    data = await AgentService.get_run(run_id, current_user.id, session)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")

    run = data["run"]
    steps = [
        AgentStepRead(
            id=s.id, step_index=s.step_index, action=s.action,
            description=s.description, status=s.status.value if hasattr(s.status, 'value') else s.status,
            error=s.error, output_json=s.output_json, started_at=s.started_at, completed_at=s.completed_at,
        )
        for s in data["steps"]
    ]

    return AgentRunRead(
        id=run.id, instruction=run.instruction,
        status=run.status.value if hasattr(run.status, 'value') else run.status,
        current_step=run.current_step, total_steps=run.total_steps,
        steps=steps, error=run.error,
        created_at=run.created_at, completed_at=run.completed_at,
    )


@router.post("/runs/{run_id}/cancel", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def cancel_run(
    request: Request,
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Cancel a running agent."""
    cancelled = await AgentService.cancel_run(run_id, current_user.id, session)
    if not cancelled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel this run")
    return {"status": "cancelled"}


@router.post("/react")
@limiter.limit("3/minute")
async def run_react_agent(
    request: Request,
    body: AgentRunRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """Run an agent using ReAct (Reason + Act) pattern with reflection loops.

    More advanced than the standard sequential agent - uses iterative
    thinking, acting, observing, and self-reflection.

    Rate limit: 3 requests/minute
    """
    from app.modules.agents.graph_engine import run_react_agent as react_run

    result = await react_run(
        instruction=body.instruction,
        user_id=current_user.id,
        max_iterations=5,
    )

    await BillingService.consume_quota(
        current_user.id, "ai_call", len(result.get("steps_completed", [])) or 1, session
    )

    return result
