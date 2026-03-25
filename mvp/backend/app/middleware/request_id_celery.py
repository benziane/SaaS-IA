"""
Celery signal handlers for request ID propagation across task boundaries.

When a task is published from within a web request, the current request ID
is injected into the task message headers. When the worker picks up the
task, the request ID is restored into the worker's contextvars so that
all log entries emitted during task execution carry the same correlation ID.
"""

import structlog
from celery import signals

from app.middleware.request_id import get_request_id, request_id_ctx

_REQUEST_ID_HEADER = "x_request_id"


@signals.before_task_publish.connect
def inject_request_id_header(
    headers: dict | None = None, **kwargs
) -> None:
    """Inject the current request ID into outgoing task headers."""
    if headers is None:
        return

    rid = get_request_id()
    if rid:
        headers[_REQUEST_ID_HEADER] = rid


@signals.task_prerun.connect
def restore_request_id(task_id: str | None = None, task: object | None = None, **kwargs) -> None:
    """
    Restore the request ID from task headers in the worker process
    and bind it to structlog context for the duration of the task.
    """
    rid = ""

    # Celery stores custom headers on the task request object
    if task is not None:
        request = getattr(task, "request", None)
        if request is not None:
            # Headers can be in request.headers or request meta depending on version
            headers = getattr(request, "headers", None) or {}
            rid = headers.get(_REQUEST_ID_HEADER, "")

            # Fallback: some Celery versions put custom headers directly on request
            if not rid:
                rid = getattr(request, _REQUEST_ID_HEADER, "") or ""

    request_id_ctx.set(rid)

    if rid:
        structlog.contextvars.bind_contextvars(request_id=rid, task_id=task_id)
    elif task_id:
        structlog.contextvars.bind_contextvars(task_id=task_id)


@signals.task_postrun.connect
def clear_request_id(task_id: str | None = None, **kwargs) -> None:
    """Clear the request ID and structlog context after task execution."""
    request_id_ctx.set("")
    structlog.contextvars.clear_contextvars()
