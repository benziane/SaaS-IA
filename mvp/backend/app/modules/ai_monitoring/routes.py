"""
AI Monitoring API routes - LLM observability dashboard + Langfuse integration.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.ai_monitoring.service import AIMonitoringService
from app.rate_limit import limiter

router = APIRouter()


# ------------------------------------------------------------------
# Existing endpoints (unchanged)
# ------------------------------------------------------------------

@router.get("/dashboard")
@limiter.limit("20/minute")
async def monitoring_dashboard(
    request: Request,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """LLM observability dashboard with KPIs, provider stats, trends."""
    return await AIMonitoringService.get_dashboard(current_user.id, session, days)


@router.get("/providers")
@limiter.limit("20/minute")
async def provider_comparison(
    request: Request,
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Compare providers by latency, cost, and quality."""
    return await AIMonitoringService.get_provider_comparison(current_user.id, session, days)


@router.get("/traces")
@limiter.limit("20/minute")
async def recent_traces(
    request: Request,
    module: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get recent AI call traces (Langfuse-style)."""
    return await AIMonitoringService.get_recent_traces(current_user.id, session, module, limit)


# ------------------------------------------------------------------
# Langfuse integration endpoints
# ------------------------------------------------------------------

class LangfuseTraceRequest(BaseModel):
    name: str
    metadata: Optional[dict] = None


class LangfuseGenerationRequest(BaseModel):
    trace_id: str
    name: str
    model: str
    input: Optional[str] = None
    output: Optional[str] = None
    usage: Optional[dict] = None
    metadata: Optional[dict] = None


class LangfuseScoreRequest(BaseModel):
    trace_id: str
    generation_id: Optional[str] = None
    name: str = "quality"
    value: float = Field(ge=0.0, le=1.0)
    comment: Optional[str] = None


@router.post("/langfuse/traces")
@limiter.limit("30/minute")
async def create_langfuse_trace(
    request: Request,
    body: LangfuseTraceRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a Langfuse trace for an LLM operation."""
    trace = AIMonitoringService.create_trace(
        name=body.name,
        user_id=str(current_user.id),
        metadata=body.metadata,
    )
    if trace is None:
        return {"status": "skipped", "reason": "Langfuse not available"}
    return {"status": "created", "trace_id": trace.id}


@router.post("/langfuse/generations")
@limiter.limit("30/minute")
async def create_langfuse_generation(
    request: Request,
    body: LangfuseGenerationRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a Langfuse generation (LLM call) within a trace."""
    generation = AIMonitoringService.create_generation(
        trace_id=body.trace_id,
        name=body.name,
        model=body.model,
        input=body.input,
        output=body.output,
        usage=body.usage,
        metadata=body.metadata,
    )
    if generation is None:
        return {"status": "skipped", "reason": "Langfuse not available"}
    return {"status": "created", "generation_id": generation.id}


@router.post("/langfuse/scores")
@limiter.limit("30/minute")
async def score_langfuse_generation(
    request: Request,
    body: LangfuseScoreRequest,
    current_user: User = Depends(get_current_user),
):
    """Score a Langfuse generation or trace for quality tracking."""
    success = AIMonitoringService.score_generation(
        trace_id=body.trace_id,
        generation_id=body.generation_id,
        name=body.name,
        value=body.value,
        comment=body.comment,
    )
    if not success:
        return {"status": "skipped", "reason": "Langfuse not available"}
    return {"status": "scored"}


@router.get("/langfuse/status")
@limiter.limit("20/minute")
async def langfuse_status(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Check Langfuse integration status."""
    status = AIMonitoringService.get_langfuse_status()
    dashboard_url = AIMonitoringService.get_langfuse_dashboard_url()
    return {**status, "dashboard_url": dashboard_url}


@router.post("/langfuse/flush")
@limiter.limit("5/minute")
async def flush_langfuse(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Flush Langfuse client to ensure all pending events are sent."""
    success = AIMonitoringService.flush()
    return {"status": "flushed" if success else "skipped"}
