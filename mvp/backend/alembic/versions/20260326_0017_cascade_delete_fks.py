"""Add CASCADE DELETE to all foreign key constraints

Revision ID: cascade_delete_001
Revises: composite_idx_001, unique_constraints_016
Create Date: 2026-03-26

All 78 FK constraints across 38+ tables were created without ondelete
behaviour, causing orphaned child rows when a parent row is deleted.
This migration drops each FK and recreates it with ondelete='CASCADE'.

Skipped: users.tenant_id -> tenants.id (already SET NULL by design).

Uses batch_alter_table for SQLite compatibility in tests.
PostgreSQL auto-names unnamed FKs as '<table>_<col>_fkey'.
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'cascade_delete_001'
down_revision: tuple = ('composite_idx_001', 'unique_constraints_016')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_SPECS = [
    # (table, local_col, ref_table, ref_col, old_fk_name, new_fk_name)
    # old_fk_name = PostgreSQL auto-generated name: <table>_<col>_fkey
    #
    # ---- initial_001 tables ----
    ('transcriptions', 'user_id', 'users', 'id',
     'transcriptions_user_id_fkey', 'fk_transcriptions_user_id'),
    ('conversations', 'user_id', 'users', 'id',
     'conversations_user_id_fkey', 'fk_conversations_user_id'),
    ('conversations', 'transcription_id', 'transcriptions', 'id',
     'conversations_transcription_id_fkey', 'fk_conversations_transcription_id'),
    ('messages', 'conversation_id', 'conversations', 'id',
     'messages_conversation_id_fkey', 'fk_messages_conversation_id'),
    ('user_quotas', 'user_id', 'users', 'id',
     'user_quotas_user_id_fkey', 'fk_user_quotas_user_id'),
    ('user_quotas', 'plan_id', 'plans', 'id',
     'user_quotas_plan_id_fkey', 'fk_user_quotas_plan_id'),
    ('comparison_results', 'user_id', 'users', 'id',
     'comparison_results_user_id_fkey', 'fk_comparison_results_user_id'),
    ('comparison_votes', 'comparison_id', 'comparison_results', 'id',
     'comparison_votes_comparison_id_fkey', 'fk_comparison_votes_comparison_id'),
    ('comparison_votes', 'user_id', 'users', 'id',
     'comparison_votes_user_id_fkey', 'fk_comparison_votes_user_id'),
    ('pipelines', 'user_id', 'users', 'id',
     'pipelines_user_id_fkey', 'fk_pipelines_user_id'),
    ('pipeline_executions', 'pipeline_id', 'pipelines', 'id',
     'pipeline_executions_pipeline_id_fkey', 'fk_pipeline_executions_pipeline_id'),
    ('pipeline_executions', 'user_id', 'users', 'id',
     'pipeline_executions_user_id_fkey', 'fk_pipeline_executions_user_id'),
    ('documents', 'user_id', 'users', 'id',
     'documents_user_id_fkey', 'fk_documents_user_id'),
    ('document_chunks', 'document_id', 'documents', 'id',
     'document_chunks_document_id_fkey', 'fk_document_chunks_document_id'),
    ('document_chunks', 'user_id', 'users', 'id',
     'document_chunks_user_id_fkey', 'fk_document_chunks_user_id'),
    ('api_keys', 'user_id', 'users', 'id',
     'api_keys_user_id_fkey', 'fk_api_keys_user_id'),
    ('agent_runs', 'user_id', 'users', 'id',
     'agent_runs_user_id_fkey', 'fk_agent_runs_user_id'),
    ('agent_steps', 'run_id', 'agent_runs', 'id',
     'agent_steps_run_id_fkey', 'fk_agent_steps_run_id'),
    ('workspaces', 'owner_id', 'users', 'id',
     'workspaces_owner_id_fkey', 'fk_workspaces_owner_id'),
    ('workspace_members', 'workspace_id', 'workspaces', 'id',
     'workspace_members_workspace_id_fkey', 'fk_workspace_members_workspace_id'),
    ('workspace_members', 'user_id', 'users', 'id',
     'workspace_members_user_id_fkey', 'fk_workspace_members_user_id'),
    ('shared_items', 'workspace_id', 'workspaces', 'id',
     'shared_items_workspace_id_fkey', 'fk_shared_items_workspace_id'),
    ('shared_items', 'shared_by', 'users', 'id',
     'shared_items_shared_by_fkey', 'fk_shared_items_shared_by'),
    ('comments', 'shared_item_id', 'shared_items', 'id',
     'comments_shared_item_id_fkey', 'fk_comments_shared_item_id'),
    ('comments', 'user_id', 'users', 'id',
     'comments_user_id_fkey', 'fk_comments_user_id'),
    ('ai_usage_logs', 'user_id', 'users', 'id',
     'ai_usage_logs_user_id_fkey', 'fk_ai_usage_logs_user_id'),
    # ---- cs_wf_001 tables ----
    ('content_projects', 'user_id', 'users', 'id',
     'content_projects_user_id_fkey', 'fk_content_projects_user_id'),
    ('generated_contents', 'project_id', 'content_projects', 'id',
     'generated_contents_project_id_fkey', 'fk_generated_contents_project_id'),
    ('generated_contents', 'user_id', 'users', 'id',
     'generated_contents_user_id_fkey', 'fk_generated_contents_user_id'),
    ('workflows', 'user_id', 'users', 'id',
     'workflows_user_id_fkey', 'fk_workflows_user_id'),
    ('workflow_runs', 'workflow_id', 'workflows', 'id',
     'workflow_runs_workflow_id_fkey', 'fk_workflow_runs_workflow_id'),
    ('workflow_runs', 'user_id', 'users', 'id',
     'workflow_runs_user_id_fkey', 'fk_workflow_runs_user_id'),
    # ---- p1_modules_001 tables ----
    ('crews', 'user_id', 'users', 'id',
     'crews_user_id_fkey', 'fk_crews_user_id'),
    ('crew_runs', 'crew_id', 'crews', 'id',
     'crew_runs_crew_id_fkey', 'fk_crew_runs_crew_id'),
    ('crew_runs', 'user_id', 'users', 'id',
     'crew_runs_user_id_fkey', 'fk_crew_runs_user_id'),
    ('voice_profiles', 'user_id', 'users', 'id',
     'voice_profiles_user_id_fkey', 'fk_voice_profiles_user_id'),
    ('speech_syntheses', 'user_id', 'users', 'id',
     'speech_syntheses_user_id_fkey', 'fk_speech_syntheses_user_id'),
    ('speech_syntheses', 'voice_id', 'voice_profiles', 'id',
     'speech_syntheses_voice_id_fkey', 'fk_speech_syntheses_voice_id'),
    ('realtime_sessions', 'user_id', 'users', 'id',
     'realtime_sessions_user_id_fkey', 'fk_realtime_sessions_user_id'),
    ('security_scans', 'user_id', 'users', 'id',
     'security_scans_user_id_fkey', 'fk_security_scans_user_id'),
    ('audit_logs', 'user_id', 'users', 'id',
     'audit_logs_user_id_fkey', 'fk_audit_logs_user_id'),
    ('guardrail_rules', 'user_id', 'users', 'id',
     'guardrail_rules_user_id_fkey', 'fk_guardrail_rules_user_id'),
    # ---- p2_modules_001 tables ----
    ('image_projects', 'user_id', 'users', 'id',
     'image_projects_user_id_fkey', 'fk_image_projects_user_id'),
    ('generated_images', 'user_id', 'users', 'id',
     'generated_images_user_id_fkey', 'fk_generated_images_user_id'),
    ('datasets', 'user_id', 'users', 'id',
     'datasets_user_id_fkey', 'fk_datasets_user_id'),
    ('data_analyses', 'dataset_id', 'datasets', 'id',
     'data_analyses_dataset_id_fkey', 'fk_data_analyses_dataset_id'),
    ('data_analyses', 'user_id', 'users', 'id',
     'data_analyses_user_id_fkey', 'fk_data_analyses_user_id'),
    ('video_projects', 'user_id', 'users', 'id',
     'video_projects_user_id_fkey', 'fk_video_projects_user_id'),
    ('generated_videos', 'user_id', 'users', 'id',
     'generated_videos_user_id_fkey', 'fk_generated_videos_user_id'),
    # ---- p3_fine_tuning_001 tables ----
    ('training_datasets', 'user_id', 'users', 'id',
     'training_datasets_user_id_fkey', 'fk_training_datasets_user_id'),
    ('fine_tune_jobs', 'user_id', 'users', 'id',
     'fine_tune_jobs_user_id_fkey', 'fk_fine_tune_jobs_user_id'),
    ('fine_tune_jobs', 'dataset_id', 'training_datasets', 'id',
     'fine_tune_jobs_dataset_id_fkey', 'fk_fine_tune_jobs_dataset_id'),
    ('model_evaluations', 'job_id', 'fine_tune_jobs', 'id',
     'model_evaluations_job_id_fkey', 'fk_model_evaluations_job_id'),
    ('model_evaluations', 'user_id', 'users', 'id',
     'model_evaluations_user_id_fkey', 'fk_model_evaluations_user_id'),
    # ---- skill_seekers_001 ----
    ('scrape_jobs', 'user_id', 'users', 'id',
     'scrape_jobs_user_id_fkey', 'fk_scrape_jobs_user_id'),
    # ---- notifications_001 ----
    ('notifications', 'user_id', 'users', 'id',
     'notifications_user_id_fkey', 'fk_notifications_user_id'),
    # ---- audio_studio_001 ----
    ('audio_files', 'user_id', 'users', 'id',
     'audio_files_user_id_fkey', 'fk_audio_files_user_id'),
    ('podcast_episodes', 'user_id', 'users', 'id',
     'podcast_episodes_user_id_fkey', 'fk_podcast_episodes_user_id'),
    ('podcast_episodes', 'audio_id', 'audio_files', 'id',
     'podcast_episodes_audio_id_fkey', 'fk_podcast_episodes_audio_id'),
    # ---- repo_analyzer_001 ----
    ('repo_analyses', 'user_id', 'users', 'id',
     'repo_analyses_user_id_fkey', 'fk_repo_analyses_user_id'),
    # ---- consolidate_015 tables ----
    ('social_accounts', 'user_id', 'users', 'id',
     'social_accounts_user_id_fkey', 'fk_social_accounts_user_id'),
    ('social_posts', 'user_id', 'users', 'id',
     'social_posts_user_id_fkey', 'fk_social_posts_user_id'),
    ('integration_connectors', 'user_id', 'users', 'id',
     'integration_connectors_user_id_fkey', 'fk_integration_connectors_user_id'),
    ('webhook_events', 'connector_id', 'integration_connectors', 'id',
     'webhook_events_connector_id_fkey', 'fk_webhook_events_connector_id'),
    ('integration_triggers', 'user_id', 'users', 'id',
     'integration_triggers_user_id_fkey', 'fk_integration_triggers_user_id'),
    ('integration_triggers', 'connector_id', 'integration_connectors', 'id',
     'integration_triggers_connector_id_fkey', 'fk_integration_triggers_connector_id'),
    ('chatbots', 'user_id', 'users', 'id',
     'chatbots_user_id_fkey', 'fk_chatbots_user_id'),
    ('chatbot_conversations', 'chatbot_id', 'chatbots', 'id',
     'chatbot_conversations_chatbot_id_fkey', 'fk_chatbot_conversations_chatbot_id'),
    ('marketplace_listings', 'author_id', 'users', 'id',
     'marketplace_listings_author_id_fkey', 'fk_marketplace_listings_author_id'),
    ('marketplace_reviews', 'user_id', 'users', 'id',
     'marketplace_reviews_user_id_fkey', 'fk_marketplace_reviews_user_id'),
    ('marketplace_reviews', 'listing_id', 'marketplace_listings', 'id',
     'marketplace_reviews_listing_id_fkey', 'fk_marketplace_reviews_listing_id'),
    ('marketplace_installs', 'user_id', 'users', 'id',
     'marketplace_installs_user_id_fkey', 'fk_marketplace_installs_user_id'),
    ('marketplace_installs', 'listing_id', 'marketplace_listings', 'id',
     'marketplace_installs_listing_id_fkey', 'fk_marketplace_installs_listing_id'),
    ('presentations', 'user_id', 'users', 'id',
     'presentations_user_id_fkey', 'fk_presentations_user_id'),
    ('sandboxes', 'user_id', 'users', 'id',
     'sandboxes_user_id_fkey', 'fk_sandboxes_user_id'),
    ('ai_forms', 'user_id', 'users', 'id',
     'ai_forms_user_id_fkey', 'fk_ai_forms_user_id'),
    ('form_responses', 'form_id', 'ai_forms', 'id',
     'form_responses_form_id_fkey', 'fk_form_responses_form_id'),
    ('pdf_documents', 'user_id', 'users', 'id',
     'pdf_documents_user_id_fkey', 'fk_pdf_documents_user_id'),
]


def _group_by_table(specs):
    grouped = {}
    for spec in specs:
        table = spec[0]
        grouped.setdefault(table, []).append(spec)
    return grouped


def upgrade() -> None:
    for table, fks in _group_by_table(FK_SPECS).items():
        with op.batch_alter_table(table, schema=None) as batch_op:
            for _tbl, col, ref_table, ref_col, old_name, new_name in fks:
                batch_op.drop_constraint(old_name, type_='foreignkey')
                batch_op.create_foreign_key(
                    new_name,
                    ref_table,
                    [col],
                    [ref_col],
                    ondelete='CASCADE',
                )


def downgrade() -> None:
    for table, fks in _group_by_table(FK_SPECS).items():
        with op.batch_alter_table(table, schema=None) as batch_op:
            for _tbl, col, ref_table, ref_col, old_name, new_name in fks:
                batch_op.drop_constraint(new_name, type_='foreignkey')
                batch_op.create_foreign_key(
                    old_name,
                    ref_table,
                    [col],
                    [ref_col],
                )
