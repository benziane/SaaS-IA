"""
AI Monitoring API routes - LLM observability dashboard.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.ai_monitoring.service import AIMonitoringService
from app.rate_limit import limiter

router = APIRouter()


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
