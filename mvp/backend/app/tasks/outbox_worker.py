"""
Celery tasks for the Transactional Outbox pattern.

- ``process_outbox``: runs every 5 seconds via Celery beat, polls
  ``outbox_events`` for pending rows and dispatches them.
- ``cleanup_outbox``: runs daily, removes processed/dead events older
  than 30 days.
"""

import asyncio

import structlog

from app.celery_app import celery_app

logger = structlog.get_logger()


def _run_async(coro):
    """Run an async coroutine from synchronous Celery task context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="outbox.process", bind=True, max_retries=0)
def process_outbox(self):
    """Poll outbox_events and dispatch pending events.

    Scheduled via Celery beat every 5 seconds.
    """
    from app.core.outbox import OutboxService

    try:
        count = _run_async(OutboxService.process_pending(batch_size=100))
        if count:
            logger.info("outbox_batch_processed", count=count)
        return count
    except Exception as exc:
        logger.error("outbox_process_error", error=str(exc))
        raise


@celery_app.task(name="outbox.cleanup", bind=True, max_retries=0)
def cleanup_outbox(self):
    """Remove old processed/dead outbox events.

    Scheduled via Celery beat once per day.
    """
    from app.core.outbox import OutboxService

    try:
        deleted = _run_async(OutboxService.cleanup(days=30))
        logger.info("outbox_cleanup_done", deleted=deleted)
        return deleted
    except Exception as exc:
        logger.error("outbox_cleanup_error", error=str(exc))
        raise
