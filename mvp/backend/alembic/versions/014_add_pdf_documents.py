"""Add pdf_documents table for PDF Processor module

Revision ID: 014ccc456ddd
Revises: 013bbb123ccc
Create Date: 2026-03-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '014ccc456ddd'
down_revision: Union[str, None] = '013bbb123ccc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    op.drop_index('ix_pdf_documents_created_at', table_name='pdf_documents')
    op.drop_index('ix_pdf_documents_status', table_name='pdf_documents')
    op.drop_index('ix_pdf_documents_user_id', table_name='pdf_documents')
    op.drop_table('pdf_documents')
