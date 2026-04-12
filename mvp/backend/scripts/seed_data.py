"""
Seed data script for SaaS-IA.

Creates demo data for development and testing:
- Admin user + demo user
- Default billing plans (Free, Pro, Enterprise)
- Sample transcriptions
- Sample pipeline
- Sample workspace

Usage:
    cd mvp/backend
    python -m scripts.seed_data

Or from Docker:
    docker exec saas-ia-backend python -m scripts.seed_data
"""

import asyncio
import logging
import os
import secrets
import string
import sys
from datetime import UTC, date, datetime
from uuid import uuid4

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

seed_logger = logging.getLogger("seed_data")


def _generate_random_password(length: int = 16) -> str:
    """Generate a secure random password with letters, digits, and punctuation."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        # Ensure at least one letter, one digit, one special char
        if (any(c.isalpha() for c in pwd)
                and any(c.isdigit() for c in pwd)
                and any(c in "!@#$%&*" for c in pwd)):
            return pwd


async def seed():
    """Seed the database with demo data."""
    from app.config import settings
    from app.database import init_db, get_session_context
    from app.auth import get_password_hash
    from app.models.user import User, Role
    from app.models.transcription import Transcription, TranscriptionStatus
    from app.models.billing import Plan, PlanName, UserQuota
    from app.models.pipeline import Pipeline, PipelineStatus
    from app.models.workspace import Workspace, WorkspaceMember, WorkspaceRole
    from sqlmodel import select
    import json

    # --- MED-06: Refuse to seed in production with hardcoded credentials ---
    environment = settings.ENVIRONMENT
    if environment == "production":
        print("WARNING: Running seed script in PRODUCTION environment.")
        print("Seed passwords will be randomly generated (not hardcoded defaults).")
        seed_logger.warning("seed_script_running_in_production")

    seed_logger.warning(
        "seed_data_executing: environment=%s - Seed data should only be used for development/testing.",
        environment,
    )

    # Use env vars if set, otherwise generate random passwords in production
    # or use defaults only in development
    if environment == "production":
        admin_password = os.environ.get("SEED_ADMIN_PASSWORD") or _generate_random_password()
        demo_password = os.environ.get("SEED_DEMO_PASSWORD") or _generate_random_password()
        manager_password = os.environ.get("SEED_MANAGER_PASSWORD") or _generate_random_password()
    else:
        admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "Admin123!")
        demo_password = os.environ.get("SEED_DEMO_PASSWORD", "Demo123!")
        manager_password = os.environ.get("SEED_MANAGER_PASSWORD", "Manager123!")

    print(f"Seeding database: {settings.DATABASE_URL[:50]}...")
    print(f"Environment: {environment}")
    print()

    # Initialize tables
    await init_db()

    async with get_session_context() as session:
        # ---------------------------------------------------------------
        # 1. Users
        # ---------------------------------------------------------------
        print("[1/7] Creating users...")

        # email_verified=True for all seeded users so they work immediately in dev
        verified = True

        # Admin
        result = await session.execute(select(User).where(User.email == "admin@saas-ia.com"))
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                email="admin@saas-ia.com",
                hashed_password=get_password_hash(admin_password),
                full_name="Admin SaaS-IA",
                role=Role.ADMIN,
                is_active=True,
                email_verified=verified,
            )
            session.add(admin)
            print("  + admin@saas-ia.com created")
            admin_created = True
        else:
            print("  = admin@saas-ia.com already exists")
            admin_created = False

        # Manager
        result = await session.execute(select(User).where(User.email == "manager@saas-ia.com"))
        manager_user = result.scalar_one_or_none()

        if not manager_user:
            manager_user = User(
                email="manager@saas-ia.com",
                hashed_password=get_password_hash(manager_password),
                full_name="Manager SaaS-IA",
                role=Role.MANAGER,
                is_active=True,
                email_verified=verified,
            )
            session.add(manager_user)
            print("  + manager@saas-ia.com created")
            manager_created = True
        else:
            print("  = manager@saas-ia.com already exists")
            manager_created = False

        # Demo user
        result = await session.execute(select(User).where(User.email == "demo@saas-ia.com"))
        demo_user = result.scalar_one_or_none()

        if not demo_user:
            demo_user = User(
                email="demo@saas-ia.com",
                hashed_password=get_password_hash(demo_password),
                full_name="Demo User",
                role=Role.USER,
                is_active=True,
                email_verified=verified,
            )
            session.add(demo_user)
            print("  + demo@saas-ia.com created")
            demo_created = True
        else:
            print("  = demo@saas-ia.com already exists")
            demo_created = False

        await session.flush()

        # ---------------------------------------------------------------
        # 2. Billing Plans
        # ---------------------------------------------------------------
        print("[2/6] Creating billing plans...")

        result = await session.execute(select(Plan))
        existing_plans = list(result.scalars().all())

        if not existing_plans:
            plans = [
                Plan(
                    name=PlanName.FREE,
                    display_name="Free",
                    max_transcriptions_month=10,
                    max_audio_minutes_month=60,
                    max_ai_calls_month=50,
                    price_cents=0,
                ),
                Plan(
                    name=PlanName.PRO,
                    display_name="Pro",
                    max_transcriptions_month=100,
                    max_audio_minutes_month=600,
                    max_ai_calls_month=500,
                    price_cents=1900,
                ),
                Plan(
                    name=PlanName.ENTERPRISE,
                    display_name="Enterprise",
                    max_transcriptions_month=999999,
                    max_audio_minutes_month=999999,
                    max_ai_calls_month=999999,
                    price_cents=0,
                ),
            ]
            for plan in plans:
                session.add(plan)
            await session.flush()
            print("  + Free, Pro, Enterprise plans created")
            free_plan = plans[0]
        else:
            print(f"  = {len(existing_plans)} plans already exist")
            free_plan = next((p for p in existing_plans if p.name == PlanName.FREE), existing_plans[0])

        # ---------------------------------------------------------------
        # 3. User Quotas
        # ---------------------------------------------------------------
        print("[3/6] Creating user quotas...")

        for user in [admin, manager_user, demo_user]:
            result = await session.execute(
                select(UserQuota).where(UserQuota.user_id == user.id)
            )
            if not result.scalar_one_or_none():
                from dateutil.relativedelta import relativedelta
                period_start = date.today().replace(day=1)
                period_end = (period_start + relativedelta(months=1)) - relativedelta(days=1)
                quota = UserQuota(
                    user_id=user.id,
                    plan_id=free_plan.id,
                    period_start=period_start,
                    period_end=period_end,
                )
                session.add(quota)
                print(f"  + Quota for {user.email}")
            else:
                print(f"  = Quota for {user.email} already exists")

        await session.flush()

        # ---------------------------------------------------------------
        # 4. Sample Transcriptions
        # ---------------------------------------------------------------
        print("[4/6] Creating sample transcriptions...")

        result = await session.execute(
            select(Transcription).where(Transcription.user_id == demo_user.id)
        )
        if not result.scalars().first():
            samples = [
                Transcription(
                    user_id=demo_user.id,
                    video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    language="en",
                    source_type="youtube",
                    status=TranscriptionStatus.COMPLETED,
                    text="This is a sample completed transcription for demo purposes. "
                         "It contains example text that would normally come from AssemblyAI.",
                    confidence=0.95,
                    duration_seconds=212,
                    completed_at=datetime.now(UTC),
                ),
                Transcription(
                    user_id=demo_user.id,
                    video_url="https://www.youtube.com/watch?v=jNQXAC9IVRw",
                    language="en",
                    source_type="youtube",
                    status=TranscriptionStatus.COMPLETED,
                    text="Another sample transcription. This demonstrates the multi-source "
                         "capability of the platform.",
                    confidence=0.92,
                    duration_seconds=19,
                    completed_at=datetime.now(UTC),
                ),
                Transcription(
                    user_id=demo_user.id,
                    video_url="upload://presentation.mp3",
                    language="fr",
                    source_type="upload",
                    original_filename="presentation.mp3",
                    status=TranscriptionStatus.PENDING,
                ),
            ]
            for t in samples:
                session.add(t)
            print("  + 3 sample transcriptions (2 completed, 1 pending)")
        else:
            print("  = Transcriptions already exist for demo user")

        # ---------------------------------------------------------------
        # 5. Sample Pipeline
        # ---------------------------------------------------------------
        print("[5/6] Creating sample pipeline...")

        result = await session.execute(
            select(Pipeline).where(Pipeline.user_id == demo_user.id)
        )
        if not result.scalars().first():
            pipeline = Pipeline(
                user_id=demo_user.id,
                name="YouTube to Summary (FR)",
                description="Transcribe a YouTube video and generate a French summary",
                steps_json=json.dumps([
                    {"id": "step1", "type": "transcription", "config": {"language": "auto"}, "position": 0},
                    {"id": "step2", "type": "summarize", "config": {"provider": "gemini"}, "position": 1},
                    {"id": "step3", "type": "translate", "config": {"target_language": "fr", "provider": "gemini"}, "position": 2},
                ]),
                status=PipelineStatus.ACTIVE,
            )
            session.add(pipeline)
            print("  + 1 sample pipeline (3 steps)")
        else:
            print("  = Pipeline already exists for demo user")

        # ---------------------------------------------------------------
        # 6. Sample Workspace
        # ---------------------------------------------------------------
        print("[6/6] Creating sample workspace...")

        result = await session.execute(
            select(Workspace).where(Workspace.owner_id == admin.id)
        )
        if not result.scalars().first():
            workspace = Workspace(
                name="SaaS-IA Team",
                description="Default team workspace for collaboration",
                owner_id=admin.id,
            )
            session.add(workspace)
            await session.flush()

            # Add admin as owner
            owner_member = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=admin.id,
                role=WorkspaceRole.OWNER,
            )
            session.add(owner_member)

            # Add demo user as editor
            editor_member = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=demo_user.id,
                role=WorkspaceRole.EDITOR,
            )
            session.add(editor_member)
            print("  + 1 workspace with 2 members (admin=owner, demo=editor)")
        else:
            print("  = Workspace already exists")

        # ---------------------------------------------------------------
        # Commit
        # ---------------------------------------------------------------
        await session.commit()

    print()
    print("Seed complete!")
    print()
    # Only show credentials in non-production environments and only for newly created users
    if environment != "production":
        print("Login credentials:")
        if admin_created:
            print(f"  Admin:   admin@saas-ia.com   / {admin_password}")
        if manager_created:
            print(f"  Manager: manager@saas-ia.com / {manager_password}")
        if demo_created:
            print(f"  User:    demo@saas-ia.com    / {demo_password}")
        if not admin_created and not manager_created and not demo_created:
            print("  (no new users created)")
    else:
        print("Production mode: credentials are NOT displayed.")
        print("Use SEED_ADMIN_PASSWORD / SEED_MANAGER_PASSWORD / SEED_DEMO_PASSWORD env vars to control passwords.")
        seed_logger.warning("seed_completed_in_production")
    print()
    print("Access the app at http://localhost:3002")


if __name__ == "__main__":
    asyncio.run(seed())
