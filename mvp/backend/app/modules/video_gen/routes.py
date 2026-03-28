"""
Video Generation API routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.video_gen.schemas import (
    AvatarVideoRequest, ClipHighlightsRequest, GenerateVideoRequest,
    VideoFromSourceRequest, VideoProjectCreate, VideoProjectRead, VideoRead,
)
from app.modules.video_gen.service import VideoGenService
from app.rate_limit import limiter

router = APIRouter()


@router.post("/generate", response_model=VideoRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def generate_video(
    request: Request, body: GenerateVideoRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Generate a video from text prompt. Rate limit: 3/min"""
    return await VideoGenService.generate_video(
        user_id=current_user.id, title=body.title, prompt=body.prompt,
        video_type=body.video_type, provider=body.provider,
        duration_s=body.duration_s, width=body.width, height=body.height,
        session=session, style=body.style, project_id=body.project_id,
        settings=body.settings,
    )


@router.post("/clips", response_model=list[VideoRead])
@limiter.limit("2/minute")
async def generate_clips(
    request: Request, body: ClipHighlightsRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Generate highlight clips from a transcription. Rate limit: 2/min"""
    clips = await VideoGenService.generate_clips(
        user_id=current_user.id, transcription_id=body.transcription_id,
        max_clips=body.max_clips, clip_duration_s=body.clip_duration_s,
        format_type=body.format, provider=body.provider, session=session,
    )
    if not clips:
        raise HTTPException(status_code=404, detail="Transcription not found or empty")
    return clips


@router.post("/avatar", response_model=VideoRead)
@limiter.limit("3/minute")
async def generate_avatar(
    request: Request, body: AvatarVideoRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Generate a talking avatar video. Rate limit: 3/min"""
    return await VideoGenService.generate_avatar_video(
        user_id=current_user.id, text=body.text,
        avatar_style=body.avatar_style, voice_id=body.voice_id,
        background=body.background, provider=body.provider, session=session,
    )


@router.post("/from-source", response_model=VideoRead)
@limiter.limit("3/minute")
async def generate_from_source(
    request: Request, body: VideoFromSourceRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Generate video from transcription or document. Rate limit: 3/min"""
    return await VideoGenService.generate_from_source(
        user_id=current_user.id, source_type=body.source_type,
        source_id=body.source_id, video_type=body.video_type,
        title=body.title, provider=body.provider,
        duration_s=body.duration_s, session=session,
    )


@router.get("/", response_model=list[VideoRead])
@limiter.limit("20/minute")
async def list_videos(
    request: Request, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List generated videos. Rate limit: 20/min"""
    return await VideoGenService.list_videos(current_user.id, session, skip, limit)


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_video(
    request: Request, video_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Delete a video. Rate limit: 10/min"""
    if not await VideoGenService.delete_video(video_id, current_user.id, session):
        raise HTTPException(status_code=404, detail="Video not found")


@router.post("/projects", response_model=VideoProjectRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_project(
    request: Request, body: VideoProjectCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Create a video project. Rate limit: 10/min"""
    return await VideoGenService.create_project(current_user.id, body.name, body.description, session)


@router.get("/projects", response_model=list[VideoProjectRead])
@limiter.limit("20/minute")
async def list_projects(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List video projects. Rate limit: 20/min"""
    return await VideoGenService.list_projects(current_user.id, session)


@router.get("/types")
async def list_video_types():
    """List available video types."""
    return {"types": [
        {"id": "text_to_video", "name": "Text to Video", "description": "Generate video from text description"},
        {"id": "image_to_video", "name": "Image to Video", "description": "Animate a static image"},
        {"id": "clip_highlights", "name": "Clip Highlights", "description": "Auto-extract viral moments"},
        {"id": "avatar_talking", "name": "Talking Avatar", "description": "AI avatar reads your script"},
        {"id": "explainer", "name": "Explainer Video", "description": "Educational explanation video"},
        {"id": "short_form", "name": "Short Form", "description": "TikTok/Reels/Shorts format"},
    ]}
