"""Sprint 4: Add compare tables (comparison_results, comparison_votes)

Revision ID: sprint4_001
Revises: sprint3_001
Create Date: 2026-03-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'sprint4_001'
down_revision: Union[str, None] = 'sprint3_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index('ix_comparison_votes_user_id', table_name='comparison_votes')
    op.drop_index('ix_comparison_votes_comparison_id', table_name='comparison_votes')
    op.drop_table('comparison_votes')
    op.drop_index('ix_comparison_results_user_id', table_name='comparison_results')
    op.drop_table('comparison_results')
