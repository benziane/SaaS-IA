"""
Multi-Agent Crew API routes - Create and run collaborative AI agent teams.
"""

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.multi_agent_crew.schemas import (
    AgentDefinition,
    AgentMessage,
    CrewCreate,
    CrewRead,
    CrewRunRead,
    CrewRunRequest,
    CrewTemplate,
    CrewUpdate,
)
from app.modules.multi_agent_crew.service import MultiAgentCrewService
from app.rate_limit import limiter

router = APIRouter()


def _crew_to_read(crew) -> CrewRead:
    agents_data = json.loads(crew.agents_json) if crew.agents_json else []
    return CrewRead(
        id=crew.id, user_id=crew.user_id, name=crew.name,
        description=crew.description, goal=crew.goal,
        agents=[AgentDefinition(**a) for a in agents_data],
        process_type=crew.process_type,
        status=crew.status.value if hasattr(crew.status, "value") else crew.status,
        is_template=crew.is_template,
        template_category=crew.template_category,
        run_count=crew.run_count,
        created_at=crew.created_at, updated_at=crew.updated_at,
    )


def _run_to_read(run) -> CrewRunRead:
    messages_data = json.loads(run.messages_json) if run.messages_json else []
    return CrewRunRead(
        id=run.id, crew_id=run.crew_id, user_id=run.user_id,
        status=run.status.value if hasattr(run.status, "value") else run.status,
        instruction=run.instruction,
        current_agent=run.current_agent, total_agents=run.total_agents,
        messages=[AgentMessage(**m) for m in messages_data],
        final_output=run.final_output, error=run.error,
        started_at=run.started_at, completed_at=run.completed_at,
        duration_ms=run.duration_ms, tokens_used=run.tokens_used,
        created_at=run.created_at,
    )


@router.post("/", response_model=CrewRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_crew(
    request: Request, body: CrewCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new AI agent crew. Rate limit: 10/min"""
    crew = await MultiAgentCrewService.create_crew(
        user_id=current_user.id, name=body.name,
        description=body.description, goal=body.goal,
        agents=[a.model_dump() for a in body.agents],
        process_type=body.process_type, session=session,
    )
    return _crew_to_read(crew)


@router.get("/", response_model=list[CrewRead])
@limiter.limit("20/minute")
async def list_crews(
    request: Request, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List user's crews. Rate limit: 20/min"""
    crews, _ = await MultiAgentCrewService.list_crews(current_user.id, session, skip, limit)
    return [_crew_to_read(c) for c in crews]


@router.get("/templates", response_model=list[CrewTemplate])
async def list_templates(category: Optional[str] = Query(None)):
    """List available crew templates."""
    templates = MultiAgentCrewService.get_templates(category)
    return [
        CrewTemplate(
            id=t["id"], name=t["name"], description=t["description"],
            category=t["category"], goal=t["goal"],
            agents=[AgentDefinition(**a) for a in t["agents"]],
            process_type=t["process_type"], icon=t.get("icon", "Groups"),
        ) for t in templates
    ]


@router.post("/from-template/{template_id}", response_model=CrewRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_from_template(
    request: Request, template_id: str, name: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a crew from a template. Rate limit: 10/min"""
    crew = await MultiAgentCrewService.create_from_template(template_id, current_user.id, name, session)
    if not crew:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template '{template_id}' not found")
    return _crew_to_read(crew)


@router.get("/{crew_id}", response_model=CrewRead)
@limiter.limit("30/minute")
async def get_crew(
    request: Request, crew_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get a crew by ID. Rate limit: 30/min"""
    crew = await MultiAgentCrewService.get_crew(crew_id, current_user.id, session)
    if not crew:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew not found")
    return _crew_to_read(crew)


@router.put("/{crew_id}", response_model=CrewRead)
@limiter.limit("10/minute")
async def update_crew(
    request: Request, crew_id: UUID, body: CrewUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update a crew. Rate limit: 10/min"""
    crew = await MultiAgentCrewService.update_crew(crew_id, current_user.id, body.model_dump(exclude_unset=True), session)
    if not crew:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew not found")
    return _crew_to_read(crew)


@router.delete("/{crew_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_crew(
    request: Request, crew_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a crew. Rate limit: 10/min"""
    if not await MultiAgentCrewService.delete_crew(crew_id, current_user.id, session):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew not found")


@router.post("/{crew_id}/run", response_model=CrewRunRead)
@limiter.limit("3/minute")
async def run_crew(
    request: Request, crew_id: UUID, body: CrewRunRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Run a crew with an instruction. Rate limit: 3/min"""
    run = await MultiAgentCrewService.run_crew(
        crew_id, current_user.id, body.instruction, session, body.input_data,
    )
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew not found")
    return _run_to_read(run)


@router.get("/{crew_id}/runs", response_model=list[CrewRunRead])
@limiter.limit("20/minute")
async def list_runs(
    request: Request, crew_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List crew runs. Rate limit: 20/min"""
    runs = await MultiAgentCrewService.list_runs(crew_id, current_user.id, session)
    return [_run_to_read(r) for r in runs]
