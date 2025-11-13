"""
API endpoints for transcription management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.core.database import get_db
from app.models.transcription import Transcription, TranscriptionStatus, LanguageCode
from app.schemas.transcription import (
    TranscriptionCreate,
    TranscriptionResponse,
    TranscriptionList,
    TranscriptionStats
)
from app.services.transcription_orchestrator import TranscriptionOrchestrator
from app.services.youtube_extractor import YouTubeExtractor

router = APIRouter(prefix="/transcriptions", tags=["transcriptions"])
orchestrator = TranscriptionOrchestrator()
youtube_extractor = YouTubeExtractor()


@router.post("/", response_model=TranscriptionResponse, status_code=201)
async def create_transcription(
    transcription_data: TranscriptionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new transcription job

    This endpoint:
    1. Validates the YouTube URL
    2. Extracts video ID
    3. Creates a database record
    4. Starts background processing
    """
    try:
        # Extract video ID
        video_id = youtube_extractor.extract_video_id(transcription_data.youtube_url)

        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        # Check if transcription already exists for this video
        result = await db.execute(
            select(Transcription).where(Transcription.video_id == video_id)
        )
        existing = result.scalar_one_or_none()

        if existing and existing.status != TranscriptionStatus.FAILED:
            return TranscriptionResponse.model_validate(existing)

        # Create transcription record
        transcription = Transcription(
            youtube_url=transcription_data.youtube_url,
            video_id=video_id,
            language=transcription_data.language,
            status=TranscriptionStatus.PENDING,
            progress=0
        )

        db.add(transcription)
        await db.commit()
        await db.refresh(transcription)

        # Start background processing
        background_tasks.add_task(
            orchestrator.process_transcription,
            transcription.id,
            db
        )

        return TranscriptionResponse.model_validate(transcription)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(
    transcription_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get transcription by ID

    Returns complete transcription information including:
    - Video metadata
    - Processing status and progress
    - Raw and corrected transcripts
    - Confidence scores and statistics
    """
    result = await db.execute(
        select(Transcription).where(Transcription.id == transcription_id)
    )
    transcription = result.scalar_one_or_none()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    return TranscriptionResponse.model_validate(transcription)


@router.get("/", response_model=TranscriptionList)
async def list_transcriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TranscriptionStatus] = None,
    language: Optional[LanguageCode] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all transcriptions with pagination

    Supports filtering by:
    - Status (pending, completed, failed, etc.)
    - Language (fr, en, ar, etc.)
    """
    # Build query
    query = select(Transcription).where(Transcription.is_deleted == False)

    if status:
        query = query.where(Transcription.status == status)

    if language:
        query = query.where(Transcription.language == language)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.order_by(Transcription.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    transcriptions = result.scalars().all()

    return TranscriptionList(
        transcriptions=[TranscriptionResponse.model_validate(t) for t in transcriptions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/video/{video_id}", response_model=TranscriptionResponse)
async def get_transcription_by_video_id(
    video_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get transcription by YouTube video ID

    Useful for checking if a video has already been transcribed
    """
    result = await db.execute(
        select(Transcription).where(Transcription.video_id == video_id)
    )
    transcription = result.scalar_one_or_none()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found for this video")

    return TranscriptionResponse.model_validate(transcription)


@router.post("/preview")
async def preview_video(url: str):
    """
    Get video information without creating transcription

    Useful for showing video details before starting transcription
    """
    try:
        video_info = await orchestrator.get_video_preview(url)
        return video_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{transcription_id}")
async def delete_transcription(
    transcription_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete transcription (soft delete)

    Marks transcription as deleted without removing from database
    """
    result = await db.execute(
        select(Transcription).where(Transcription.id == transcription_id)
    )
    transcription = result.scalar_one_or_none()

    if not transcription:
        raise HTTPException(status_code=404, detail="Transcription not found")

    transcription.is_deleted = True
    await db.commit()

    return {"message": "Transcription deleted successfully"}


@router.get("/stats/overview", response_model=TranscriptionStats)
async def get_transcription_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get transcription statistics

    Returns:
    - Total transcriptions count
    - Status breakdown (completed, in progress, failed)
    - Total video duration processed
    - Average confidence score
    - Language distribution
    """
    # Get counts by status
    result = await db.execute(
        select(
            func.count(Transcription.id).label("total"),
            func.count().filter(Transcription.status == TranscriptionStatus.COMPLETED).label("completed"),
            func.count().filter(
                Transcription.status.in_([
                    TranscriptionStatus.PENDING,
                    TranscriptionStatus.DOWNLOADING,
                    TranscriptionStatus.EXTRACTING,
                    TranscriptionStatus.TRANSCRIBING,
                    TranscriptionStatus.POST_PROCESSING
                ])
            ).label("in_progress"),
            func.count().filter(Transcription.status == TranscriptionStatus.FAILED).label("failed"),
            func.sum(Transcription.video_duration).label("total_duration"),
            func.sum(Transcription.processing_time).label("total_processing_time"),
            func.avg(Transcription.confidence_score).label("avg_confidence")
        ).where(Transcription.is_deleted == False)
    )
    stats = result.one()

    # Get language distribution
    lang_result = await db.execute(
        select(
            Transcription.language,
            func.count(Transcription.id).label("count")
        )
        .where(Transcription.is_deleted == False)
        .group_by(Transcription.language)
    )
    languages = {row.language: row.count for row in lang_result}

    return TranscriptionStats(
        total_transcriptions=stats.total or 0,
        completed=stats.completed or 0,
        in_progress=stats.in_progress or 0,
        failed=stats.failed or 0,
        total_duration=stats.total_duration or 0.0,
        total_processing_time=stats.total_processing_time or 0.0,
        average_confidence=stats.avg_confidence or 0.0,
        languages=languages
    )
