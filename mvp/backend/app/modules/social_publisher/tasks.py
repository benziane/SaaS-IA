"""
Celery tasks for social_publisher scheduled post publishing.

Provides a periodic task that finds posts with status=SCHEDULED whose
scheduled_at time has passed and publishes them.
"""

import asyncio
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


async def _publish_scheduled_posts():
    """Find all due scheduled posts and publish them."""
    from uuid import UUID
    from sqlmodel import select
    from app.database import get_session_context
    from app.models.social_publisher import PostStatus, SocialPost
    from app.modules.social_publisher.service import SocialPublisherService

    now = datetime.now(UTC)
    published_count = 0
    failed_count = 0

    async with get_session_context() as session:
        result = await session.execute(
            select(SocialPost).where(
                SocialPost.status == PostStatus.SCHEDULED,
                SocialPost.schedule_at <= now,
            )
        )
        posts = list(result.scalars().all())

        if not posts:
            logger.debug("social_scheduled_publish_none_due")
            return {"published": 0, "failed": 0, "total_due": 0}

        logger.info("social_scheduled_publish_starting", total_due=len(posts))

        for post in posts:
            try:
                await SocialPublisherService.publish_post(
                    user_id=post.user_id,
                    post_id=post.id,
                    session=session,
                )
                published_count += 1
                logger.info(
                    "social_scheduled_post_published",
                    post_id=str(post.id),
                )
            except Exception as e:
                failed_count += 1
                logger.error(
                    "social_scheduled_post_failed",
                    post_id=str(post.id),
                    error=str(e)[:500],
                )

    return {
        "published": published_count,
        "failed": failed_count,
        "total_due": len(posts),
    }


@celery_app.task(
    bind=True,
    name="social_publisher.publish_scheduled",
    max_retries=1,
    default_retry_delay=30,
)
def publish_scheduled_posts_task(self):
    """
    Celery task that publishes all scheduled posts whose scheduled_at <= now.

    Designed to be called periodically via Celery Beat (e.g. every 60 seconds).
    """
    logger.info(
        "celery_task_started",
        task="social_publisher.publish_scheduled",
        attempt=self.request.retries + 1,
    )
    try:
        return _run_async(_publish_scheduled_posts())
    except Exception as e:
        logger.error(
            "social_scheduled_publish_task_error",
            error=str(e),
        )
        raise self.retry(exc=e)
