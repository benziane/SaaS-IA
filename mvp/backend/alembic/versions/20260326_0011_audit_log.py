"""Add audit_log table for immutable compliance-grade audit trail

-- CRITICAL: Never add UPDATE or DELETE permissions on this table
-- REVOKE UPDATE, DELETE ON audit_log FROM app_user;

Revision ID: audit_log_001
Revises: audio_studio_001
Create Date: 2026-03-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'audit_log_001'
down_revision: Union[str, None] = 'audio_studio_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- CRITICAL: This table is INSERT-only. --
    # -- Never add UPDATE or DELETE permissions on this table. --
    # -- REVOKE UPDATE, DELETE ON audit_log FROM app_user; --
    op.create_table('audit_log',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tenant_id', sa.Uuid(), nullable=True),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('old_value_json', sa.Text(), nullable=True),
        sa.Column('new_value_json', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
        sa.Column('record_hash', sa.String(64), nullable=False),
        sa.Column('previous_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )

    # Indexes for common query patterns
    op.create_index('ix_audit_log_tenant_id', 'audit_log', ['tenant_id'])
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])
    op.create_index('ix_audit_log_action', 'audit_log', ['action'])
    op.create_index('ix_audit_log_resource_type', 'audit_log', ['resource_type'])
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])

    # Composite index for the most common query: filter by tenant + time range
    op.create_index(
        'ix_audit_log_tenant_created',
        'audit_log',
        ['tenant_id', 'created_at'],
    )

    # Composite index for user activity queries
    op.create_index(
        'ix_audit_log_user_created',
        'audit_log',
        ['user_id', 'created_at'],
    )


def downgrade() -> None:
    op.drop_table('audit_log')
