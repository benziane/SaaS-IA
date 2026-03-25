"""Add audio_files and podcast_episodes tables for audio_studio module

Revision ID: audio_studio_001
Revises: notifications_001
Create Date: 2026-03-25
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'audio_studio_001'
down_revision: Union[str, None] = 'notifications_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Audio files table
    op.create_table('audio_files',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('duration_seconds', sa.Float(), nullable=False, server_default='0'),
        sa.Column('sample_rate', sa.Integer(), nullable=False, server_default='44100'),
        sa.Column('channels', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('format', sa.String(20), nullable=False, server_default='mp3'),
        sa.Column('file_size_kb', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('chapters_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('waveform_json', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='uploading'),
        sa.Column('file_path', sa.String(1000), nullable=False, server_default=''),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_audio_files_user_id', 'audio_files', ['user_id'])
    op.create_index('ix_audio_files_status', 'audio_files', ['status'])
    op.create_index(
        'ix_audio_files_user_active',
        'audio_files',
        ['user_id', 'is_deleted'],
        postgresql_where=sa.text('is_deleted = false'),
    )

    # Podcast episodes table
    op.create_table('podcast_episodes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('audio_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('show_notes', sa.Text(), nullable=True),
        sa.Column('publish_date', sa.DateTime(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['audio_id'], ['audio_files.id']),
    )
    op.create_index('ix_podcast_episodes_user_id', 'podcast_episodes', ['user_id'])
    op.create_index('ix_podcast_episodes_audio_id', 'podcast_episodes', ['audio_id'])
    op.create_index('ix_podcast_episodes_published', 'podcast_episodes', ['is_published'])


def downgrade() -> None:
    op.drop_table('podcast_episodes')
    op.drop_table('audio_files')
