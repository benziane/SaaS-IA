"""Add user_memories table for AI memory module

Revision ID: mem_search_001
Revises: pgvector_001
Create Date: 2026-03-24
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'mem_search_001'
down_revision: Union[str, None] = 'pgvector_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('user_memories',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('memory_type', sa.String(50), nullable=False, server_default='fact'),
        sa.Column('content', sa.String(2000), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.8'),
        sa.Column('source', sa.String(50), nullable=False, server_default='manual'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_memories_user_id', 'user_memories', ['user_id'])


def downgrade() -> None:
    op.drop_table('user_memories')
