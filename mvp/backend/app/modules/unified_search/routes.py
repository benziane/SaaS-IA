"""Unified Search API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.unified_search.service import UnifiedSearchService
from app.rate_limit import limiter

router = APIRouter()


@router.get("/")
@limiter.limit("30/minute")
async def universal_search(
    request: Request,
    q: str = Query(..., min_length=1, max_length=500),
    modules: Optional[str] = Query(None, description="Comma-separated module filter"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Search across all platform modules in one query."""
    module_list = modules.split(",") if modules else None
    return await UnifiedSearchService.search(current_user.id, q, session, module_list, limit)


@router.get("/answer")
@limiter.limit("10/minute")
async def search_and_answer(
    request: Request,
    q: str = Query(..., min_length=1, max_length=500),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Cross-module RAG: search all modules and synthesize an answer."""
    return await UnifiedSearchService.search_and_answer(current_user.id, q, session)
