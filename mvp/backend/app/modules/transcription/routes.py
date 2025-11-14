"""
Transcription API routes
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Query, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.auth import get_current_user
from app.models.user import User
from app.schemas.transcription import TranscriptionCreate, TranscriptionRead
from app.modules.transcription.service import TranscriptionService
from app.rate_limit import limiter, get_rate_limit

# Router
router = APIRouter()


def get_transcription_service() -> TranscriptionService:
    """Dependency to get transcription service instance"""
    return TranscriptionService()


@router.post("/", response_model=TranscriptionRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit("transcription_create"))
async def create_transcription(
    request: Request,
    data: TranscriptionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Create a new transcription job
    
    The transcription will be processed in the background.
    You can check the status using GET /api/transcription/{job_id}
    
    Rate limit: 10 requests/minute (API cost control)
    """
    
    # Create job
    job = await service.create_job(
        video_url=data.video_url,
        user_id=current_user.id,
        language=data.language,
        session=session
    )
    
    # Process in background (non-blocking)
    background_tasks.add_task(service.process_transcription, job.id)
    
    return job


@router.get("/{job_id}", response_model=TranscriptionRead)
@limiter.limit(get_rate_limit("transcription_get"))
async def get_transcription(
    request: Request,
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Get a transcription job by ID
    
    Rate limit: 30 requests/minute
    """
    
    job = await service.get_job(job_id, session)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return job


@router.get("/", response_model=List[TranscriptionRead])
@limiter.limit(get_rate_limit("transcription_list"))
async def list_transcriptions(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    service: TranscriptionService = Depends(get_transcription_service)
):
    """
    List all transcription jobs for the current user
    
    Rate limit: 20 requests/minute
    """
    
    jobs = await service.list_user_jobs(
        user_id=current_user.id,
        session=session,
        skip=skip,
        limit=limit
    )
    
    return jobs


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(get_rate_limit("transcription_delete"))
async def delete_transcription(
    request: Request,
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Delete a transcription job
    
    Rate limit: 10 requests/minute
    """
    
    # Get job to check ownership
    job = await service.get_job(job_id, session)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Delete
    await service.delete_job(job_id, session)
    
    return None

