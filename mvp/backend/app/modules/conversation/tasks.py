"""
Celery tasks for conversation module.

Placeholder for future async AI processing tasks.
"""

from app.celery_app import celery_app

import structlog

logger = structlog.get_logger()


@celery_app.task(name="conversation.process_ai_response")
def process_ai_response_task(conversation_id: str, message_content: str):
    """
    Optional async AI response processing.

    Currently a placeholder for future use when conversation AI processing
    needs to be moved to background workers.
    """
    logger.info(
        "conversation_async_task",
        conversation_id=conversation_id,
        note="placeholder_for_future_use",
    )
    return {"status": "not_implemented", "conversation_id": conversation_id}
