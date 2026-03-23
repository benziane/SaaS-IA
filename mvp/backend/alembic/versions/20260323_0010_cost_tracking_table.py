"""Add AI usage cost tracking table

Revision ID: cost_001
Revises: diarize_001
Create Date: 2026-03-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'cost_001'
down_revision: Union[str, None] = 'diarize_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_usage_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('module', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost_cents', sa.Float(), nullable=False, server_default='0'),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ai_usage_logs_user_id', 'ai_usage_logs', ['user_id'])
    op.create_index('ix_ai_usage_logs_provider', 'ai_usage_logs', ['provider'])
    op.create_index('ix_ai_usage_logs_created_at', 'ai_usage_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_ai_usage_logs_created_at', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_provider', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_user_id', table_name='ai_usage_logs')
    op.drop_table('ai_usage_logs')
