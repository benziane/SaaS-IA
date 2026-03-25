"""Add pgvector extension and embedding column to document_chunks

Revision ID: pgvector_001
Revises: p3_fine_tuning_001
Create Date: 2026-03-23

Adds:
- pgvector extension (CREATE EXTENSION IF NOT EXISTS vector)
- embedding vector(384) column on document_chunks (nullable for backward compat)
- HNSW index for fast cosine similarity search
- embedding_model column on documents to track which model was used
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'pgvector_001'
down_revision: Union[str, None] = 'p3_fine_tuning_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding column (384 dimensions = all-MiniLM-L6-v2 output size)
    op.execute(
        "ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding vector(384)"
    )

    # Create HNSW index for fast cosine similarity search
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )

    # Add embedding_model column to documents to track which model generated embeddings
    op.add_column(
        'documents',
        sa.Column('embedding_model', sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('documents', 'embedding_model')
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding")
    # Don't drop the extension as other things might use it
