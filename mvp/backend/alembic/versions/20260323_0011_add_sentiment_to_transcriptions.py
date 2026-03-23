"""Add sentiment fields to transcriptions

Revision ID: sentiment_001
Revises: cost_001
Create Date: 2026-03-23
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'sentiment_001'
down_revision: Union[str, None] = 'cost_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('transcriptions', sa.Column('sentiment_json', sa.Text(), nullable=True))
    op.add_column('transcriptions', sa.Column('sentiment_score', sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column('transcriptions', 'sentiment_score')
    op.drop_column('transcriptions', 'sentiment_json')
