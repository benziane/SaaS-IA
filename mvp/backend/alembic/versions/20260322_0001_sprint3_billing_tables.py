"""Sprint 3: Add billing tables (plans, user_quotas)

Revision ID: sprint3_001
Revises:
Create Date: 2026-03-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = 'sprint3_001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'plans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=20), nullable=False),
        sa.Column('display_name', sa.String(length=50), nullable=False),
        sa.Column('max_transcriptions_month', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_audio_minutes_month', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('max_ai_calls_month', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('price_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_plans_name', 'plans', ['name'])

    op.create_table(
        'user_quotas',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('plan_id', sa.Uuid(), nullable=False),
        sa.Column('transcriptions_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('audio_minutes_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ai_calls_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_quotas_user_id', 'user_quotas', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_user_quotas_user_id', table_name='user_quotas')
    op.drop_table('user_quotas')
    op.drop_index('ix_plans_name', table_name='plans')
    op.drop_table('plans')
