"""
Audio Studio API routes - Podcast/audio editing studio with AI features.
"""

import json
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status, Query
from fastapi.responses import FileResponse, Response
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.modules.audio_studio.schemas import (
    AudioEditRequest,
    AudioRead,
    AudioUploadResponse,
    ChapterCreate,
    PodcastEpisodeCreate,
    PodcastEpisodeRead,
    RSSFeedConfig,
    SplitRequest,
)
from app.modules.audio_studio.service import AudioStudioService
from app.rate_limit import limiter

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".mp4", ".m4a", ".ogg", ".webm", ".flac", ".aac", ".wma"}
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB


def _get_service(session: AsyncSession = Depends(get_session)) -> AudioStudioService:
    return AudioStudioService(session)


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=AudioUploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def upload_audio(
    request: Request,
    file: UploadFile = File(..., description="Audio file (mp3, wav, ogg, flac, m4a, etc.)"),
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Upload an audio file. Rate limit: 5/min."""
    # Validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    data = await file.read()
    if len(data) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum: {MAX_UPLOAD_SIZE // (1024 * 1024)} MB",
        )

    record = await service.upload_audio(
        user_id=current_user.id,
        file_bytes=data,
        original_filename=file.filename or "audio.mp3",
    )
    return record


# ---------------------------------------------------------------------------
# List / Get / Delete
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[AudioRead])
@limiter.limit("30/minute")
async def list_audio(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """List audio files. Rate limit: 30/min."""
    items, _total = await service.list_audio(current_user.id, skip, limit)
    # Hydrate chapters from JSON
    results = []
    for item in items:
        read = AudioRead(
            id=item.id,
            user_id=item.user_id,
            filename=item.original_filename,
            duration_seconds=item.duration_seconds,
            sample_rate=item.sample_rate,
            channels=item.channels,
            format=item.format,
            file_size_kb=item.file_size_kb,
            transcript=item.transcript,
            chapters=json.loads(item.chapters_json) if item.chapters_json else [],
            status=item.status.value if hasattr(item.status, "value") else item.status,
            waveform_data=json.loads(item.waveform_json) if item.waveform_json else None,
            created_at=item.created_at,
        )
        results.append(read)
    return results


@router.get("/{audio_id}", response_model=AudioRead)
@limiter.limit("30/minute")
async def get_audio(
    request: Request,
    audio_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Get audio file details. Rate limit: 30/min."""
    item = await service.get_audio(current_user.id, audio_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")
    return AudioRead(
        id=item.id,
        user_id=item.user_id,
        filename=item.original_filename,
        duration_seconds=item.duration_seconds,
        sample_rate=item.sample_rate,
        channels=item.channels,
        format=item.format,
        file_size_kb=item.file_size_kb,
        transcript=item.transcript,
        chapters=json.loads(item.chapters_json) if item.chapters_json else [],
        status=item.status.value if hasattr(item.status, "value") else item.status,
        waveform_data=json.loads(item.waveform_json) if item.waveform_json else None,
        created_at=item.created_at,
    )


@router.delete("/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_audio(
    request: Request,
    audio_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Delete an audio file. Rate limit: 5/min."""
    if not await service.delete_audio(current_user.id, audio_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found")


# ---------------------------------------------------------------------------
# Edit
# ---------------------------------------------------------------------------

@router.post("/{audio_id}/edit", response_model=AudioRead)
@limiter.limit("10/minute")
async def edit_audio(
    request: Request,
    audio_id: UUID,
    body: AudioEditRequest,
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Apply edit operations to an audio file (non-destructive). Rate limit: 10/min."""
    try:
        item = await service.edit_audio(
            user_id=current_user.id,
            audio_id=audio_id,
            operations=[op.dict() for op in body.operations],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    return AudioRead(
        id=item.id,
        user_id=item.user_id,
        filename=item.original_filename,
        duration_seconds=item.duration_seconds,
        sample_rate=item.sample_rate,
        channels=item.channels,
        format=item.format,
        file_size_kb=item.file_size_kb,
        transcript=item.transcript,
        chapters=json.loads(item.chapters_json) if item.chapters_json else [],
        status=item.status.value if hasattr(item.status, "value") else item.status,
        waveform_data=json.loads(item.waveform_json) if item.waveform_json else None,
        created_at=item.created_at,
    )


# ---------------------------------------------------------------------------
# Transcribe
# ---------------------------------------------------------------------------

@router.post("/{audio_id}/transcribe", response_model=AudioRead)
@limiter.limit("5/minute")
async def transcribe_audio(
    request: Request,
    audio_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Transcribe audio file. Rate limit: 5/min."""
    try:
        item = await service.transcribe_audio(current_user.id, audio_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return AudioRead(
        id=item.id,
        user_id=item.user_id,
        filename=item.original_filename,
        duration_seconds=item.duration_seconds,
        sample_rate=item.sample_rate,
        channels=item.channels,
        format=item.format,
        file_size_kb=item.file_size_kb,
        transcript=item.transcript,
        chapters=json.loads(item.chapters_json) if item.chapters_json else [],
        status=item.status.value if hasattr(item.status, "value") else item.status,
        waveform_data=json.loads(item.waveform_json) if item.waveform_json else None,
        created_at=item.created_at,
    )


# ---------------------------------------------------------------------------
# Chapters
# ---------------------------------------------------------------------------

@router.post("/{audio_id}/chapters", response_model=AudioRead)
@limiter.limit("10/minute")
async def generate_chapters(
    request: Request,
    audio_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Generate AI-powered chapter markers. Rate limit: 10/min."""
    try:
        item = await service.generate_chapters(current_user.id, audio_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return AudioRead(
        id=item.id,
        user_id=item.user_id,
        filename=item.original_filename,
        duration_seconds=item.duration_seconds,
        sample_rate=item.sample_rate,
        channels=item.channels,
        format=item.format,
        file_size_kb=item.file_size_kb,
        transcript=item.transcript,
        chapters=json.loads(item.chapters_json) if item.chapters_json else [],
        status=item.status.value if hasattr(item.status, "value") else item.status,
        waveform_data=json.loads(item.waveform_json) if item.waveform_json else None,
        created_at=item.created_at,
    )


# ---------------------------------------------------------------------------
# Show Notes
# ---------------------------------------------------------------------------

@router.post("/{audio_id}/show-notes")
@limiter.limit("10/minute")
async def generate_show_notes(
    request: Request,
    audio_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Generate AI-powered podcast show notes. Rate limit: 10/min."""
    try:
        return await service.generate_show_notes(current_user.id, audio_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Waveform
# ---------------------------------------------------------------------------

@router.get("/{audio_id}/waveform")
@limiter.limit("30/minute")
async def get_waveform(
    request: Request,
    audio_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Get waveform visualization data. Rate limit: 30/min."""
    try:
        waveform = await service.generate_waveform(current_user.id, audio_id)
        return {"audio_id": str(audio_id), "waveform": waveform, "points": len(waveform)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------

@router.post("/{audio_id}/split")
@limiter.limit("5/minute")
async def split_audio(
    request: Request,
    audio_id: UUID,
    body: Optional[SplitRequest] = None,
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Split audio at silence points. Rate limit: 5/min."""
    min_silence_ms = body.min_silence_ms if body else 1000
    silence_thresh_db = body.silence_thresh_db if body else -40
    try:
        segments = await service.split_by_silence(
            current_user.id, audio_id, min_silence_ms, silence_thresh_db,
        )
        return {"audio_id": str(audio_id), "segments": segments, "count": len(segments)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

@router.get("/{audio_id}/export/{target_format}")
@limiter.limit("30/minute")
async def export_audio(
    request: Request,
    audio_id: UUID,
    target_format: str,
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Export audio to mp3/wav/ogg/flac. Rate limit: 30/min."""
    try:
        file_path = await service.export_audio(current_user.id, audio_id, target_format)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Export failed")

        media_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
        }
        return FileResponse(
            path=file_path,
            media_type=media_types.get(target_format, "application/octet-stream"),
            filename=os.path.basename(file_path),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))


# ---------------------------------------------------------------------------
# Podcast Episodes
# ---------------------------------------------------------------------------

@router.post("/episodes", response_model=PodcastEpisodeRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_episode(
    request: Request,
    body: PodcastEpisodeCreate,
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Create a podcast episode. Rate limit: 10/min."""
    try:
        episode = await service.create_podcast_episode(current_user.id, body.dict())
        return episode
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/episodes", response_model=list[PodcastEpisodeRead])
@limiter.limit("30/minute")
async def list_episodes(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """List podcast episodes. Rate limit: 30/min."""
    return await service.list_episodes(current_user.id, skip, limit)


# ---------------------------------------------------------------------------
# RSS Feed
# ---------------------------------------------------------------------------

@router.post("/rss-feed")
@limiter.limit("5/minute")
async def generate_rss_feed(
    request: Request,
    body: RSSFeedConfig,
    current_user: User = Depends(get_current_user),
    service: AudioStudioService = Depends(_get_service),
):
    """Generate RSS/XML podcast feed. Rate limit: 5/min."""
    xml = await service.generate_rss_feed(current_user.id, body.dict())
    return Response(content=xml, media_type="application/rss+xml")
