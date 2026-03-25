"""
SaaS-IA MVP - FastAPI Application (Enterprise S+++)

Main entry point for the API.
Middleware stack: CORS -> RequestID -> ShutdownGuard -> Sentry -> RateLimit -> Logging -> Security -> Compression -> Prometheus
"""

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from slowapi.errors import RateLimitExceeded
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.auth import get_current_user, router as auth_router
from app.ai_assistant.routes import router as ai_assistant_router
from app.rate_limit import limiter, rate_limit_exceeded_handler
from app.metrics import PrometheusMiddleware
from app.modules import ModuleRegistry

# --- Phase 1: Logging (BEFORE any other import that uses structlog) ---
from app.core.logging_config import configure_logging
configure_logging()

# --- Phase 6b: Error tracking (early, to catch startup errors) ---
from app.core.error_tracking import init_error_tracking
init_error_tracking()

logger = structlog.get_logger()

# --- Phase 3: Lifespan with graceful shutdown ---
from app.core.lifecycle import lifespan

# HIGH-04: Disable Swagger/ReDoc in production to prevent information disclosure
_is_production = settings.ENVIRONMENT == "production"

# Create FastAPI app with enterprise lifespan
app = FastAPI(
    title=settings.APP_NAME,
    description="Plateforme SaaS modulaire d'intelligence artificielle - Version MVP",
    version="1.0.0",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    lifespan=lifespan,
)

# --- OpenAPI enrichment (tags, servers, security schemes) ---
from app.api.docs import custom_openapi, TAGS_METADATA
app.openapi_tags = TAGS_METADATA
app.openapi = lambda: custom_openapi(app)

# --- Phase 6a: OpenTelemetry (must be after app creation) ---
from app.core.telemetry import setup_telemetry
setup_telemetry(app)

# Add rate limiting (existing - kept as-is)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ============================================================
# MIDDLEWARE STACK (Starlette executes in REVERSE add order)
# First added = last executed on request, first on response
# ============================================================

# 8. Prometheus metrics (outermost - wraps everything)
app.add_middleware(PrometheusMiddleware)

# 7. Compression (compresses final response, skips SSE/metrics)
from app.middleware.compression import SelectiveCompressionMiddleware
app.add_middleware(SelectiveCompressionMiddleware)

# 6. Security Headers (HSTS, CSP, X-Frame-Options, etc.)
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# 5b. Sliding Window Rate Limiter (global, coexists with per-endpoint slowapi)
from app.middleware.rate_limiter import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# 5. Request Logging (timing + user_id + status-based log level)
from app.middleware.logging_middleware import RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)

# 4. Sentry Context (enriches error reports with request context)
from app.middleware.sentry_context import SentryContextMiddleware
app.add_middleware(SentryContextMiddleware)

# 3. Shutdown Guard (returns 503 during graceful shutdown)
from app.middleware.shutdown_guard import ShutdownGuardMiddleware
app.add_middleware(ShutdownGuardMiddleware)

# 2. Request ID (generates/propagates X-Request-ID - everything depends on this)
from app.middleware.request_id import RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)

# 1. CORS (must be first executed for preflight OPTIONS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import Celery request_id signals (auto-registers on import)
# NOTE: Using importlib to avoid `import app.middleware.request_id_celery`
# which would rebind the name `app` in this module to the `app` package,
# overwriting the FastAPI instance assigned above.
import importlib as _importlib
_importlib.import_module("app.middleware.request_id_celery")

# Include routers
app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    ai_assistant_router,
    prefix="/api/ai-assistant",
    tags=["AI Assistant"]
)

# Auto-discover and register plugin modules
registered = ModuleRegistry.discover_modules(app)
logger.info(
    "modules_registered",
    count=len(registered),
    modules=[m["name"] for m in registered],
)

# Enterprise health checks (Kubernetes-ready: /health/live, /health/ready, /health/startup)
from app.api.health import router as health_router, mark_startup_complete
app.include_router(health_router)
mark_startup_complete([m["name"] for m in registered])

# Public API v1 routes (API key authentication)
from app.modules.api_keys.public_routes import router as public_api_router
app.include_router(
    public_api_router,
    prefix="/v1",
    tags=["Public API v1"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
@limiter.limit("100/minute")
async def health_check(request: Request):
    """
    Health check endpoint
    
    Returns the health status of the application
    
    Rate limit: 100 requests/minute
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


# Registered modules endpoint (HIGH-05: require authentication)
@app.get("/api/modules", tags=["Modules"])
async def list_modules(current_user=Depends(get_current_user)):
    """
    List all registered plugin modules.

    Returns metadata for every module that was successfully discovered
    and loaded at startup. Requires authentication.
    """
    modules = ModuleRegistry.get_registered_modules()
    return {
        "count": len(modules),
        "modules": modules,
    }


# Prometheus metrics endpoint
@app.get("/metrics", tags=["Monitoring"], include_in_schema=False)
async def metrics(request: Request):
    """
    Expose Prometheus metrics in text format.

    Access is restricted: the endpoint is available when ENVIRONMENT is
    ``development``, or when the request carries a valid
    ``X-Metrics-Token`` header matching the METRICS_TOKEN setting.
    """
    is_dev = settings.ENVIRONMENT == "development"
    token_valid = request.headers.get("X-Metrics-Token") == settings.metrics_token_resolved

    if not (is_dev or token_valid):
        return PlainTextResponse("Forbidden", status_code=403)

    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint
    
    Returns basic information about the API
    """
    return {
        "message": "Welcome to SaaS-IA MVP API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug_enabled
    )

