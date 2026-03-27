"""Add email_verified field to users table

Revision ID: email_verified_018
Revises: cascade_delete_001
Create Date: 2026-03-27
"""

from alembic import op
import sqlalchemy as sa

revision: str = 'email_verified_018'
down_revision: str = 'cascade_delete_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    op.drop_column('users', 'email_verified')
