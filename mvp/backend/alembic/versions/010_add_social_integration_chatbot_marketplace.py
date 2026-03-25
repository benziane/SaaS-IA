"""Add social_publisher, integration_hub, ai_chatbot_builder, marketplace tables

Revision ID: 010abc123def
Revises: mem_search_001
Create Date: 2026-03-25
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '010abc123def'
down_revision: Union[str, None] = 'mem_search_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- Social Publisher ----
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

    # ---- Integration Hub ----
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

    # ---- AI Chatbot Builder ----
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

    # ---- Marketplace ----
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


def downgrade() -> None:
    # Drop in reverse order (child tables first to avoid FK violations)
    op.drop_table('marketplace_installs')
    op.drop_table('marketplace_reviews')
    op.drop_table('marketplace_listings')
    op.drop_table('chatbot_conversations')
    op.drop_table('chatbots')
    op.drop_table('integration_triggers')
    op.drop_table('webhook_events')
    op.drop_table('integration_connectors')
    op.drop_table('social_posts')
    op.drop_table('social_accounts')
