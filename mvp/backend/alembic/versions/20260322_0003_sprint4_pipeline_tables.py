"""Sprint 4: Add pipeline tables (pipelines, pipeline_executions)

Revision ID: sprint4_002
Revises: sprint4_001
Create Date: 2026-03-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'sprint4_002'
down_revision: Union[str, None] = 'sprint4_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'pipelines',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('steps_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pipelines_user_id', 'pipelines', ['user_id'])

    op.create_table(
        'pipeline_executions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('pipeline_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_steps', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('results_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('error', sa.String(length=2000), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pipeline_executions_pipeline_id', 'pipeline_executions', ['pipeline_id'])
    op.create_index('ix_pipeline_executions_user_id', 'pipeline_executions', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_pipeline_executions_user_id', table_name='pipeline_executions')
    op.drop_index('ix_pipeline_executions_pipeline_id', table_name='pipeline_executions')
    op.drop_table('pipeline_executions')
    op.drop_index('ix_pipelines_user_id', table_name='pipelines')
    op.drop_table('pipelines')
