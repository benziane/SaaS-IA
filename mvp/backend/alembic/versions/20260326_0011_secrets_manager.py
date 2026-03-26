"""Add secret_registrations table for secrets rotation tracking

Revision ID: secrets_mgr_001
Revises: repo_analyzer_001
Create Date: 2026-03-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'secrets_mgr_001'
down_revision: Union[str, None] = 'outbox_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('secret_registrations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('secret_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('rotation_days', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('registered_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_rotated_at', sa.DateTime(), nullable=True),
        sa.Column('next_rotation_at', sa.DateTime(), nullable=True),
        sa.Column('rotation_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_secret_registrations_name', 'secret_registrations', ['name'], unique=True)
    op.create_index('ix_secret_registrations_status', 'secret_registrations', ['status'])


def downgrade() -> None:
    op.drop_index('ix_secret_registrations_status', table_name='secret_registrations')
    op.drop_index('ix_secret_registrations_name', table_name='secret_registrations')
    op.drop_table('secret_registrations')
