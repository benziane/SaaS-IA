"""Add presentations, sandboxes, ai_forms, form_responses tables

Revision ID: 011def456abc
Revises: 010abc123def
Create Date: 2026-03-25
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '011def456abc'
down_revision: Union[str, None] = '010abc123def'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- Presentation Gen ----
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

    # ---- Code Sandbox ----
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

    # ---- AI Forms ----
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

    # ---- Form Responses ----
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


def downgrade() -> None:
    # Drop in reverse order (form_responses depends on ai_forms)
    op.drop_index('ix_form_responses_form_id', table_name='form_responses')
    op.drop_table('form_responses')

    op.drop_index('ix_ai_forms_is_deleted', table_name='ai_forms')
    op.drop_index('ix_ai_forms_user_id', table_name='ai_forms')
    op.drop_table('ai_forms')

    op.drop_index('ix_sandboxes_is_deleted', table_name='sandboxes')
    op.drop_index('ix_sandboxes_user_id', table_name='sandboxes')
    op.drop_table('sandboxes')

    op.drop_index('ix_presentations_user_id', table_name='presentations')
    op.drop_table('presentations')
