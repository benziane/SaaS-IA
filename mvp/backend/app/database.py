"""
Database configuration and session management
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

import structlog
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

logger = structlog.get_logger()

# Convert postgresql:// to postgresql+asyncpg://
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine with connection pool tuning
engine = create_async_engine(
    database_url,
    echo=settings.sql_echo_enabled,
    future=True,
    pool_size=50,
    max_overflow=25,
    pool_timeout=60,
    pool_recycle=3600,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "application_name": "saas_ia",
            "jit": "off",
            "statement_timeout": "30000",
        }
    },
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Import all models to register them
        from app.models.user import User, Role  # noqa: F401
        from app.models.tenant import Tenant  # noqa: F401
        from app.models.transcription import Transcription, TranscriptionStatus  # noqa: F401
        from app.models.conversation import Conversation, Message  # noqa: F401
        from app.models.billing import Plan, UserQuota  # noqa: F401
        from app.models.compare import ComparisonResult, ComparisonVote  # noqa: F401
        from app.models.pipeline import Pipeline, PipelineExecution  # noqa: F401
        from app.models.knowledge import Document, DocumentChunk  # noqa: F401
        from app.models.api_key import APIKey  # noqa: F401
        from app.models.workspace import Workspace, WorkspaceMember, SharedItem, Comment  # noqa: F401
        from app.models.agent import AgentRun, AgentStep  # noqa: F401
        from app.models.cost_tracking import AIUsageLog  # noqa: F401
        from app.models.skill_seekers import ScrapeJob, ScrapeJobStatus  # noqa: F401
        from app.models.notification import Notification  # noqa: F401
        from app.models.outbox import OutboxEvent  # noqa: F401
        from app.models.audit_log import AuditLogEntry  # noqa: F401
        from app.models.secrets_manager import SecretRegistration  # noqa: F401

        # Create all tables
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    
    Usage:
        @router.get("/")
        async def endpoint(session: AsyncSession = Depends(get_session)):
            ...
    """
    async with async_session() as session:
        yield session


@asynccontextmanager
async def get_session_context():
    """
    Context manager for database session

    Usage:
        async with get_session_context() as session:
            ...
    """
    async with async_session() as session:
        yield session


# ---------------------------------------------------------------------------
# Connection readiness check with retry
# ---------------------------------------------------------------------------

async def wait_for_db(max_retries: int = 5, base_delay: float = 1.0) -> None:
    """
    Wait for the database to become reachable using exponential backoff.

    Raises ``ConnectionError`` after *max_retries* failed attempts.
    """
    from sqlalchemy import text

    for attempt in range(1, max_retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("database_ready", attempt=attempt)
            return
        except Exception as exc:
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "database_not_ready",
                attempt=attempt,
                max_retries=max_retries,
                next_retry_in=delay,
                error=str(exc),
            )
            if attempt == max_retries:
                raise ConnectionError(
                    f"Database not reachable after {max_retries} attempts"
                ) from exc
            await asyncio.sleep(delay)


# ---------------------------------------------------------------------------
# Connection pool metrics
# ---------------------------------------------------------------------------

@dataclass
class PoolMetrics:
    """Snapshot of the connection-pool state."""
    size: int
    checked_in: int
    checked_out: int
    overflow: int

    @staticmethod
    def get_stats() -> Optional["PoolMetrics"]:
        """
        Return current pool statistics, or ``None`` if the pool is not
        available (e.g. NullPool).
        """
        pool = engine.pool
        try:
            return PoolMetrics(
                size=pool.size(),
                checked_in=pool.checkedin(),
                checked_out=pool.checkedout(),
                overflow=pool.overflow(),
            )
        except AttributeError:
            return None

