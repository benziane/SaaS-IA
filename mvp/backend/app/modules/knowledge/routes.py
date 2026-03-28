"""
Knowledge Base API routes - Document upload, search, and RAG queries.
"""

import json
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.knowledge.schemas import (
    AskRequest,
    AskResponse,
    ChunkRead,
    DocumentRead,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.modules.knowledge.service import KnowledgeService
from app.modules.billing.service import BillingService
from app.modules.billing.middleware import require_ai_call_quota
from app.cache import cache_get, cache_set
from app.rate_limit import limiter

router = APIRouter()

# Supported document types
ALLOWED_DOC_TYPES = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
}
MAX_DOC_SIZE = 10 * 1024 * 1024  # 10 MB


def _extract_text(content: bytes, filename: str) -> str:
    """Extract text content from uploaded file."""
    # For now, support plain text files only
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return content.decode("latin-1")
        except Exception:
            raise ValueError(f"Cannot decode file content: {filename}")


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="Document to index (TXT, MD, CSV)"),
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Upload a document to the knowledge base.

    Supported formats: TXT, MD, CSV.
    Maximum size: 10 MB.
    The document is chunked and indexed for semantic search.

    Rate limit: 5 requests/minute
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must have a filename.",
        )

    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in ALLOWED_DOC_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_DOC_TYPES.keys()))}",
        )

    content = await file.read()
    if len(content) > MAX_DOC_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_DOC_SIZE // (1024 * 1024)} MB.",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    text_content = _extract_text(content, file.filename)

    document = await KnowledgeService.upload_document(
        user_id=current_user.id,
        filename=file.filename,
        content_type=ALLOWED_DOC_TYPES.get(ext, "text/plain"),
        text_content=text_content,
        session=session,
    )

    return document


@router.get("/documents", response_model=list[DocumentRead])
@limiter.limit("20/minute")
async def list_documents(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List all documents in the user's knowledge base.

    Rate limit: 20 requests/minute
    """
    return await KnowledgeService.list_documents(current_user.id, session)


@router.get("/documents/{document_id}/chunks", response_model=list[ChunkRead])
@limiter.limit("20/minute")
async def list_document_chunks(
    request: Request,
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List all chunks for a specific document.

    Rate limit: 20 requests/minute
    """
    chunks = await KnowledgeService.list_document_chunks(document_id, current_user.id, session)
    if chunks is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return chunks


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_document(
    request: Request,
    document_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a document and its chunks from the knowledge base.

    Rate limit: 10 requests/minute
    """
    deleted = await KnowledgeService.delete_document(
        document_id, current_user.id, session
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return None


@router.post("/search", response_model=SearchResponse)
@limiter.limit("20/minute")
async def search_documents(
    request: Request,
    body: SearchRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Search documents using semantic similarity.

    Rate limit: 20 requests/minute
    """
    import hashlib
    cache_key = f"search:{current_user.id}:{hashlib.md5(body.query.encode()).hexdigest()}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return SearchResponse(**cached)

    results = await KnowledgeService.search(
        user_id=current_user.id,
        query=body.query,
        session=session,
        limit=body.limit,
    )

    # Cache for 2 minutes
    response = SearchResponse(
        query=body.query,
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )
    await cache_set(cache_key, response.model_dump(), ttl_seconds=120)
    return response


@router.post("/ask", response_model=AskResponse)
@limiter.limit("10/minute")
async def ask_question(
    request: Request,
    body: AskRequest,
    current_user: User = Depends(require_ai_call_quota),
    session: AsyncSession = Depends(get_session),
):
    """
    Ask a question using RAG (Retrieval-Augmented Generation).

    Retrieves relevant chunks from the knowledge base and uses AI
    to generate an answer with source citations.

    Rate limit: 10 requests/minute
    """
    result = await KnowledgeService.rag_query(
        user_id=current_user.id,
        question=body.question,
        session=session,
        limit=body.limit,
    )

    # Consume AI quota
    await BillingService.consume_quota(current_user.id, "ai_call", 1, session)

    return AskResponse(
        question=result["question"],
        answer=result["answer"],
        sources=[SearchResult(**s) for s in result["sources"]],
        provider=result["provider"],
    )


@router.post("/search/vector", response_model=SearchResponse)
@limiter.limit("20/minute")
async def search_vector(
    request: Request,
    body: SearchRequest,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Semantic vector search using pgvector embeddings.

    Requires sentence-transformers to be installed and documents to have embeddings.
    Falls back to empty results if vector search is unavailable.

    Rate limit: 20 requests/minute
    """
    results = await KnowledgeService.search_vector(
        user_id=current_user.id,
        query=body.query,
        session=session,
        limit=body.limit,
    )

    return SearchResponse(
        query=body.query,
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


@router.post("/reindex-embeddings", status_code=202)
@limiter.limit("1/minute")
async def reindex_embeddings(
    request: Request,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """
    Reindex all existing document chunks with vector embeddings.

    This is useful after enabling sentence-transformers on an existing knowledge base.
    Processes chunks that don't have embeddings yet.

    Rate limit: 1 request/minute
    """
    from app.modules.knowledge import embedding_service

    if not embedding_service.is_available():
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Embedding service not available. Install sentence-transformers.",
        )

    import sqlalchemy as sa

    # Get chunks without embeddings
    result = await session.execute(
        sa.text("""
            SELECT id, content FROM document_chunks
            WHERE user_id = :uid AND embedding IS NULL
            ORDER BY created_at
            LIMIT 500
        """),
        {"uid": str(current_user.id)},
    )
    rows = result.fetchall()

    if not rows:
        return {"message": "All chunks already have embeddings", "reindexed": 0}

    # Batch embed
    texts = [row[1] for row in rows]
    embeddings = embedding_service.embed_texts(texts)

    reindexed = 0
    for row, emb in zip(rows, embeddings):
        if emb is not None:
            emb_str = "[" + ",".join(str(v) for v in emb) + "]"
            await session.execute(
                sa.text("UPDATE document_chunks SET embedding = :emb WHERE id = :cid"),
                {"emb": emb_str, "cid": str(row[0])},
            )
            reindexed += 1

    await session.commit()

    return {
        "message": f"Reindexed {reindexed} chunks with embeddings",
        "reindexed": reindexed,
        "remaining": len(rows) - reindexed,
        "model": embedding_service.get_model_name(),
    }


@router.get("/search/status")
async def search_status():
    """Check which search modes are available."""
    from app.modules.knowledge import embedding_service
    return {
        "tfidf": True,
        "vector": embedding_service.is_available(),
        "hybrid": embedding_service.is_available(),
        "embedding_model": embedding_service.get_model_name() if embedding_service.is_available() else None,
        "embedding_dimensions": 384 if embedding_service.is_available() else None,
    }
