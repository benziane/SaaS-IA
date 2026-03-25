"""
Celery application configuration for SaaS-IA.

Uses Redis as both broker and result backend.
Auto-discovers tasks in app.modules.*.tasks.
"""

import os

from celery import Celery

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
)

# Auto-discover tasks in all module packages
celery_app.autodiscover_tasks([
    "app.modules.transcription",
    "app.modules.conversation",
    "app.modules.skill_seekers",
])
