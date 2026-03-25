"""
Public API v1 routes - Authenticated via API key (X-API-Key header).
"""

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.modules.api_keys.service import APIKeyService
from app.rate_limit import limiter

router = APIRouter()


async def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    session: AsyncSession = Depends(get_session),
) -> tuple:
    """Dependency to verify API key from header.

    Raises 401 for invalid/expired keys, 429 when the daily limit is exceeded.
    """
    # verify_key raises HTTPException(429) when daily limit is hit
    result = await APIKeyService.verify_key(x_api_key, session)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
        )
    return result  # (user_id, permissions)


@router.post("/transcribe")
@limiter.limit("10/minute")
async def api_transcribe(
    request: Request,
    auth: tuple = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """
    Public API: Submit a transcription job.

    Authenticate with X-API-Key header.

    Rate limit: 10 requests/minute
    """
    user_id, permissions = auth
    if "write" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key does not have 'write' permission",
        )

    body = await request.json()
    video_url = body.get("video_url")
    language = body.get("language", "auto")

    if not video_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="video_url is required",
        )

    from app.modules.transcription.service import TranscriptionService
    service = TranscriptionService()
    job = await service.create_job(
        video_url=video_url,
        user_id=user_id,
        language=language,
        session=session,
    )

    return {
        "job_id": str(job.id),
        "status": job.status.value,
        "message": "Transcription job created. Check status via GET /v1/jobs/{job_id}",
    }


@router.post("/process")
@limiter.limit("10/minute")
async def api_process(
    request: Request,
    auth: tuple = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """
    Public API: Process text with AI.

    Authenticate with X-API-Key header.

    Rate limit: 10 requests/minute
    """
    user_id, permissions = auth
    if "write" not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key does not have 'write' permission",
        )

    body = await request.json()
    text = body.get("text")
    task = body.get("task", "general")
    provider = body.get("provider", "gemini")

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="text is required",
        )

    from app.ai_assistant.service import AIAssistantService
    result = await AIAssistantService.process_text_with_provider(
        text=text,
        task=task,
        provider_name=provider,
    )

    return {
        "result": result.get("processed_text", ""),
        "provider": result.get("provider", provider),
        "model": result.get("model", provider),
    }


@router.get("/jobs/{job_id}")
@limiter.limit("30/minute")
async def api_get_job(
    request: Request,
    job_id: str,
    auth: tuple = Depends(verify_api_key),
    session: AsyncSession = Depends(get_session),
):
    """
    Public API: Get job status.

    Authenticate with X-API-Key header.

    Rate limit: 30 requests/minute
    """
    from uuid import UUID
    from app.modules.transcription.service import TranscriptionService

    user_id, permissions = auth
    service = TranscriptionService()

    try:
        job = await service.get_job(UUID(job_id), session)
    except (ValueError, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format",
        )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return {
        "job_id": str(job.id),
        "status": job.status.value,
        "text": job.text,
        "confidence": job.confidence,
        "duration_seconds": job.duration_seconds,
        "error": job.error,
        "created_at": job.created_at.isoformat(),
    }
