"""
SaaS-IA MVP - FastAPI Application

Main entry point for the API
"""

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db
from app.auth import router as auth_router
from app.modules.transcription.routes import router as transcription_router
from app.ai_assistant.routes import router as ai_assistant_router
from app.rate_limit import limiter, rate_limit_exceeded_handler

# Initialize structured logger
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("application_startup", app_name=settings.APP_NAME, environment=settings.ENVIRONMENT)

    # Security checks for critical configuration
    _weak_default = "change-me-in-production-use-strong-random-key"
    if not settings.SECRET_KEY or settings.SECRET_KEY == _weak_default:
        logger.critical(
            "insecure_secret_key",
            msg="SECRET_KEY is missing or still set to the weak default. "
                "Set a strong random SECRET_KEY in your .env file before running in production.",
        )

    if not settings.DATABASE_URL:
        logger.critical(
            "missing_database_url",
            msg="DATABASE_URL is not configured. "
                "Set DATABASE_URL in your .env file.",
        )

    # Initialize database
    await init_db()
    logger.info("database_initialized")
    
    yield
    
    # Shutdown
    logger.info("application_shutdown")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Plateforme SaaS modulaire d'intelligence artificielle - Version MVP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    transcription_router,
    prefix="/api/transcription",
    tags=["Transcription"]
)

app.include_router(
    ai_assistant_router,
    prefix="/api/ai-assistant",
    tags=["AI Assistant"]
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
        reload=settings.DEBUG
    )

