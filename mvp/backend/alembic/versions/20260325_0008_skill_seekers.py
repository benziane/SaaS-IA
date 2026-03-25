"""Add scrape_jobs table for Skill Seekers module

Revision ID: skill_seekers_001
Revises: mem_search_001
Create Date: 2026-03-25
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'skill_seekers_001'
down_revision: Union[str, None] = 'mem_search_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('scrape_jobs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('repos_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('targets_json', sa.Text(), nullable=False, server_default='["claude"]'),
        sa.Column('enhance', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_step', sa.String(500), nullable=False, server_default='queued'),
        sa.Column('output_files_json', sa.Text(), nullable=True),
        sa.Column('error', sa.String(2000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_scrape_jobs_user_id', 'scrape_jobs', ['user_id'])
    op.create_index('ix_scrape_jobs_status', 'scrape_jobs', ['status'])


def downgrade() -> None:
    op.drop_index('ix_scrape_jobs_status', table_name='scrape_jobs')
    op.drop_index('ix_scrape_jobs_user_id', table_name='scrape_jobs')
    op.drop_table('scrape_jobs')
