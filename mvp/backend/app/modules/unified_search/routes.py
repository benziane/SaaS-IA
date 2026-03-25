"""Unified Search API routes."""

from typing import Optional
from fastapi import APIRouter, Body, Depends, Query, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.unified_search.service import UnifiedSearchService, is_meilisearch_available
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


@router.get("/status")
@limiter.limit("30/minute")
async def search_status(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Return search engine status (Meilisearch availability)."""
    return {
        "meilisearch_available": is_meilisearch_available(),
        "fallback": "postgresql",
    }


@router.post("/index")
@limiter.limit("60/minute")
async def index_document(
    request: Request,
    module: str = Body(..., description="Module name (e.g. transcriptions, knowledge)"),
    doc_id: str = Body(..., description="Unique document identifier"),
    content: str = Body(..., description="Text content to index"),
    metadata: Optional[dict] = Body(None, description="Extra metadata fields"),
    current_user: User = Depends(get_current_user),
):
    """Index a document in Meilisearch for fast search."""
    meta = metadata or {}
    meta.setdefault("user_id", str(current_user.id))
    success = await UnifiedSearchService.index_document(module, doc_id, content, meta)
    return {"indexed": success, "module": module, "doc_id": doc_id}


@router.post("/reindex/{module_name}")
@limiter.limit("5/minute")
async def reindex_module(
    request: Request,
    module_name: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Rebuild Meilisearch index for a specific module from PostgreSQL data."""
    result = await UnifiedSearchService.reindex_module(module_name, session)
    return result
