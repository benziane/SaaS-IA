"""Add content_studio and ai_workflows tables

Revision ID: cs_wf_001
Revises: initial_001
Create Date: 2026-03-23

Adds:
- content_projects: Multi-format content generation projects
- generated_contents: Individual generated content pieces
- workflows: No-code AI automation workflows
- workflow_runs: Workflow execution history
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'cs_wf_001'
down_revision: Union[str, None] = 'initial_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # Content Studio: Projects
    # ---------------------------------------------------------------
    op.create_table(
        'content_projects',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_id', sa.String(length=200), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=False, server_default=''),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='auto'),
        sa.Column('tone', sa.String(length=50), nullable=False, server_default='professional'),
        sa.Column('target_audience', sa.String(length=200), nullable=True),
        sa.Column('keywords', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_content_projects_user_id', 'content_projects', ['user_id'])

    # ---------------------------------------------------------------
    # Content Studio: Generated Contents
    # ---------------------------------------------------------------
    op.create_table(
        'generated_contents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('format', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['content_projects.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_generated_contents_project_id', 'generated_contents', ['project_id'])
    op.create_index('ix_generated_contents_user_id', 'generated_contents', ['user_id'])
    op.create_index('ix_generated_contents_format', 'generated_contents', ['format'])

    # ---------------------------------------------------------------
    # AI Workflows: Workflows
    # ---------------------------------------------------------------
    op.create_table(
        'workflows',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('trigger_type', sa.String(length=50), nullable=False, server_default='manual'),
        sa.Column('trigger_config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('nodes_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('edges_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('is_template', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('template_category', sa.String(length=100), nullable=True),
        sa.Column('run_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('schedule_cron', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workflows_user_id', 'workflows', ['user_id'])

    # ---------------------------------------------------------------
    # AI Workflows: Runs
    # ---------------------------------------------------------------
    op.create_table(
        'workflow_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('workflow_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('trigger_type', sa.String(length=50), nullable=False, server_default='manual'),
        sa.Column('trigger_data_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('current_node', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_nodes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('results_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('error', sa.String(length=2000), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workflow_runs_workflow_id', 'workflow_runs', ['workflow_id'])
    op.create_index('ix_workflow_runs_user_id', 'workflow_runs', ['user_id'])


def downgrade() -> None:
    op.drop_table('workflow_runs')
    op.drop_table('workflows')
    op.drop_table('generated_contents')
    op.drop_table('content_projects')
