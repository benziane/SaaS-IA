"""
Enterprise structlog configuration for SaaS-IA.

JSON output in production, colored console in development.
Sensitive data filtering, environment tagging, stdlib integration.
"""

import logging
from typing import Any

import structlog
from structlog.types import EventDict

from app.config import settings
from app.middleware.request_id_structlog import inject_context_vars
from app.core.telemetry_structlog import inject_trace_context

SENSITIVE_KEYS: frozenset[str] = frozenset({
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "authorization",
    "cookie",
    "session_id",
    "credit_card",
    "ssn",
    "access_token",
    "refresh_token",
    "private_key",
})

_REDACTED = "***REDACTED***"


def _clean_value(value: Any) -> Any:
    """Recursively clean sensitive data from nested structures."""
    if isinstance(value, dict):
        return {
            k: (_REDACTED if k.lower() in SENSITIVE_KEYS else _clean_value(v))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        cleaned = [_clean_value(item) for item in value]
        return type(value)(cleaned) if isinstance(value, tuple) else cleaned
    return value


def filter_sensitive_data(
    logger: Any, method: str, event_dict: EventDict
) -> EventDict:
    """Structlog processor that redacts sensitive keys from log events."""
    for key in list(event_dict.keys()):
        if key.lower() in SENSITIVE_KEYS:
            event_dict[key] = _REDACTED
        else:
            event_dict[key] = _clean_value(event_dict[key])
    return event_dict


def add_environment(
    logger: Any, method: str, event_dict: EventDict
) -> EventDict:
    """Add service name and environment to every log entry."""
    event_dict["service"] = "saas-ia"
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict


def configure_logging() -> None:
    """Configure structlog and stdlib logging for the application."""

    is_production = settings.ENVIRONMENT.lower() == "production"
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Shared processors used by both structlog and stdlib
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        inject_context_vars,
        inject_trace_context,
        filter_sensitive_data,
        add_environment,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if is_production:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure stdlib root logger with structlog ProcessorFormatter
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Reduce noise from verbose third-party loggers
    for noisy_logger in (
        "uvicorn.access",
        "sqlalchemy.engine",
        "httpx",
        "httpcore",
    ):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(**initial_binds: Any) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger, optionally with initial context."""
    log: structlog.stdlib.BoundLogger = structlog.get_logger(**initial_binds)
    return log
