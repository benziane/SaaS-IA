"""Add missing composite indexes for query performance

Revision ID: composite_idx_001
Revises: consolidate_015
Create Date: 2026-03-26

Adds composite indexes on columns commonly used together in
WHERE / JOIN / ORDER BY clauses.  Without these indexes the planner
falls back to sequential scans on large tables.

Indexes added:
 1. ix_workspace_members_composite        (workspace_id, user_id)
 2. ix_shared_items_item                  (item_type, item_id)
 3. ix_ai_usage_logs_user_time            (user_id, created_at)
 4. ix_workflow_runs_status_time           (status, created_at)
 5. ix_agent_runs_status_time              (status, created_at)
 6. ix_social_posts_schedule               (user_id, status, schedule_at)
 7. ix_generated_contents_project_status   (project_id, status)
 8. ix_messages_conversation_time          (conversation_id, created_at)
 9. ix_document_chunks_document            (document_id, chunk_index)
10. ix_pipeline_executions_status          (pipeline_id, status)
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'composite_idx_001'
down_revision: Union[str, None] = 'consolidate_015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- helpers ----------------------------------------------------------------
# Wrap each create/drop in try-except so the migration is idempotent:
# if an index already exists (or was already dropped) we just skip it.

def _safe_create_index(name: str, table: str, columns: list[str]) -> None:
    """Create an index, silently skipping if it already exists."""
    try:
        op.create_index(name, table, columns)
    except Exception:
        pass  # index already exists – nothing to do


def _safe_drop_index(name: str, table: str) -> None:
    """Drop an index, silently skipping if it does not exist."""
    try:
        op.drop_index(name, table_name=table)
    except Exception:
        pass  # index already gone – nothing to do


# --- upgrade ----------------------------------------------------------------

def upgrade() -> None:
    # 1. workspace_members: used in membership lookups / unique-pair checks
    _safe_create_index(
        'ix_workspace_members_composite',
        'workspace_members',
        ['workspace_id', 'user_id'],
    )

    # 2. shared_items: polymorphic item lookup (WHERE item_type = ? AND item_id = ?)
    _safe_create_index(
        'ix_shared_items_item',
        'shared_items',
        ['item_type', 'item_id'],
    )

    # 3. ai_usage_logs: per-user cost dashboards ordered by time
    _safe_create_index(
        'ix_ai_usage_logs_user_time',
        'ai_usage_logs',
        ['user_id', 'created_at'],
    )

    # 4. workflow_runs: listing runs filtered by status + newest first
    _safe_create_index(
        'ix_workflow_runs_status_time',
        'workflow_runs',
        ['status', 'created_at'],
    )

    # 5. agent_runs: same pattern as workflow_runs
    _safe_create_index(
        'ix_agent_runs_status_time',
        'agent_runs',
        ['status', 'created_at'],
    )

    # 6. social_posts: scheduler query (user's scheduled posts by status + time)
    _safe_create_index(
        'ix_social_posts_schedule',
        'social_posts',
        ['user_id', 'status', 'schedule_at'],
    )

    # 7. generated_contents: content list per project filtered by status
    _safe_create_index(
        'ix_generated_contents_project_status',
        'generated_contents',
        ['project_id', 'status'],
    )

    # 8. messages: conversation thread ordered by time
    _safe_create_index(
        'ix_messages_conversation_time',
        'messages',
        ['conversation_id', 'created_at'],
    )

    # 9. document_chunks: ordered retrieval of chunks within a document
    _safe_create_index(
        'ix_document_chunks_document',
        'document_chunks',
        ['document_id', 'chunk_index'],
    )

    # 10. pipeline_executions: list executions per pipeline filtered by status
    _safe_create_index(
        'ix_pipeline_executions_status',
        'pipeline_executions',
        ['pipeline_id', 'status'],
    )


# --- downgrade --------------------------------------------------------------

def downgrade() -> None:
    _safe_drop_index('ix_pipeline_executions_status', 'pipeline_executions')
    _safe_drop_index('ix_document_chunks_document', 'document_chunks')
    _safe_drop_index('ix_messages_conversation_time', 'messages')
    _safe_drop_index('ix_generated_contents_project_status', 'generated_contents')
    _safe_drop_index('ix_social_posts_schedule', 'social_posts')
    _safe_drop_index('ix_agent_runs_status_time', 'agent_runs')
    _safe_drop_index('ix_workflow_runs_status_time', 'workflow_runs')
    _safe_drop_index('ix_ai_usage_logs_user_time', 'ai_usage_logs')
    _safe_drop_index('ix_shared_items_item', 'shared_items')
    _safe_drop_index('ix_workspace_members_composite', 'workspace_members')
