"""
Database-specific integration tests.

Tests Alembic migrations, table structure, indexes, foreign keys,
and connection pool behavior.
"""

import asyncio

import pytest
from sqlalchemy import text, inspect
from sqlmodel import SQLModel

from tests.integration.conftest import USE_REAL_DB


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestDatabaseSchema:
    """Verify database schema is correctly created."""

    @pytest.mark.asyncio
    async def test_tables_created(self, db_engine):
        """All core tables should exist after create_all."""
        async with db_engine.connect() as conn:
            if USE_REAL_DB:
                result = await conn.execute(
                    text(
                        "SELECT tablename FROM pg_tables "
                        "WHERE schemaname = 'public' "
                        "ORDER BY tablename"
                    )
                )
                tables = {row[0] for row in result.fetchall()}
            else:
                # SQLite: query sqlite_master
                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                tables = {row[0] for row in result.fetchall()}

        # Core tables that must exist
        expected_core = {"users", "tenants", "transcriptions", "conversations"}
        missing = expected_core - tables
        assert not missing, f"Missing core tables: {missing}"

    @pytest.mark.asyncio
    async def test_users_table_columns(self, db_engine):
        """The users table should have the expected columns."""
        async with db_engine.connect() as conn:
            if USE_REAL_DB:
                result = await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'users' ORDER BY ordinal_position"
                    )
                )
                columns = {row[0] for row in result.fetchall()}
            else:
                result = await conn.execute(text("PRAGMA table_info(users)"))
                columns = {row[1] for row in result.fetchall()}

        expected = {"id", "email", "hashed_password", "role", "is_active"}
        missing = expected - columns
        assert not missing, f"Missing columns in users: {missing}"

    @pytest.mark.asyncio
    async def test_transcriptions_table_columns(self, db_engine):
        """The transcriptions table should have the expected columns."""
        async with db_engine.connect() as conn:
            if USE_REAL_DB:
                result = await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'transcriptions' ORDER BY ordinal_position"
                    )
                )
                columns = {row[0] for row in result.fetchall()}
            else:
                result = await conn.execute(text("PRAGMA table_info(transcriptions)"))
                columns = {row[1] for row in result.fetchall()}

        expected = {"id", "user_id", "video_url", "status", "text"}
        missing = expected - columns
        assert not missing, f"Missing columns in transcriptions: {missing}"

    @pytest.mark.asyncio
    @pytest.mark.skipif(not USE_REAL_DB, reason="Index inspection requires PostgreSQL")
    async def test_indexes_exist(self, db_engine):
        """Key indexes should exist on PostgreSQL."""
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE schemaname = 'public' "
                    "ORDER BY indexname"
                )
            )
            indexes = {row[0] for row in result.fetchall()}

        # At minimum, primary key indexes should exist
        assert any("users" in idx for idx in indexes), "No index found for users table"
        assert any("transcription" in idx for idx in indexes), "No index found for transcriptions table"

    @pytest.mark.asyncio
    @pytest.mark.skipif(not USE_REAL_DB, reason="FK inspection requires PostgreSQL")
    async def test_foreign_keys_valid(self, db_engine):
        """Foreign key constraints should reference existing tables."""
        async with db_engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT tc.table_name, kcu.column_name, "
                    "ccu.table_name AS foreign_table "
                    "FROM information_schema.table_constraints tc "
                    "JOIN information_schema.key_column_usage kcu "
                    "  ON tc.constraint_name = kcu.constraint_name "
                    "JOIN information_schema.constraint_column_usage ccu "
                    "  ON tc.constraint_name = ccu.constraint_name "
                    "WHERE tc.constraint_type = 'FOREIGN KEY'"
                )
            )
            fks = result.fetchall()

        # Verify that referenced tables exist
        existing_result = await db_engine.connect()
        async with db_engine.connect() as conn:
            tbl_result = await conn.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public'"
                )
            )
            existing_tables = {row[0] for row in tbl_result.fetchall()}

        for table_name, column_name, foreign_table in fks:
            assert foreign_table in existing_tables, (
                f"FK {table_name}.{column_name} references non-existent table {foreign_table}"
            )


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

class TestDatabaseCRUD:
    """Verify basic CRUD operations work on the database."""

    @pytest.mark.asyncio
    async def test_create_and_read_user(self, session):
        """Create a user and read it back."""
        from app.models.user import User, Role
        from uuid import uuid4

        user = User(
            id=uuid4(),
            email=f"crud_test_{uuid4().hex[:8]}@test.com",
            hashed_password="$2b$12$test_hash",
            full_name="CRUD Test",
            role=Role.USER,
            is_active=True,
            email_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        assert user.id is not None
        assert user.email.startswith("crud_test_")

    @pytest.mark.asyncio
    async def test_create_and_read_transcription(self, session, test_user_in_db):
        """Create a transcription linked to a user."""
        from app.models.transcription import Transcription, TranscriptionStatus

        t = Transcription(
            user_id=test_user_in_db.id,
            video_url="https://youtube.com/watch?v=test123",
            language="en",
            status=TranscriptionStatus.PENDING,
        )
        session.add(t)
        await session.commit()
        await session.refresh(t)

        assert t.id is not None
        assert t.user_id == test_user_in_db.id
        assert t.status == TranscriptionStatus.PENDING

    @pytest.mark.asyncio
    async def test_update_user(self, session, test_user_in_db):
        """Update a user's full name."""
        test_user_in_db.full_name = "Updated Name"
        session.add(test_user_in_db)
        await session.commit()
        await session.refresh(test_user_in_db)

        assert test_user_in_db.full_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_user(self, session):
        """Create and delete a user."""
        from app.models.user import User, Role
        from uuid import uuid4
        from sqlmodel import select

        user = User(
            id=uuid4(),
            email=f"delete_test_{uuid4().hex[:8]}@test.com",
            hashed_password="$2b$12$test_hash",
            role=Role.USER,
            is_active=True,
            email_verified=True,
        )
        session.add(user)
        await session.commit()

        user_id = user.id
        await session.delete(user)
        await session.commit()

        result = await session.execute(select(User).where(User.id == user_id))
        assert result.scalar_one_or_none() is None


# ---------------------------------------------------------------------------
# Connection pool
# ---------------------------------------------------------------------------

class TestPooling:
    """Verify connection pool behavior."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not USE_REAL_DB, reason="Pool metrics require PostgreSQL engine")
    async def test_pool_metrics(self, db_engine):
        """Pool metrics should be retrievable."""
        pool = db_engine.pool
        try:
            size = pool.size()
            checked_in = pool.checkedin()
            checked_out = pool.checkedout()
            overflow = pool.overflow()
            assert size >= 0
            assert checked_in >= 0
            assert checked_out >= 0
        except AttributeError:
            pytest.skip("Pool does not support metrics (NullPool)")

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, db_engine):
        """Multiple concurrent sessions should work without deadlock."""
        from sqlalchemy.orm import sessionmaker
        from sqlmodel.ext.asyncio.session import AsyncSession
        from sqlmodel import select
        from app.models.user import User

        factory = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

        async def run_query(n):
            async with factory() as sess:
                result = await sess.execute(select(User).limit(1))
                return n

        results = await asyncio.gather(*[run_query(i) for i in range(5)])
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_session_isolation(self, db_engine):
        """Changes in one session should not leak into another before commit."""
        from sqlalchemy.orm import sessionmaker
        from sqlmodel.ext.asyncio.session import AsyncSession
        from sqlmodel import select
        from app.models.user import User, Role
        from uuid import uuid4

        factory = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

        unique_email = f"isolation_{uuid4().hex}@test.com"

        # Session 1: add user but don't commit
        async with factory() as s1:
            user = User(
                id=uuid4(),
                email=unique_email,
                hashed_password="$2b$12$hash",
                role=Role.USER,
                is_active=True,
                email_verified=True,
            )
            s1.add(user)
            # Do NOT commit

            # Session 2: should NOT see the uncommitted user
            async with factory() as s2:
                result = await s2.execute(
                    select(User).where(User.email == unique_email)
                )
                found = result.scalar_one_or_none()
                # In SQLite, same file = same view, but in-memory each session is isolated
                # In PostgreSQL, default read committed isolation means s2 won't see s1's uncommitted data
                if USE_REAL_DB:
                    assert found is None, "Uncommitted data leaked between sessions"

            # Rollback s1
            await s1.rollback()


# ---------------------------------------------------------------------------
# Migrations (PostgreSQL only)
# ---------------------------------------------------------------------------

class TestMigrations:
    """Verify Alembic migrations can be applied."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(not USE_REAL_DB, reason="Alembic migrations require PostgreSQL")
    async def test_current_revision(self):
        """Alembic should report a current revision."""
        import subprocess
        import os

        backend_dir = os.path.join(os.path.dirname(__file__), "..", "..")
        result = subprocess.run(
            ["python", "-m", "alembic", "current"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should not error
        assert result.returncode == 0, f"alembic current failed: {result.stderr}"

    @pytest.mark.asyncio
    @pytest.mark.skipif(not USE_REAL_DB, reason="Alembic migrations require PostgreSQL")
    async def test_migration_history(self):
        """Alembic should have a non-empty migration history."""
        import subprocess
        import os

        backend_dir = os.path.join(os.path.dirname(__file__), "..", "..")
        result = subprocess.run(
            ["python", "-m", "alembic", "history", "--verbose"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"alembic history failed: {result.stderr}"
        # Should output at least one revision
        assert len(result.stdout.strip()) > 0
