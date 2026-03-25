"""
Celery tasks for transcription processing.

These tasks replace the BackgroundTasks-based processing, providing
persistence across restarts and automatic retry with exponential backoff.
"""

import asyncio
import os
from datetime import UTC, datetime

import structlog

from app.celery_app import celery_app

logger = structlog.get_logger()


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _process_transcription(job_id: str, video_url: str, language: str, source_type: str):
    """Async implementation of transcription processing."""
    from uuid import UUID
    from app.database import get_session_context
    from app.models.transcription import Transcription, TranscriptionStatus
    from app.modules.transcription.service import TranscriptionService
    from app.metrics import transcription_jobs_total

    service = TranscriptionService()

    async with get_session_context() as session:
        job = await session.get(Transcription, UUID(job_id))
        if not job:
            logger.error("celery_transcription_job_not_found", job_id=job_id)
            return {"status": "not_found"}

        try:
            job.status = TranscriptionStatus.PROCESSING
            job.updated_at = datetime.now(UTC)
            await session.commit()

            logger.info(
                "celery_transcription_processing",
                job_id=job_id,
                video_url=video_url,
            )

            if service.mock_mode:
                result = await service._mock_transcribe(video_url)
            else:
                result = await service._real_transcribe(video_url)

            job.status = TranscriptionStatus.COMPLETED
            job.text = result["text"]
            job.confidence = result.get("confidence", 0.95)
            job.duration_seconds = result.get("duration_seconds", 180)
            job.completed_at = datetime.now(UTC)
            job.updated_at = datetime.now(UTC)
            await session.commit()

            transcription_jobs_total.labels(status="completed").inc()

            logger.info(
                "celery_transcription_completed",
                job_id=job_id,
                text_length=len(result["text"]),
            )
            return {"status": "completed", "job_id": job_id}

        except Exception as e:
            job.status = TranscriptionStatus.FAILED
            job.error = str(e)[:1000]
            job.retry_count += 1
            job.updated_at = datetime.now(UTC)
            await session.commit()

            transcription_jobs_total.labels(status="failed").inc()

            logger.error(
                "celery_transcription_failed",
                job_id=job_id,
                error=str(e),
            )
            raise


async def _process_upload(job_id: str, file_path: str, language: str):
    """Async implementation of upload transcription processing."""
    from uuid import UUID
    from app.database import get_session_context
    from app.models.transcription import Transcription, TranscriptionStatus
    from app.modules.transcription.service import TranscriptionService
    from app.metrics import transcription_jobs_total

    service = TranscriptionService()

    async with get_session_context() as session:
        job = await session.get(Transcription, UUID(job_id))
        if not job:
            logger.error("celery_upload_job_not_found", job_id=job_id)
            return {"status": "not_found"}

        try:
            job.status = TranscriptionStatus.PROCESSING
            job.updated_at = datetime.now(UTC)
            await session.commit()

            logger.info(
                "celery_upload_processing",
                job_id=job_id,
                file_path=file_path,
            )

            if service.mock_mode:
                result = await service._mock_transcribe(file_path)
            else:
                result = await service._real_transcribe_file(file_path, language)

            job.status = TranscriptionStatus.COMPLETED
            job.text = result["text"]
            job.confidence = result.get("confidence", 0.95)
            job.duration_seconds = result.get("duration_seconds", 0)
            job.completed_at = datetime.now(UTC)
            job.updated_at = datetime.now(UTC)
            await session.commit()

            transcription_jobs_total.labels(status="completed").inc()

            logger.info(
                "celery_upload_completed",
                job_id=job_id,
                text_length=len(result["text"]),
            )
            return {"status": "completed", "job_id": job_id}

        except Exception as e:
            job.status = TranscriptionStatus.FAILED
            job.error = str(e)[:1000]
            job.retry_count += 1
            job.updated_at = datetime.now(UTC)
            await session.commit()

            transcription_jobs_total.labels(status="failed").inc()

            logger.error(
                "celery_upload_failed",
                job_id=job_id,
                error=str(e),
            )
            raise
        finally:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info("celery_upload_temp_cleaned", file_path=file_path)
            except Exception as e:
                logger.warning("celery_upload_cleanup_failed", error=str(e))


@celery_app.task(
    bind=True,
    name="transcription.process",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def process_transcription_task(self, job_id: str, video_url: str, language: str = "auto", source_type: str = "youtube"):
    """
    Celery task for processing URL-based transcriptions.

    Retries up to 3 times with exponential backoff on failure.
    """
    logger.info(
        "celery_task_started",
        task="process_transcription",
        job_id=job_id,
        attempt=self.request.retries + 1,
    )
    return _run_async(_process_transcription(job_id, video_url, language, source_type))


@celery_app.task(
    bind=True,
    name="transcription.process_upload",
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
)
def process_upload_task(self, job_id: str, file_path: str, language: str = "auto"):
    """
    Celery task for processing file upload transcriptions.

    Cleans up temporary files in the finally block regardless of outcome.
    Retries up to 3 times with exponential backoff.
    """
    logger.info(
        "celery_task_started",
        task="process_upload",
        job_id=job_id,
        attempt=self.request.retries + 1,
    )
    return _run_async(_process_upload(job_id, file_path, language))
