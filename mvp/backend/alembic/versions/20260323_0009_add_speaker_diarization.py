"""Add speaker diarization fields to transcriptions

Revision ID: diarize_001
Revises: agent_001
Create Date: 2026-03-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'diarize_001'
down_revision: Union[str, None] = 'agent_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('transcriptions', sa.Column('speakers_json', sa.Text(), nullable=True))
    op.add_column('transcriptions', sa.Column('speaker_count', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('transcriptions', 'speaker_count')
    op.drop_column('transcriptions', 'speakers_json')
