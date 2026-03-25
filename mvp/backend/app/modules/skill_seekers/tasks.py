"""
Celery tasks for Skill Seekers scrape job processing.

Provides persistence across restarts and automatic retry with exponential backoff.
Falls back to BackgroundTasks if Celery workers are unavailable.
"""

import asyncio

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


async def _process_scrape_job(job_id: str):
    """Async implementation of scrape job processing."""
    from uuid import UUID
    from app.modules.skill_seekers.service import SkillSeekersService

    service = SkillSeekersService()
    await service.run_job(UUID(job_id))
    return {"status": "completed", "job_id": job_id}


@celery_app.task(
    bind=True,
    name="skill_seekers.process",
    max_retries=2,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def process_scrape_job_task(self, job_id: str):
    """
    Celery task for processing skill_seekers scrape jobs.

    Retries up to 2 times with exponential backoff on failure.
    """
    logger.info(
        "celery_task_started",
        task="skill_seekers.process",
        job_id=job_id,
        attempt=self.request.retries + 1,
    )
    return _run_async(_process_scrape_job(job_id))
