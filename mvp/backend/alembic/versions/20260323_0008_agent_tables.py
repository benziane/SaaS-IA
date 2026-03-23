"""Add AI agent tables

Revision ID: agent_001
Revises: collab_001
Create Date: 2026-03-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'agent_001'
down_revision: Union[str, None] = 'collab_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('instruction', sa.String(length=5000), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='planning'),
        sa.Column('plan_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('results_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_steps', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error', sa.String(length=2000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_runs_user_id', 'agent_runs', ['user_id'])

    op.create_table(
        'agent_steps',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('run_id', sa.Uuid(), nullable=False),
        sa.Column('step_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('input_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('output_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='planning'),
        sa.Column('error', sa.String(length=1000), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['agent_runs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_steps_run_id', 'agent_steps', ['run_id'])


def downgrade() -> None:
    op.drop_index('ix_agent_steps_run_id', table_name='agent_steps')
    op.drop_table('agent_steps')
    op.drop_index('ix_agent_runs_user_id', table_name='agent_runs')
    op.drop_table('agent_runs')
