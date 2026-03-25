"""
Knowledge Base service - Document processing, chunking, search, and RAG.

Search modes (auto-selected):
- TF-IDF (legacy, always available) - original cosine similarity
- Vector search (pgvector + sentence-transformers) - semantic embeddings
- Hybrid search (TF-IDF + vector, auto-selected when embeddings exist)
"""

import json
import math
import re
from collections import Counter
from datetime import UTC, datetime
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

            # Generate embeddings if sentence-transformers is available
            from app.modules.knowledge import embedding_service
            embeddings = None
            if embedding_service.is_available():
                chunk_texts = [c for c in chunks]
                embeddings = embedding_service.embed_texts(chunk_texts)
                document.embedding_model = embedding_service.get_model_name()

            # Store chunks (with embeddings if available)
            for i, chunk_text in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document.id,
                    user_id=user_id,
                    content=chunk_text,
                    chunk_index=i,
                    metadata_json=json.dumps({"filename": filename, "chunk_index": i}),
                )
                session.add(chunk)
                await session.flush()

                # Store embedding via raw SQL (pgvector column not in SQLModel)
                if embeddings and embeddings[i] is not None:
                    emb_str = "[" + ",".join(str(v) for v in embeddings[i]) + "]"
                    await session.execute(
                        __import__("sqlalchemy").text(
                            "UPDATE document_chunks SET embedding = :emb WHERE id = :cid"
                        ),
                        {"emb": emb_str, "cid": str(chunk.id)},
                    )

            document.total_chunks = len(chunks)
            document.status = DocumentStatus.INDEXED
            document.updated_at = datetime.now(UTC)

            await session.commit()
            await session.refresh(document)

            has_vectors = embeddings is not None and any(e is not None for e in embeddings)
            logger.info(
                "document_indexed",
                document_id=str(document.id),
                filename=filename,
                chunks=len(chunks),
                vector_search_enabled=has_vectors,
            )

        except Exception as e:
            document.status = DocumentStatus.FAILED
            document.error = str(e)[:1000]
            document.updated_at = datetime.now(UTC)
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
        doc.updated_at = datetime.now(UTC)
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
    async def list_document_chunks(
        document_id: UUID,
        user_id: UUID,
        session: AsyncSession,
    ):
        """List all chunks for a document, verifying ownership."""
        document = await session.get(Document, document_id)
        if not document or document.user_id != user_id:
            return None
        result = await session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
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
        """Smart search: uses hybrid (vector + TF-IDF) when embeddings exist, falls back to TF-IDF.

        This method auto-detects the best search strategy:
        1. If pgvector embeddings exist -> hybrid search (best quality)
        2. Otherwise -> TF-IDF cosine similarity (legacy, always works)
        """
        # Try hybrid search first (pgvector + TF-IDF fusion)
        try:
            from app.modules.knowledge import embedding_service
            if embedding_service.is_available():
                hybrid_results = await KnowledgeService.search_hybrid(
                    user_id, query, session, limit
                )
                if hybrid_results:
                    return hybrid_results
        except Exception as e:
            logger.debug("hybrid_search_fallback", reason=str(e))

        # Fallback: original TF-IDF search (always works)
        return await KnowledgeService.search_tfidf(user_id, query, session, limit)

    @staticmethod
    async def search_tfidf(
        user_id: UUID,
        query: str,
        session: AsyncSession,
        limit: int = 5,
    ) -> list[dict]:
        """Original TF-IDF cosine similarity search (legacy, always available)."""
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
    async def search_vector(
        user_id: UUID,
        query: str,
        session: AsyncSession,
        limit: int = 5,
    ) -> list[dict]:
        """Semantic vector search using pgvector cosine similarity.

        Requires embeddings to be generated (sentence-transformers + pgvector).
        Returns empty list if embeddings are not available.
        """
        from app.modules.knowledge import embedding_service

        query_embedding = embedding_service.embed_text(query)
        if query_embedding is None:
            return []

        emb_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        try:
            import sqlalchemy as sa
            # pgvector cosine distance: 1 - cosine_similarity (lower = more similar)
            sql = sa.text("""
                SELECT
                    dc.id AS chunk_id,
                    dc.document_id,
                    d.filename,
                    dc.content,
                    dc.chunk_index,
                    1 - (dc.embedding <=> :query_emb::vector) AS score
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE dc.user_id = :uid
                  AND dc.embedding IS NOT NULL
                ORDER BY dc.embedding <=> :query_emb::vector
                LIMIT :lim
            """)

            result = await session.execute(
                sql, {"uid": str(user_id), "query_emb": emb_str, "lim": limit}
            )
            rows = result.fetchall()

            return [
                {
                    "chunk_id": row[0],
                    "document_id": row[1],
                    "filename": row[2],
                    "content": row[3],
                    "chunk_index": row[4],
                    "score": round(float(row[5]), 4),
                }
                for row in rows
                if row[5] and float(row[5]) > 0.1  # filter low-quality matches
            ]

        except Exception as e:
            logger.warning("vector_search_failed", error=str(e))
            return []

    @staticmethod
    async def search_hybrid(
        user_id: UUID,
        query: str,
        session: AsyncSession,
        limit: int = 5,
        vector_weight: float = 0.7,
    ) -> list[dict]:
        """Hybrid search: combines vector similarity (70%) with TF-IDF (30%).

        Reciprocal Rank Fusion (RRF) merges results from both methods
        for better precision and recall than either alone.
        """
        # Run both searches
        vector_results = await KnowledgeService.search_vector(
            user_id, query, session, limit=limit * 2
        )
        tfidf_results = await KnowledgeService.search_tfidf(
            user_id, query, session, limit=limit * 2
        )

        if not vector_results:
            return tfidf_results[:limit]
        if not tfidf_results:
            return vector_results[:limit]

        # Reciprocal Rank Fusion (RRF)
        k = 60  # RRF constant
        rrf_scores: dict[str, dict] = {}

        for rank, result in enumerate(vector_results):
            cid = str(result["chunk_id"])
            rrf_scores[cid] = result.copy()
            rrf_scores[cid]["rrf_score"] = vector_weight * (1.0 / (k + rank + 1))

        for rank, result in enumerate(tfidf_results):
            cid = str(result["chunk_id"])
            tfidf_rrf = (1 - vector_weight) * (1.0 / (k + rank + 1))
            if cid in rrf_scores:
                rrf_scores[cid]["rrf_score"] += tfidf_rrf
            else:
                rrf_scores[cid] = result.copy()
                rrf_scores[cid]["rrf_score"] = tfidf_rrf

        # Sort by RRF score
        merged = sorted(rrf_scores.values(), key=lambda x: x["rrf_score"], reverse=True)

        # Normalize scores to 0-1 range
        for item in merged:
            item["score"] = round(item.pop("rrf_score") * 100, 4)

        return merged[:limit]

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

            # Track AI cost for RAG query
            try:
                from app.modules.cost_tracker.tracker import track_ai_usage
                await track_ai_usage(
                    user_id=user_id,
                    provider="gemini",
                    model=result.get("model", "gemini-2.5-flash"),
                    module="knowledge",
                    action="rag_query",
                    input_tokens=0,
                    output_tokens=0,
                    latency_ms=0,
                    success=True,
                    session=session,
                )
            except Exception:
                pass  # Cost tracking should never break main flow

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
