"""
Structlog processor that injects request-scoped context variables.

Kept in a separate module from request_id.py so that the middleware
itself has zero dependency on structlog (separation of concerns).
"""

from typing import Any

from structlog.types import EventDict

from app.middleware.request_id import current_user_id_ctx, request_id_ctx


def inject_context_vars(
    logger: Any, method: str, event_dict: EventDict
) -> EventDict:
    """
    Structlog processor: adds ``request_id`` and ``user_id`` from
    contextvars into every log event dict.

    * ``request_id`` is added whenever it is non-empty.
    * ``user_id`` is added only when it differs from the default
      ``"anonymous"`` value, keeping logs clean for unauthenticated
      requests.
    """
    rid = request_id_ctx.get()
    if rid:
        event_dict["request_id"] = rid

    uid = current_user_id_ctx.get()
    if uid and uid != "anonymous":
        event_dict["user_id"] = uid

    return event_dict
