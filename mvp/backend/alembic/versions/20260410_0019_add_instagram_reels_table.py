"""add_instagram_reels_table

Revision ID: instagram_reels_019
Revises: email_verified_018
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = 'instagram_reels_019'
down_revision: str = 'email_verified_018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'instagram_reels',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('username', sqlmodel.AutoString(length=100), nullable=False),
        sa.Column('reel_id', sqlmodel.AutoString(length=100), nullable=False),
        sa.Column('reel_url', sqlmodel.AutoString(length=500), nullable=False),
        sa.Column('caption', sqlmodel.AutoString(length=2200), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('comments', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('views', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration_seconds', sa.Float(), nullable=False, server_default='0'),
        sa.Column('thumbnail_url', sqlmodel.AutoString(length=500), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('transcript_language', sqlmodel.AutoString(length=10), nullable=True),
        sa.Column('sentiment_label', sqlmodel.AutoString(length=20), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('provider', sqlmodel.AutoString(length=50), nullable=False, server_default='mock'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_instagram_reels_user_id', 'instagram_reels', ['user_id'])
    op.create_index('ix_instagram_reels_username', 'instagram_reels', ['username'])
    op.create_index('ix_instagram_reels_reel_id', 'instagram_reels', ['reel_id'])


def downgrade() -> None:
    op.drop_index('ix_instagram_reels_reel_id', table_name='instagram_reels')
    op.drop_index('ix_instagram_reels_username', table_name='instagram_reels')
    op.drop_index('ix_instagram_reels_user_id', table_name='instagram_reels')
    op.drop_table('instagram_reels')
