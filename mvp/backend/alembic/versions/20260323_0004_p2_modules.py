"""Add P2 modules: image_gen, data_analyst, video_gen

Revision ID: p2_modules_001
Revises: p1_modules_001
Create Date: 2026-03-23
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'p2_modules_001'
down_revision: Union[str, None] = 'p1_modules_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- Image Gen ----
    op.create_table('image_projects',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('image_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_image_projects_user_id', 'image_projects', ['user_id'])

    op.create_table('generated_images',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('prompt', sa.String(5000), nullable=False),
        sa.Column('negative_prompt', sa.String(2000), nullable=True),
        sa.Column('style', sa.String(50), nullable=False, server_default='realistic'),
        sa.Column('provider', sa.String(50), nullable=False, server_default='gemini'),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('width', sa.Integer(), nullable=False, server_default='1024'),
        sa.Column('height', sa.Integer(), nullable=False, server_default='1024'),
        sa.Column('image_url', sa.String(2000), nullable=True),
        sa.Column('thumbnail_url', sa.String(2000), nullable=True),
        sa.Column('source_type', sa.String(50), nullable=False, server_default='prompt'),
        sa.Column('source_id', sa.String(200), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error', sa.String(1000), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_generated_images_user_id', 'generated_images', ['user_id'])

    # ---- Data Analyst ----
    op.create_table('datasets',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('filename', sa.String(300), nullable=False),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('row_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('column_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('columns_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('preview_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('stats_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(20), nullable=False, server_default='uploading'),
        sa.Column('error', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_datasets_user_id', 'datasets', ['user_id'])

    op.create_table('data_analyses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('dataset_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('question', sa.String(2000), nullable=False),
        sa.Column('analysis_type', sa.String(50), nullable=False, server_default='general'),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('charts_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('insights_json', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('code_executed', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('error', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_data_analyses_dataset_id', 'data_analyses', ['dataset_id'])
    op.create_index('ix_data_analyses_user_id', 'data_analyses', ['user_id'])

    # ---- Video Gen ----
    op.create_table('video_projects',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(1000), nullable=True),
        sa.Column('video_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_duration_s', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_video_projects_user_id', 'video_projects', ['user_id'])

    op.create_table('generated_videos',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('video_type', sa.String(50), nullable=False, server_default='text_to_video'),
        sa.Column('prompt', sa.String(5000), nullable=False, server_default=''),
        sa.Column('provider', sa.String(50), nullable=False, server_default='gemini'),
        sa.Column('source_type', sa.String(50), nullable=True),
        sa.Column('source_id', sa.String(200), nullable=True),
        sa.Column('video_url', sa.String(2000), nullable=True),
        sa.Column('thumbnail_url', sa.String(2000), nullable=True),
        sa.Column('duration_s', sa.Float(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=False, server_default='1920'),
        sa.Column('height', sa.Integer(), nullable=False, server_default='1080'),
        sa.Column('fps', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('format', sa.String(10), nullable=False, server_default='mp4'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error', sa.String(1000), nullable=True),
        sa.Column('settings_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_generated_videos_user_id', 'generated_videos', ['user_id'])


def downgrade() -> None:
    op.drop_table('generated_videos')
    op.drop_table('video_projects')
    op.drop_table('data_analyses')
    op.drop_table('datasets')
    op.drop_table('generated_images')
    op.drop_table('image_projects')
