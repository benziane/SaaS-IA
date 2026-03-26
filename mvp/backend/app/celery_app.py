"""
Celery application configuration for SaaS-IA.

Uses Redis as both broker and result backend.
Auto-discovers tasks in app.modules.*.tasks and app.tasks.
"""

import os

from celery import Celery
from celery.schedules import crontab

# Ensure settings can be loaded
_redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "saas_ia",
    broker=_redis_url,
    backend=_redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    # Celery beat schedule for periodic tasks
    beat_schedule={
        "outbox-process-pending": {
            "task": "outbox.process",
            "schedule": 5.0,  # every 5 seconds
        },
        "outbox-cleanup-old-events": {
            "task": "outbox.cleanup",
            "schedule": crontab(hour=3, minute=0),  # daily at 03:00 UTC
        },
        "secrets-check-rotations": {
            "task": "secrets.check_rotations",
            "schedule": crontab(hour=6, minute=0),  # daily at 06:00 UTC
        },
    },
)

# Auto-discover tasks in all module packages
celery_app.autodiscover_tasks([
    "app.modules.transcription",
    "app.modules.conversation",
    "app.modules.skill_seekers",
    "app.modules.social_publisher",
    "app.tasks",
])
