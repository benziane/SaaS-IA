"""Add outbox_events table for transactional outbox pattern

Revision ID: outbox_001
Revises: repo_analyzer_001
Create Date: 2026-03-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'outbox_001'
down_revision: Union[str, None] = 'repo_analyzer_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('outbox_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('payload_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('tenant_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    # Indexes for the polling query (status + created_at) and filtering
    op.create_index('ix_outbox_events_event_type', 'outbox_events', ['event_type'])
    op.create_index('ix_outbox_events_status', 'outbox_events', ['status'])
    op.create_index('ix_outbox_events_created_at', 'outbox_events', ['created_at'])
    op.create_index('ix_outbox_events_user_id', 'outbox_events', ['user_id'])
    op.create_index('ix_outbox_events_tenant_id', 'outbox_events', ['tenant_id'])
    # Composite index for the primary polling query
    op.create_index(
        'ix_outbox_events_pending_poll',
        'outbox_events',
        ['status', 'created_at'],
        postgresql_where=sa.text("status IN ('pending', 'failed')"),
    )


def downgrade() -> None:
    op.drop_index('ix_outbox_events_pending_poll', table_name='outbox_events')
    op.drop_index('ix_outbox_events_tenant_id', table_name='outbox_events')
    op.drop_index('ix_outbox_events_user_id', table_name='outbox_events')
    op.drop_index('ix_outbox_events_created_at', table_name='outbox_events')
    op.drop_index('ix_outbox_events_status', table_name='outbox_events')
    op.drop_index('ix_outbox_events_event_type', table_name='outbox_events')
    op.drop_table('outbox_events')
