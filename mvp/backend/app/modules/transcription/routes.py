"""
Transcription API routes
"""

import os
import tempfile
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, status, Query, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.auth import get_current_user
from app.models.user import User, Role
from app.modules.billing.service import BillingService
from app.modules.billing.middleware import require_transcription_quota
from app.models.transcription import TranscriptionStatus
from app.schemas.transcription import TranscriptionCreate, TranscriptionRead, PaginatedResponse
from app.modules.transcription.service import TranscriptionService
from app.modules.transcription.websocket import get_debug_manager
from app.transcription.audio_cache import get_audio_cache
from app.config import settings
from app.rate_limit import limiter, get_rate_limit

# Allowed file types for upload transcription
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".mp4", ".m4a", ".ogg", ".webm", ".flac"}
ALLOWED_MIME_TYPES = {
    "audio/mpeg", "audio/mp3",
    "audio/wav", "audio/x-wav", "audio/wave",
    "video/mp4", "audio/mp4",
    "audio/m4a", "audio/x-m4a",
    "audio/ogg", "audio/vorbis",
    "video/webm", "audio/webm",
    "audio/flac", "audio/x-flac",
}
MAX_UPLOAD_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB

# Router
router = APIRouter()


def _celery_available() -> bool:
    """Check if Celery workers are available."""
    try:
        from app.celery_app import celery_app
        # Ping with a short timeout to check if any worker is reachable
        result = celery_app.control.ping(timeout=1.0)
        return bool(result)
    except Exception:
        return False


def _require_debug_access(user: User) -> None:
    """Raise 403 unless the environment is development or the user is admin."""
    if settings.ENVIRONMENT == "development":
        return
    if user.role == Role.ADMIN:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Debug endpoints are restricted to development environment or admin users"
    )


def get_transcription_service() -> TranscriptionService:
    """Dependency to get transcription service instance"""
    return TranscriptionService()


@router.post("/", response_model=TranscriptionRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit("transcription_create"))
async def create_transcription(
    request: Request,
    data: TranscriptionCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_transcription_quota),
    session: AsyncSession = Depends(get_session),
    service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Create a new transcription job.

    Accepts source_type: "youtube" (default) or "url" (non-YouTube sites
    supported by yt-dlp).  The transcription will be processed in the
    background.  Check status via GET /api/transcription/{job_id}.

    Rate limit: 10 requests/minute (API cost control)
    """

    # Create job
    job = await service.create_job(
        video_url=data.video_url,
        user_id=current_user.id,
        language=data.language,
        session=session,
        source_type=data.source_type
    )

    # Consume transcription quota
    await BillingService.consume_quota(current_user.id, "transcription", 1, session)

    # Process via Celery if available, otherwise fallback to BackgroundTasks
    if _celery_available():
        from app.modules.transcription.tasks import process_transcription_task
        process_transcription_task.delay(
            str(job.id), data.video_url, data.language or "auto", data.source_type
        )
    else:
        background_tasks.add_task(service.process_transcription, job.id)

    return job


@router.post("/upload", response_model=TranscriptionRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def upload_transcription(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Audio/video file to transcribe"),
    language: Optional[str] = Form("auto", description="Language code (e.g., 'en', 'fr', 'auto')"),
    current_user: User = Depends(require_transcription_quota),
    session: AsyncSession = Depends(get_session),
    service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Upload an audio/video file for transcription.

    Supported formats: MP3, WAV, MP4, M4A, OGG, WEBM, FLAC.
    Maximum file size: 500 MB.

    The transcription is processed in the background.
    Check status via GET /api/transcription/{job_id}.

    Rate limit: 5 requests/minute
    """

    # Validate filename and extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename."
        )

    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Validate MIME type
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MIME type '{content_type}'. Allowed types: audio/mpeg, audio/wav, video/mp4, audio/m4a, audio/ogg, video/webm, audio/flac"
        )

    # Read file and validate size
    file_content = await file.read()
    if len(file_content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
        )

    if len(file_content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # Save to temporary location in the audio cache directory
    audio_cache = get_audio_cache()
    upload_dir = os.path.join(audio_cache._cache_dir, "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    safe_filename = f"{uuid4()}{ext}"
    temp_path = os.path.join(upload_dir, safe_filename)

    try:
        with open(temp_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # Create transcription job
    job = await service.create_job(
        video_url=f"upload://{file.filename}",
        user_id=current_user.id,
        language=language,
        session=session,
        source_type="upload",
        original_filename=file.filename
    )

    # Consume transcription quota
    await BillingService.consume_quota(current_user.id, "transcription", 1, session)

    # Process via Celery if available, otherwise fallback to BackgroundTasks
    if _celery_available():
        from app.modules.transcription.tasks import process_upload_task
        process_upload_task.delay(str(job.id), temp_path, language)
    else:
        background_tasks.add_task(service.process_upload_transcription, job.id, temp_path, language)

    return job


@router.get("/stats")
@limiter.limit("20/minute")
async def get_transcription_stats(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Get transcription statistics for the current user.

    Returns aggregate counts, total duration, average confidence,
    and the 5 most recent transcription jobs.

    Rate limit: 20 requests/minute
    """
    return await service.get_user_stats(
        user_id=current_user.id,
        session=session,
    )


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


@router.get("/", response_model=PaginatedResponse[TranscriptionRead])
@limiter.limit(get_rate_limit("transcription_list"))
async def list_transcriptions(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of items to return"),
    status: Optional[TranscriptionStatus] = Query(None, description="Filter by transcription status"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    service: TranscriptionService = Depends(get_transcription_service)
):
    """
    List all transcription jobs for the current user with pagination.

    Returns a paginated response containing items, total count, and pagination metadata.

    Rate limit: 20 requests/minute
    """

    items, total = await service.list_user_jobs(
        user_id=current_user.id,
        session=session,
        skip=skip,
        limit=limit,
        status=status
    )

    return PaginatedResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total
    )


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


@router.websocket("/debug/{job_id}")
async def websocket_debug(
    websocket: WebSocket,
    job_id: str
):
    """
    WebSocket endpoint for real-time debug streaming
    """
    # Block access in non-development environments
    if settings.ENVIRONMENT != "development":
        await websocket.close(code=4003, reason="Debug endpoints are restricted to development environment")
        return

    manager = get_debug_manager()
    await manager.connect(websocket, job_id)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "job_id": job_id,
            "message": "Debug stream connected"
        })
        
        # Keep connection alive
        while True:
            # Wait for messages (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)


@router.get("/debug/{job_id}/audio")
async def download_debug_audio(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download cached audio file for debugging

    Audio files are cached for 30 minutes after transcription.
    This endpoint allows you to download and listen to the audio that was transcribed.
    """
    _require_debug_access(current_user)
    audio_cache = get_audio_cache()
    
    # Get cached audio
    cached_audio = audio_cache.get_audio(job_id)
    
    if not cached_audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found or expired (cached for 30 minutes)"
        )
    
    # Return audio file
    return FileResponse(
        path=cached_audio["path"],
        filename=cached_audio["filename"],
        media_type="audio/webm",  # or audio/m4a, audio/opus
        headers={
            "Content-Disposition": f'attachment; filename="{cached_audio["filename"]}"',
            "X-Audio-Duration": str(cached_audio["metadata"].get("duration", 0)),
            "X-Video-Title": cached_audio["metadata"].get("title", "Unknown")
        }
    )


@router.post("/debug/transcribe/{job_id}", status_code=status.HTTP_200_OK)
async def debug_transcribe(
    job_id: str,
    data: TranscriptionCreate,
    current_user: User = Depends(get_current_user),
    service: TranscriptionService = Depends(get_transcription_service)
):
    """
    Direct transcription endpoint for debugging (synchronous, waits for completion)
    
    This endpoint processes the transcription synchronously and returns the result.
    Use the WebSocket endpoint /debug/{job_id} to receive real-time updates.
    
    IMPORTANT: Connect to WebSocket BEFORE calling this endpoint!
    
    WARNING: This endpoint can take 30-60 seconds to complete.
    """
    _require_debug_access(current_user)
    import structlog
    from app.transcription import YouTubeService, AssemblyAIService
    from app.transcription.debug_logger import start_debug_session, end_debug_session
    from app.transcription.audio_cache import get_audio_cache
    import shutil
    import asyncio
    
    logger = structlog.get_logger()
    
    try:
        # Start debug session with the provided job_id (WebSocket enabled)
        debug = start_debug_session(job_id, data.video_url, websocket_enabled=True)
        audio_cache = get_audio_cache()
        
        logger.info("debug_transcription_started", video_url=data.video_url, job_id=job_id, user_id=str(current_user.id))
        
        # Validate YouTube URL
        video_id = YouTubeService.extract_video_id(data.video_url)
        is_valid = video_id is not None
        debug.log_youtube_validation(is_valid, video_id)
        
        if not is_valid:
            raise ValueError(f"Invalid YouTube URL: {data.video_url}")
        
        # Download audio from YouTube
        audio_file, metadata = await asyncio.to_thread(
            YouTubeService.download_audio,
            data.video_url
        )
        
        # Detect language from metadata
        from app.transcription.language_detector import LanguageDetector
        detected_language = LanguageDetector.detect_language_from_metadata(metadata)
        
        # Log download complete with job_id and detected language
        import os
        file_size = os.path.getsize(audio_file)
        debug.log_youtube_download_complete(audio_file, file_size, metadata, job_id, detected_language)
        
        try:
            # Cache audio file for debug (30 minutes TTL)
            cached_audio_path = audio_cache.store_audio(
                job_id,
                audio_file,
                metadata,
                ttl_minutes=30
            )
            logger.info("audio_cached_for_debug", job_id=job_id, cached_path=cached_audio_path)
            
            # Transcribe using AssemblyAI with detected language (blocking call in thread)
            result = await asyncio.to_thread(
                AssemblyAIService.transcribe_audio,
                audio_file,
                detected_language  # Pass detected language
            )
            
            # Extract raw transcription
            raw_text = result["text"]
            confidence = result.get("confidence")
            
            # Improve transcription quality with AI Assistant
            logger.info(
                "ai_improvement_start",
                job_id=job_id,
                raw_text_length=len(raw_text),
                confidence=confidence
            )
            
            try:
                # Log AI Router start
                debug.log_ai_router_start(len(raw_text), detected_language)
                
                # 🆕 USE AI ROUTER for intelligent model selection
                from app.ai_assistant.service import AIAssistantService
                from app.ai_assistant.classification.model_selector import SelectionStrategy
                
                logger.info(
                    "ai_router_start",
                    job_id=job_id,
                    text_length=len(raw_text),
                    language=detected_language
                )
                
                # Use AI Router with COST_OPTIMIZED strategy (prefer free models)
                improved_result = await AIAssistantService.process_text_smart(
                    db=session,
                    text=raw_text,
                    task="improve_quality",
                    language=detected_language,
                    metadata={
                        "source": "youtube_transcription",
                        "job_id": job_id,
                        "confidence": confidence
                    },
                    strategy=SelectionStrategy.COST_OPTIMIZED,  # ✅ Prefer free models
                    provider_override=None  # Let router decide
                )
                
                improved_text = improved_result["processed_text"]
                
                # Extract router decisions
                classification = improved_result.get("classification", {})
                model_selection = improved_result.get("model_selection", {})
                
                # Log AI Router success
                debug.log_ai_router_complete(
                    raw_length=len(raw_text),
                    improved_length=len(improved_text),
                    domain=classification.get("primary_domain", "unknown"),
                    sensitivity=classification.get("sensitivity", {}).get("level", "low"),
                    model_used=model_selection.get("model", "unknown"),
                    strategy=model_selection.get("strategy_used", "unknown"),
                    confidence=classification.get("confidence", 0.0)
                )
                
                logger.info(
                    "ai_router_success",
                    job_id=job_id,
                    raw_length=len(raw_text),
                    improved_length=len(improved_text),
                    # Classification info
                    domain=classification.get("primary_domain"),
                    confidence=classification.get("confidence"),
                    sensitivity=classification.get("sensitivity", {}).get("level"),
                    # Model selection info
                    model_used=model_selection.get("model"),
                    strategy=model_selection.get("strategy_used"),
                    fallback=model_selection.get("fallback_used"),
                    # Performance
                    total_time_ms=improved_result.get("total_processing_time_ms"),
                    cost="FREE"  # ✅ Always free with COST_OPTIMIZED
                )
            except Exception as e:
                # Log AI Router failure
                debug.log_ai_router_failed(str(e))
                
                logger.warning(
                    "ai_improvement_failed",
                    job_id=job_id,
                    error=str(e),
                    fallback="using_raw_text"
                )
                improved_text = raw_text  # Fallback to raw text
            
            # Extract results
            final_result = {
                "text": improved_text,  # Use improved text
                "raw_text": raw_text,  # Keep original for comparison
                "confidence": confidence,
                "duration_seconds": result.get("audio_duration"),
                "job_id": job_id,
                "audio_available": True,
                "ai_improved": improved_text != raw_text
            }
            
            # End debug session
            end_debug_session()
            
            logger.info(
                "debug_transcription_complete",
                video_url=data.video_url,
                user_id=str(current_user.id),
                text_length=len(final_result["text"]),
                job_id=job_id
            )
            
            return final_result
            
        finally:
            # Cleanup: Delete temporary audio file (original download, not cache)
            try:
                temp_dir = os.path.dirname(audio_file)
                shutil.rmtree(temp_dir)
                logger.info("temp_audio_cleanup", temp_dir=temp_dir)
                debug.log_cleanup(temp_dir, True)
            except Exception as e:
                logger.warning("temp_audio_cleanup_failed", error=str(e))
                debug.log_cleanup(temp_dir, False)
                
    except Exception as e:
        logger.error(
            "debug_transcription_failed",
            video_url=data.video_url,
            user_id=str(current_user.id),
            error=str(e),
            job_id=job_id
        )
        
        # Log error to debug session
        try:
            from app.transcription.debug_logger import get_debug_logger
            debug = get_debug_logger()
            if debug:
                debug.log_error("TRANSCRIPTION_ERROR", e)
            end_debug_session()
        except Exception:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/debug/run-backend-test", status_code=status.HTTP_200_OK)
async def run_backend_test(
    current_user: User = Depends(get_current_user)
):
    """
    Run the complete backend-only transcription test.
    
    This endpoint executes the Python test script (test_transcription_complete.py)
    and returns the full output including all steps and results.
    
    WARNING: This can take 30-60 seconds to complete.
    """
    _require_debug_access(current_user)
    import structlog
    import subprocess
    import json
    from datetime import datetime
    
    logger = structlog.get_logger()
    
    try:
        logger.info(
            "backend_test_start",
            user_id=str(current_user.id),
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Run the test script
        result = subprocess.run(
            ["python", "test_transcription_complete.py"],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes max
        )
        
        # Parse output
        output = result.stdout
        error = result.stderr
        exit_code = result.returncode
        
        success = exit_code == 0
        
        logger.info(
            "backend_test_complete",
            user_id=str(current_user.id),
            success=success,
            exit_code=exit_code,
            output_length=len(output)
        )
        
        return {
            "success": success,
            "exit_code": exit_code,
            "output": output,
            "error": error if error else None,
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": None  # Could be parsed from output
        }
        
    except subprocess.TimeoutExpired:
        logger.error(
            "backend_test_timeout",
            user_id=str(current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Test execution timeout (max 2 minutes)"
        )
    except Exception as e:
        logger.error(
            "backend_test_error",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test execution failed: {str(e)}"
        )

