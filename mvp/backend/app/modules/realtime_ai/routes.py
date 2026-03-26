"""
Realtime AI API routes - Live voice and vision AI sessions.
"""

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.realtime_ai.schemas import (
    SendMessageRequest,
    SessionCreate,
    SessionRead,
    SessionSummaryRequest,
    SessionTranscript,
)
from app.modules.realtime_ai.service import RealtimeAIService
from app.rate_limit import limiter

router = APIRouter()


def _session_to_read(rt) -> SessionRead:
    return SessionRead(
        id=rt.id, user_id=rt.user_id, title=rt.title,
        mode=rt.mode.value if hasattr(rt.mode, "value") else rt.mode,
        status=rt.status.value if hasattr(rt.status, "value") else rt.status,
        provider=rt.provider, model=rt.model,
        system_prompt=rt.system_prompt,
        knowledge_base_id=rt.knowledge_base_id,
        config_json=rt.config_json,
        total_turns=rt.total_turns,
        audio_duration_s=rt.audio_duration_s,
        tokens_used=rt.tokens_used,
        started_at=rt.started_at,
        ended_at=rt.ended_at,
        created_at=rt.created_at,
    )


@router.post("/sessions", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_session(
    request: Request, body: SessionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new realtime AI session. Rate limit: 10/min"""
    rt = await RealtimeAIService.create_session(
        user_id=current_user.id, title=body.title, mode=body.mode,
        provider=body.provider, system_prompt=body.system_prompt,
        knowledge_base_id=body.knowledge_base_id, config=body.config,
        session=session,
    )
    return _session_to_read(rt)


@router.get("/sessions", response_model=list[SessionRead])
@limiter.limit("20/minute")
async def list_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List user's sessions. Rate limit: 20/min"""
    sessions = await RealtimeAIService.list_sessions(current_user.id, session)
    return [_session_to_read(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionRead)
@limiter.limit("30/minute")
async def get_session_detail(
    request: Request, session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get session details. Rate limit: 30/min"""
    rt = await RealtimeAIService.get_session(session_id, current_user.id, session)
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return _session_to_read(rt)


@router.post("/sessions/{session_id}/message")
@limiter.limit("30/minute")
async def send_message(
    request: Request, session_id: UUID, body: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Send a message and get AI response. Rate limit: 30/min"""
    result = await RealtimeAIService.send_message(
        session_id, current_user.id, body.content, body.content_type, session,
    )
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
    return result


@router.post("/sessions/{session_id}/end", response_model=SessionRead)
@limiter.limit("10/minute")
async def end_session(
    request: Request, session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """End a session and generate summary. Rate limit: 10/min"""
    rt = await RealtimeAIService.end_session(session_id, current_user.id, session)
    if not rt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return _session_to_read(rt)


@router.get("/sessions/{session_id}/transcript")
@limiter.limit("20/minute")
async def get_transcript(
    request: Request, session_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get full session transcript. Rate limit: 20/min"""
    transcript = await RealtimeAIService.get_transcript(session_id, current_user.id, session)
    if not transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return transcript


@router.get("/config")
@limiter.limit("20/minute")
async def get_config(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get available realtime AI configuration options."""
    return RealtimeAIService.get_config()
