"""Initial consolidated migration - all tables

Revision ID: initial_001
Revises: None
Create Date: 2026-03-23

Consolidates all previous migrations into a single initial migration:
- sprint3_001: billing tables (plans, user_quotas)
- sprint4_001: compare tables (comparison_results, comparison_votes)
- sprint4_002: pipeline tables (pipelines, pipeline_executions)
- sprint5_001: knowledge tables (documents, document_chunks)
- sprint5_002: api_keys table
- stripe_001: stripe fields on plans/user_quotas
- collab_001: workspace tables (workspaces, workspace_members, shared_items, comments)
- agent_001: agent tables (agent_runs, agent_steps)
- diarize_001: speaker diarization on transcriptions
- cost_001: ai_usage_logs table
- sentiment_001: sentiment on transcriptions
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'initial_001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # Users (base table -- no FKs)
    # ---------------------------------------------------------------
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # ---------------------------------------------------------------
    # Transcriptions (FK -> users)
    # ---------------------------------------------------------------
    op.create_table(
        'transcriptions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('video_url', sa.String(length=500), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=True, server_default='auto'),
        sa.Column('source_type', sa.String(length=20), nullable=True, server_default='youtube'),
        sa.Column('original_filename', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        # Speaker diarization
        sa.Column('speakers_json', sa.Text(), nullable=True),
        sa.Column('speaker_count', sa.Integer(), nullable=True),
        # Sentiment analysis
        sa.Column('sentiment_json', sa.Text(), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        # Error handling
        sa.Column('error', sa.String(length=1000), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_transcriptions_user_id', 'transcriptions', ['user_id'])

    # ---------------------------------------------------------------
    # Conversations (FK -> users, transcriptions)
    # ---------------------------------------------------------------
    op.create_table(
        'conversations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('transcription_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['transcription_id'], ['transcriptions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_transcription_id', 'conversations', ['transcription_id'])

    # ---------------------------------------------------------------
    # Messages (FK -> conversations)
    # ---------------------------------------------------------------
    op.create_table(
        'messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])

    # ---------------------------------------------------------------
    # Plans (no FKs)
    # ---------------------------------------------------------------
    op.create_table(
        'plans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=20), nullable=False),
        sa.Column('display_name', sa.String(length=50), nullable=False),
        sa.Column('max_transcriptions_month', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('max_audio_minutes_month', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('max_ai_calls_month', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('price_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('stripe_price_id', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_plans_name', 'plans', ['name'])

    # ---------------------------------------------------------------
    # User Quotas (FK -> users, plans)
    # ---------------------------------------------------------------
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
        sa.Column('stripe_customer_id', sa.String(length=100), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_quotas_user_id', 'user_quotas', ['user_id'])

    # ---------------------------------------------------------------
    # Comparison Results (FK -> users)
    # ---------------------------------------------------------------
    op.create_table(
        'comparison_results',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('providers_used', sa.String(length=500), nullable=True),
        sa.Column('results_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_comparison_results_user_id', 'comparison_results', ['user_id'])

    # ---------------------------------------------------------------
    # Comparison Votes (FK -> comparison_results, users)
    # ---------------------------------------------------------------
    op.create_table(
        'comparison_votes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('comparison_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('quality_score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['comparison_id'], ['comparison_results.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_comparison_votes_comparison_id', 'comparison_votes', ['comparison_id'])
    op.create_index('ix_comparison_votes_user_id', 'comparison_votes', ['user_id'])

    # ---------------------------------------------------------------
    # Pipelines (FK -> users)
    # ---------------------------------------------------------------
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

    # ---------------------------------------------------------------
    # Pipeline Executions (FK -> pipelines, users)
    # ---------------------------------------------------------------
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

    # ---------------------------------------------------------------
    # Documents - Knowledge Base (FK -> users)
    # ---------------------------------------------------------------
    op.create_table(
        'documents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('total_chunks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('error', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])

    # ---------------------------------------------------------------
    # Document Chunks (FK -> documents, users)
    # ---------------------------------------------------------------
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('document_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])
    op.create_index('ix_document_chunks_user_id', 'document_chunks', ['user_id'])

    # ---------------------------------------------------------------
    # API Keys (FK -> users)
    # ---------------------------------------------------------------
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=8), nullable=False),
        sa.Column('permissions_json', sa.Text(), nullable=False, server_default='["read", "write"]'),
        sa.Column('rate_limit_per_day', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])

    # ---------------------------------------------------------------
    # Agent Runs (FK -> users)
    # ---------------------------------------------------------------
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

    # ---------------------------------------------------------------
    # Agent Steps (FK -> agent_runs)
    # ---------------------------------------------------------------
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

    # ---------------------------------------------------------------
    # Workspaces (FK -> users)
    # ---------------------------------------------------------------
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('owner_id', sa.Uuid(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workspaces_owner_id', 'workspaces', ['owner_id'])

    # ---------------------------------------------------------------
    # Workspace Members (FK -> workspaces, users)
    # ---------------------------------------------------------------
    op.create_table(
        'workspace_members',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='viewer'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_workspace_members_workspace_id', 'workspace_members', ['workspace_id'])
    op.create_index('ix_workspace_members_user_id', 'workspace_members', ['user_id'])

    # ---------------------------------------------------------------
    # Shared Items (FK -> workspaces, users)
    # ---------------------------------------------------------------
    op.create_table(
        'shared_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('workspace_id', sa.Uuid(), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('item_id', sa.Uuid(), nullable=False),
        sa.Column('shared_by', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.ForeignKeyConstraint(['shared_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shared_items_workspace_id', 'shared_items', ['workspace_id'])

    # ---------------------------------------------------------------
    # Comments (FK -> shared_items, users)
    # ---------------------------------------------------------------
    op.create_table(
        'comments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('shared_item_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('content', sa.String(length=5000), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['shared_item_id'], ['shared_items.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_comments_shared_item_id', 'comments', ['shared_item_id'])

    # ---------------------------------------------------------------
    # AI Usage Logs - Cost Tracker (FK -> users)
    # ---------------------------------------------------------------
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
    # Drop in reverse dependency order
    op.drop_index('ix_ai_usage_logs_created_at', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_provider', table_name='ai_usage_logs')
    op.drop_index('ix_ai_usage_logs_user_id', table_name='ai_usage_logs')
    op.drop_table('ai_usage_logs')

    op.drop_index('ix_comments_shared_item_id', table_name='comments')
    op.drop_table('comments')

    op.drop_index('ix_shared_items_workspace_id', table_name='shared_items')
    op.drop_table('shared_items')

    op.drop_index('ix_workspace_members_user_id', table_name='workspace_members')
    op.drop_index('ix_workspace_members_workspace_id', table_name='workspace_members')
    op.drop_table('workspace_members')

    op.drop_index('ix_workspaces_owner_id', table_name='workspaces')
    op.drop_table('workspaces')

    op.drop_index('ix_agent_steps_run_id', table_name='agent_steps')
    op.drop_table('agent_steps')

    op.drop_index('ix_agent_runs_user_id', table_name='agent_runs')
    op.drop_table('agent_runs')

    op.drop_index('ix_api_keys_user_id', table_name='api_keys')
    op.drop_table('api_keys')

    op.drop_index('ix_document_chunks_user_id', table_name='document_chunks')
    op.drop_index('ix_document_chunks_document_id', table_name='document_chunks')
    op.drop_table('document_chunks')

    op.drop_index('ix_documents_user_id', table_name='documents')
    op.drop_table('documents')

    op.drop_index('ix_pipeline_executions_user_id', table_name='pipeline_executions')
    op.drop_index('ix_pipeline_executions_pipeline_id', table_name='pipeline_executions')
    op.drop_table('pipeline_executions')

    op.drop_index('ix_pipelines_user_id', table_name='pipelines')
    op.drop_table('pipelines')

    op.drop_index('ix_comparison_votes_user_id', table_name='comparison_votes')
    op.drop_index('ix_comparison_votes_comparison_id', table_name='comparison_votes')
    op.drop_table('comparison_votes')

    op.drop_index('ix_comparison_results_user_id', table_name='comparison_results')
    op.drop_table('comparison_results')

    op.drop_index('ix_user_quotas_user_id', table_name='user_quotas')
    op.drop_table('user_quotas')

    op.drop_index('ix_plans_name', table_name='plans')
    op.drop_table('plans')

    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_table('messages')

    op.drop_index('ix_conversations_transcription_id', table_name='conversations')
    op.drop_index('ix_conversations_user_id', table_name='conversations')
    op.drop_table('conversations')

    op.drop_index('ix_transcriptions_user_id', table_name='transcriptions')
    op.drop_table('transcriptions')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
