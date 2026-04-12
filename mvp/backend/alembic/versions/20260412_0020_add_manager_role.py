"""add_manager_role

Revision ID: add_manager_role_020
Revises: instagram_reels_019
Create Date: 2026-04-12

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = 'add_manager_role_020'
down_revision: str = 'instagram_reels_019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE role ADD VALUE IF NOT EXISTS 'MANAGER'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values without recreating the type.
    # Downgrade is a no-op — MANAGER value will remain but unused.
    pass
