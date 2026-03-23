"""
Knowledge Base service - Document processing, chunking, search, and RAG.

Uses TF-IDF + cosine similarity for the MVP. Can be upgraded to pgvector later.
"""

import json
import math
import re
from collections import Counter
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.knowledge import Document, DocumentChunk, DocumentStatus

logger = structlog.get_logger()

# Chunk configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


class KnowledgeService:
    """Service for knowledge base operations."""

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
        """Split text into overlapping chunks."""
        if not text.strip():
            return []

        # Split by paragraphs first, then by sentences
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += ("\n\n" + para) if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Start new chunk with overlap from previous
                if overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks if chunks else [text.strip()[:chunk_size]]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple tokenizer: lowercase, split on non-alphanumeric."""
        return re.findall(r'[a-z0-9]+', text.lower())

    @staticmethod
    def _compute_tf(tokens: list[str]) -> dict[str, float]:
        """Compute term frequency."""
        counts = Counter(tokens)
        total = len(tokens)
        return {term: count / total for term, count in counts.items()} if total > 0 else {}

    @staticmethod
    def _cosine_similarity(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
        """Compute cosine similarity between two term vectors."""
        common = set(vec_a.keys()) & set(vec_b.keys())
        if not common:
            return 0.0

        dot_product = sum(vec_a[t] * vec_b[t] for t in common)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    @staticmethod
    async def upload_document(
        user_id: UUID,
        filename: str,
        content_type: str,
        text_content: str,
        session: AsyncSession,
    ) -> Document:
        """Upload and index a document."""
        # Create document record
        document = Document(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            status=DocumentStatus.PROCESSING,
        )
        session.add(document)
        await session.flush()

        try:
            # Chunk the text
            chunks = KnowledgeService._chunk_text(text_content)

            # Store chunks
            for i, chunk_text in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document.id,
                    user_id=user_id,
                    content=chunk_text,
                    chunk_index=i,
                    metadata_json=json.dumps({"filename": filename, "chunk_index": i}),
                )
                session.add(chunk)

            document.total_chunks = len(chunks)
            document.status = DocumentStatus.INDEXED
            document.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(document)

            logger.info(
                "document_indexed",
                document_id=str(document.id),
                filename=filename,
                chunks=len(chunks),
            )

        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.error = str(e)[:1000]
            document.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(document)
            logger.error("document_indexing_failed", error=str(e))

        return document

    @staticmethod
    async def index_text_content(
        user_id: UUID,
        filename: str,
        content: str,
        content_type: str = "text/markdown",
        session: AsyncSession = None,
    ) -> Optional[dict]:
        """Index raw text content into the knowledge base."""
        if not content.strip():
            return None

        # Create document record
        doc = Document(
            user_id=user_id,
            filename=filename[:255],
            content_type=content_type,
            total_chunks=0,
            status=DocumentStatus.PROCESSING,
        )
        session.add(doc)
        await session.flush()

        # Chunk the content
        chunks = KnowledgeService._chunk_text(content)

        for i, chunk_text in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=doc.id,
                user_id=user_id,
                content=chunk_text,
                chunk_index=i,
                metadata_json=json.dumps({"filename": filename[:255], "chunk_index": i}),
            )
            session.add(chunk)

        doc.total_chunks = len(chunks)
        doc.status = DocumentStatus.INDEXED
        doc.updated_at = datetime.utcnow()
        session.add(doc)
        await session.commit()

        return {"document_id": str(doc.id), "total_chunks": len(chunks)}

    @staticmethod
    async def list_documents(
        user_id: UUID,
        session: AsyncSession,
    ) -> list[Document]:
        """List all documents for a user."""
        result = await session.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_document(
        document_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ) -> bool:
        """Delete a document and its chunks."""
        document = await session.get(Document, document_id)
        if not document or document.user_id != user_id:
            return False

        # Delete chunks first
        chunk_result = await session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        for chunk in chunk_result.scalars().all():
            await session.delete(chunk)

        await session.delete(document)
        await session.commit()

        logger.info("document_deleted", document_id=str(document_id))
        return True

    @staticmethod
    async def search(
        user_id: UUID,
        query: str,
        session: AsyncSession,
        limit: int = 5,
    ) -> list[dict]:
        """Search documents using TF-IDF cosine similarity."""
        # Get all user chunks
        result = await session.execute(
            select(DocumentChunk, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.user_id == user_id)
        )
        rows = result.all()

        if not rows:
            return []

        # Compute query TF vector
        query_tokens = KnowledgeService._tokenize(query)
        query_tf = KnowledgeService._compute_tf(query_tokens)

        # Score each chunk
        scored = []
        for chunk, filename in rows:
            chunk_tokens = KnowledgeService._tokenize(chunk.content)
            chunk_tf = KnowledgeService._compute_tf(chunk_tokens)
            score = KnowledgeService._cosine_similarity(query_tf, chunk_tf)

            if score > 0:
                scored.append({
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "filename": filename,
                    "content": chunk.content,
                    "score": round(score, 4),
                    "chunk_index": chunk.chunk_index,
                })

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    @staticmethod
    async def rag_query(
        user_id: UUID,
        question: str,
        session: AsyncSession,
        limit: int = 5,
    ) -> dict:
        """Answer a question using RAG: retrieve relevant chunks then ask AI."""
        # Search for relevant chunks
        sources = await KnowledgeService.search(user_id, question, session, limit)

        # Build context from sources
        if sources:
            context_parts = []
            for i, source in enumerate(sources):
                context_parts.append(
                    f"[Source {i+1}: {source['filename']}]\n{source['content']}"
                )
            context = "\n\n".join(context_parts)
        else:
            context = "No relevant documents found in the knowledge base."

        # Ask AI with context
        prompt = (
            f"Based on the following context from the user's knowledge base, "
            f"answer the question. If the answer cannot be found in the context, "
            f"say so clearly.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        )

        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=prompt,
                task="rag_answer",
                provider_name="gemini",
                user_id=user_id,
                module="knowledge",
            )
            answer = result.get("processed_text", "Unable to generate answer.")
            provider = result.get("provider", "gemini")
        except Exception as e:
            logger.error("rag_query_failed", error=str(e))
            answer = f"Error generating answer: {str(e)}"
            provider = "error"

        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "provider": provider,
        }
