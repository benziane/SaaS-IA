"""
OpenTelemetry setup for the SaaS-IA platform.

Provides distributed tracing with automatic instrumentation for FastAPI,
AsyncPG, Redis, and HTTPX. Uses ConsoleSpanExporter in development and
OTLPSpanExporter in production.

All opentelemetry imports are wrapped in try/except ImportError so the
application starts normally when the otel packages are not installed.

Usage (in lifespan or main.py):
    from app.core.telemetry import setup_telemetry, shutdown_telemetry

    setup_telemetry(app)
    # ... on shutdown ...
    shutdown_telemetry()
"""

import os

import structlog

from app.config import settings

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Graceful degradation: opentelemetry is optional
# ---------------------------------------------------------------------------

HAS_OTEL = False

try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )

    HAS_OTEL = True
except ImportError:
    pass


def _create_resource() -> "Resource | None":
    """Build an OTEL Resource describing this service."""
    if not HAS_OTEL:
        return None

    version = getattr(settings, "APP_VERSION", None) or os.getenv("APP_VERSION", "1.0.0")
    environment = settings.ENVIRONMENT

    return Resource.create(
        {
            "service.name": "saas-ia",
            "service.version": version,
            "deployment.environment": environment,
        }
    )


def _setup_tracing(resource: "Resource") -> None:
    """Configure the global TracerProvider with the appropriate exporter."""
    provider = TracerProvider(resource=resource)

    is_production = settings.ENVIRONMENT.lower() == "production"

    if is_production:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
            exporter = OTLPSpanExporter(endpoint=endpoint)
        except ImportError:
            logger.warning(
                "otlp_exporter_unavailable",
                msg="opentelemetry-exporter-otlp-proto-grpc not installed, "
                    "falling back to ConsoleSpanExporter",
            )
            exporter = ConsoleSpanExporter()
    else:
        exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def setup_telemetry(app) -> None:
    """
    Main entry point: initialise OpenTelemetry tracing and instrument
    the FastAPI application plus database / cache / HTTP clients.

    Safe to call even when opentelemetry is not installed.
    """
    if not HAS_OTEL:
        logger.info("telemetry_skipped", reason="opentelemetry not installed")
        return

    resource = _create_resource()
    _setup_tracing(resource)

    # ── FastAPI ──────────────────────────────────────────────────────────
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health/.*,metrics",
        )
    except ImportError:
        logger.debug("otel_instrument_skip", target="fastapi")

    # ── AsyncPG ──────────────────────────────────────────────────────────
    try:
        from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

        AsyncPGInstrumentor().instrument()
    except ImportError:
        logger.debug("otel_instrument_skip", target="asyncpg")

    # ── Redis ────────────────────────────────────────────────────────────
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
    except ImportError:
        logger.debug("otel_instrument_skip", target="redis")

    # ── HTTPX ────────────────────────────────────────────────────────────
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
    except ImportError:
        logger.debug("otel_instrument_skip", target="httpx")

    logger.info(
        "telemetry_initialized",
        environment=settings.ENVIRONMENT,
    )


def shutdown_telemetry() -> None:
    """Flush pending spans and shut down the tracer provider."""
    if not HAS_OTEL:
        return

    provider = trace.get_tracer_provider()
    if hasattr(provider, "force_flush"):
        try:
            provider.force_flush(timeout_millis=5000)
        except Exception as exc:
            logger.warning("telemetry_flush_error", error=str(exc))

    if hasattr(provider, "shutdown"):
        try:
            provider.shutdown()
        except Exception as exc:
            logger.warning("telemetry_shutdown_error", error=str(exc))

    logger.info("telemetry_shutdown_complete")
