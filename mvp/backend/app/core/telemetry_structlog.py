"""
Structlog processor that injects OpenTelemetry trace context into log events.

Adds ``trace_id`` and ``span_id`` fields to every log entry when a valid
span is active. This allows correlating log lines with distributed traces
in backends like Jaeger, Grafana Tempo, or Datadog.

Graceful: if opentelemetry is not installed the processor is a no-op.

Usage (in logging_config.py shared_processors):
    from app.core.telemetry_structlog import inject_trace_context

    shared_processors = [
        inject_trace_context,
        ...
    ]
"""

from typing import Any

from structlog.types import EventDict

# ---------------------------------------------------------------------------
# Graceful degradation
# ---------------------------------------------------------------------------

_HAS_OTEL = False

try:
    from opentelemetry import trace
    from opentelemetry.trace import INVALID_SPAN

    _HAS_OTEL = True
except ImportError:
    pass


def inject_trace_context(
    logger: Any, method: str, event_dict: EventDict
) -> EventDict:
    """
    Structlog processor: if an active OpenTelemetry span exists, inject
    ``trace_id`` and ``span_id`` into the log event dict.

    Trace ID is formatted as a 32-character lowercase hex string (032x).
    Span ID is formatted as a 16-character lowercase hex string (016x).
    """
    if not _HAS_OTEL:
        return event_dict

    span = trace.get_current_span()
    if span is None or span is INVALID_SPAN:
        return event_dict

    ctx = span.get_span_context()
    if ctx is None or not ctx.is_valid:
        return event_dict

    event_dict["trace_id"] = format(ctx.trace_id, "032x")
    event_dict["span_id"] = format(ctx.span_id, "016x")

    return event_dict
