"""Add repo_analyses table for Repo Analyzer module

Revision ID: repo_analyzer_001
Revises: notifications_001
Create Date: 2026-03-25
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'repo_analyzer_001'
down_revision: Union[str, None] = 'notifications_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('repo_analyses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('repo_url', sa.String(500), nullable=False),
        sa.Column('repo_name', sa.String(200), nullable=False, server_default=''),
        sa.Column('analysis_types_json', sa.Text(), nullable=False, server_default='["all"]'),
        sa.Column('depth', sa.String(20), nullable=False, server_default='standard'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_step', sa.String(500), nullable=False, server_default='queued'),
        sa.Column('results_json', sa.Text(), nullable=True),
        sa.Column('error', sa.String(2000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_repo_analyses_user_id', 'repo_analyses', ['user_id'])
    op.create_index('ix_repo_analyses_status', 'repo_analyses', ['status'])


def downgrade() -> None:
    op.drop_index('ix_repo_analyses_status', table_name='repo_analyses')
    op.drop_index('ix_repo_analyses_user_id', table_name='repo_analyses')
    op.drop_table('repo_analyses')
