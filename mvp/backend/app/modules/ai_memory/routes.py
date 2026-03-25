"""AI Memory API routes."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.ai_memory.service import AIMemoryService
from app.rate_limit import limiter

router = APIRouter()


class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    memory_type: str = Field(default="fact", description="preference, fact, context, instruction")
    category: Optional[str] = None


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    source: str = Field(default="manual")


@router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def add_memory(
    request: Request, body: MemoryCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Add a memory entry manually."""
    return await AIMemoryService.add_memory(
        current_user.id, body.content, body.memory_type, body.category, "manual", session,
    )


@router.get("/")
@limiter.limit("20/minute")
async def list_memories(
    request: Request,
    memory_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List user memories."""
    return await AIMemoryService.list_memories(current_user.id, session, memory_type)


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_memory(
    request: Request, memory_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a memory."""
    if not await AIMemoryService.delete_memory(memory_id, current_user.id, session):
        raise HTTPException(status_code=404, detail="Memory not found")


@router.get("/context")
@limiter.limit("30/minute")
async def get_context(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get the current memory context injection string."""
    context = await AIMemoryService.get_context_injection(current_user.id, session)
    return {"context": context, "has_memories": bool(context)}


@router.post("/extract")
@limiter.limit("5/minute")
async def extract_memories(
    request: Request, body: ExtractRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Auto-extract memories from text using AI."""
    memories = await AIMemoryService.auto_extract_memories(
        current_user.id, body.text, body.source, session,
    )
    return {"extracted": len(memories), "memories": memories}


@router.delete("/forget-all", status_code=status.HTTP_200_OK)
@limiter.limit("1/minute")
async def forget_all(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """RGPD: forget all memories."""
    count = await AIMemoryService.forget_all(current_user.id, session)
    return {"forgotten": count}
