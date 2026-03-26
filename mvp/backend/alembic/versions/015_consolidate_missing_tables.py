"""Consolidate missing tables: social, integration, chatbot, marketplace,
presentations, sandbox, forms, tenants, pdf_documents

Revision ID: consolidate_015
Revises: secrets_mgr_001
Create Date: 2026-03-26

Merges all tables that existed only in the removed duplicate chain (010-014)
into a single migration appended to the linear chain.

Tables created:
- social_accounts, social_posts           (social_publisher)
- integration_connectors, webhook_events,
  integration_triggers                    (integration_hub)
- chatbots, chatbot_conversations         (ai_chatbot_builder)
- marketplace_listings, marketplace_reviews,
  marketplace_installs                    (marketplace)
- presentations                           (presentation_gen)
- sandboxes                               (code_sandbox)
- ai_forms, form_responses               (ai_forms)
- tenants + users.tenant_id FK           (tenants)
- pdf_documents                           (pdf_processor)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'consolidate_015'
down_revision: Union[str, None] = 'secrets_mgr_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================================================================
    # Social Publisher
    # ==================================================================
    op.create_table('social_accounts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('account_name', sa.String(200), nullable=False),
        sa.Column('access_token_hash', sa.String(500), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_social_accounts_user_id', 'social_accounts', ['user_id'])
    op.create_index('ix_social_accounts_platform', 'social_accounts', ['platform'])

    op.create_table('social_posts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('platforms_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('schedule_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('results_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('media_urls_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('hashtags_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_social_posts_user_id', 'social_posts', ['user_id'])
    op.create_index('ix_social_posts_status', 'social_posts', ['status'])

    # ==================================================================
    # Integration Hub
    # ==================================================================
    op.create_table('integration_connectors',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False, server_default='custom'),
        sa.Column('config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('events_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_event_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_integration_connectors_user_id', 'integration_connectors', ['user_id'])

    op.create_table('webhook_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('connector_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.String(200), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(20), nullable=False, server_default='received'),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['connector_id'], ['integration_connectors.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_webhook_events_connector_id', 'webhook_events', ['connector_id'])

    op.create_table('integration_triggers',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('connector_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.String(200), nullable=False),
        sa.Column('action_module', sa.String(100), nullable=False),
        sa.Column('action_config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('executions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['connector_id'], ['integration_connectors.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_integration_triggers_user_id', 'integration_triggers', ['user_id'])
    op.create_index('ix_integration_triggers_connector_id', 'integration_triggers', ['connector_id'])

    # ==================================================================
    # AI Chatbot Builder
    # ==================================================================
    op.create_table('chatbots',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('model', sa.String(50), nullable=False, server_default='gemini'),
        sa.Column('knowledge_base_ids', sa.Text(), nullable=True),
        sa.Column('personality', sa.String(50), nullable=False, server_default='professional'),
        sa.Column('welcome_message', sa.String(1000), nullable=True),
        sa.Column('theme', sa.Text(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('embed_token', sa.String(100), nullable=True, unique=True),
        sa.Column('channels', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('conversations_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chatbots_user_id', 'chatbots', ['user_id'])
    op.create_index('ix_chatbots_is_deleted', 'chatbots', ['is_deleted'])

    op.create_table('chatbot_conversations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('chatbot_id', sa.Uuid(), nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('messages', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('satisfaction_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['chatbot_id'], ['chatbots.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chatbot_conversations_chatbot_id', 'chatbot_conversations', ['chatbot_id'])
    op.create_index('ix_chatbot_conversations_session_id', 'chatbot_conversations', ['session_id'])

    # ==================================================================
    # Marketplace
    # ==================================================================
    op.create_table('marketplace_listings',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('author_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('price', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0.0'),
        sa.Column('content_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('tags_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('preview_images_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('rating', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('reviews_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('installs_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['author_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_marketplace_listings_author_id', 'marketplace_listings', ['author_id'])
    op.create_index('ix_marketplace_listings_type', 'marketplace_listings', ['type'])
    op.create_index('ix_marketplace_listings_category', 'marketplace_listings', ['category'])
    op.create_index('ix_marketplace_listings_is_deleted', 'marketplace_listings', ['is_deleted'])

    op.create_table('marketplace_reviews',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('listing_id', sa.Uuid(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['listing_id'], ['marketplace_listings.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'listing_id', name='uq_marketplace_review_user_listing'),
    )
    op.create_index('ix_marketplace_reviews_user_id', 'marketplace_reviews', ['user_id'])
    op.create_index('ix_marketplace_reviews_listing_id', 'marketplace_reviews', ['listing_id'])

    op.create_table('marketplace_installs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('listing_id', sa.Uuid(), nullable=False),
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0.0'),
        sa.Column('installed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['listing_id'], ['marketplace_listings.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_marketplace_installs_user_id', 'marketplace_installs', ['user_id'])
    op.create_index('ix_marketplace_installs_listing_id', 'marketplace_installs', ['listing_id'])

    # ==================================================================
    # Presentation Gen
    # ==================================================================
    op.create_table('presentations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('topic', sa.String(1000), nullable=False),
        sa.Column('num_slides', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('style', sa.String(50), nullable=False, server_default='professional'),
        sa.Column('template', sa.String(50), nullable=False, server_default='default'),
        sa.Column('slides_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(20), nullable=False, server_default='generating'),
        sa.Column('format', sa.String(20), nullable=False, server_default='json'),
        sa.Column('download_url', sa.String(500), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_presentations_user_id', 'presentations', ['user_id'])

    # ==================================================================
    # Code Sandbox
    # ==================================================================
    op.create_table('sandboxes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('language', sa.String(30), nullable=False, server_default='python'),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('cells_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sandboxes_user_id', 'sandboxes', ['user_id'])
    op.create_index('ix_sandboxes_is_deleted', 'sandboxes', ['is_deleted'])

    # ==================================================================
    # AI Forms
    # ==================================================================
    op.create_table('ai_forms',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('fields_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('style', sa.String(50), nullable=False, server_default='conversational'),
        sa.Column('thank_you_message', sa.String(1000), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('share_token', sa.String(100), nullable=True, unique=True),
        sa.Column('responses_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ai_forms_user_id', 'ai_forms', ['user_id'])
    op.create_index('ix_ai_forms_is_deleted', 'ai_forms', ['is_deleted'])

    op.create_table('form_responses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('form_id', sa.Uuid(), nullable=False),
        sa.Column('answers_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('analysis', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['form_id'], ['ai_forms.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_form_responses_form_id', 'form_responses', ['form_id'])

    # ==================================================================
    # Tenants (multi-tenant RLS)
    # ==================================================================
    op.create_table('tenants',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('plan', sa.String(50), nullable=False, server_default='free'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('config_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('branding_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('max_users', sa.Integer(), nullable=False, server_default=sa.text('5')),
        sa.Column('max_storage_mb', sa.Integer(), nullable=False, server_default=sa.text('1000')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True)
    op.create_index('ix_tenants_plan', 'tenants', ['plan'])
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'])

    # Add tenant_id to users
    op.add_column('users', sa.Column('tenant_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        'fk_users_tenant_id', 'users', 'tenants',
        ['tenant_id'], ['id'], ondelete='SET NULL',
    )
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])

    # ==================================================================
    # PDF Processor
    # ==================================================================
    op.create_table('pdf_documents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('num_pages', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('file_size_kb', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('pages_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('keywords_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(20), nullable=False, server_default='uploading'),
        sa.Column('file_path', sa.String(1000), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pdf_documents_user_id', 'pdf_documents', ['user_id'])
    op.create_index('ix_pdf_documents_status', 'pdf_documents', ['status'])
    op.create_index('ix_pdf_documents_created_at', 'pdf_documents', ['created_at'])


def downgrade() -> None:
    # PDF Processor
    op.drop_index('ix_pdf_documents_created_at', table_name='pdf_documents')
    op.drop_index('ix_pdf_documents_status', table_name='pdf_documents')
    op.drop_index('ix_pdf_documents_user_id', table_name='pdf_documents')
    op.drop_table('pdf_documents')

    # Tenants
    op.drop_constraint('fk_users_tenant_id', 'users', type_='foreignkey')
    op.drop_index('ix_users_tenant_id', table_name='users')
    op.drop_column('users', 'tenant_id')
    op.drop_index('ix_tenants_is_active', table_name='tenants')
    op.drop_index('ix_tenants_plan', table_name='tenants')
    op.drop_index('ix_tenants_slug', table_name='tenants')
    op.drop_table('tenants')

    # AI Forms
    op.drop_index('ix_form_responses_form_id', table_name='form_responses')
    op.drop_table('form_responses')
    op.drop_index('ix_ai_forms_is_deleted', table_name='ai_forms')
    op.drop_index('ix_ai_forms_user_id', table_name='ai_forms')
    op.drop_table('ai_forms')

    # Code Sandbox
    op.drop_index('ix_sandboxes_is_deleted', table_name='sandboxes')
    op.drop_index('ix_sandboxes_user_id', table_name='sandboxes')
    op.drop_table('sandboxes')

    # Presentation Gen
    op.drop_index('ix_presentations_user_id', table_name='presentations')
    op.drop_table('presentations')

    # Marketplace
    op.drop_table('marketplace_installs')
    op.drop_table('marketplace_reviews')
    op.drop_table('marketplace_listings')

    # AI Chatbot Builder
    op.drop_table('chatbot_conversations')
    op.drop_table('chatbots')

    # Integration Hub
    op.drop_table('integration_triggers')
    op.drop_table('webhook_events')
    op.drop_table('integration_connectors')

    # Social Publisher
    op.drop_table('social_posts')
    op.drop_table('social_accounts')
