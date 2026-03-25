"""
Unified Search Service - Search across ALL platform modules in one query.

Searches transcriptions, knowledge base, content studio, conversations,
analyses, and more. Returns faceted results with cross-module RAG synthesis.

Uses Meilisearch if available, falls back to PostgreSQL full-text search.
"""

import json
import os
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog

try:
    import meilisearch
    HAS_MEILISEARCH = True
except ImportError:
    HAS_MEILISEARCH = False

from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Meilisearch lazy singleton
# ---------------------------------------------------------------------------
_meilisearch_client = None


def _get_meilisearch_client():
    """Return a Meilisearch client, creating it on first call.

    Reads MEILISEARCH_URL and MEILISEARCH_API_KEY from environment.
    Returns None if the library is not installed or the connection fails.
    """
    global _meilisearch_client
    if _meilisearch_client is not None:
        return _meilisearch_client

    if not HAS_MEILISEARCH:
        return None

    url = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
    api_key = os.getenv("MEILISEARCH_API_KEY", "")

    try:
        client = meilisearch.Client(url, api_key) if api_key else meilisearch.Client(url)
        # Verify connectivity
        client.health()
        _meilisearch_client = client
        logger.info("meilisearch_connected", url=url)
        return _meilisearch_client
    except Exception as e:
        logger.warning("meilisearch_connection_failed", url=url, error=str(e))
        return None


def is_meilisearch_available() -> bool:
    """Check if Meilisearch client is installed and reachable."""
    return _get_meilisearch_client() is not None


class UnifiedSearchService:
    """Service for cross-module universal search."""

    @staticmethod
    async def search(
        user_id: UUID,
        query: str,
        session: AsyncSession,
        modules: Optional[list[str]] = None,
        limit: int = 20,
    ) -> dict:
        """Search across all modules.

        Tries Meilisearch first if available for fast, typo-tolerant search.
        Falls back to PostgreSQL ILIKE-based search when Meilisearch is
        unavailable or returns an error.

        Returns results grouped by module with relevance scoring.
        """
        # --- Meilisearch path (fast, typo-tolerant) ---
        if HAS_MEILISEARCH and _get_meilisearch_client() is not None:
            try:
                ms_result = await UnifiedSearchService._search_meilisearch(
                    query, modules, limit, user_id,
                )
                if ms_result["total"] > 0:
                    logger.debug(
                        "search_via_meilisearch",
                        query=query,
                        total=ms_result["total"],
                    )
                    return ms_result
                # Meilisearch returned 0 results - fall through to DB search
                # which may still find ILIKE matches for content not yet indexed.
            except Exception as e:
                logger.warning("meilisearch_search_failed_fallback_to_db", error=str(e))

        # --- PostgreSQL fallback (always available) ---
        return await UnifiedSearchService._search_postgres(
            user_id, query, session, modules, limit,
        )

    @staticmethod
    async def _search_postgres(
        user_id: UUID,
        query: str,
        session: AsyncSession,
        modules: Optional[list[str]] = None,
        limit: int = 20,
    ) -> dict:
        """PostgreSQL ILIKE-based search across modules (original implementation)."""
        results = []
        facets = {}

        # Search each module in parallel-ish (sequential for simplicity)
        search_fns = {
            "transcriptions": UnifiedSearchService._search_transcriptions,
            "knowledge": UnifiedSearchService._search_knowledge,
            "content": UnifiedSearchService._search_content,
            "conversations": UnifiedSearchService._search_conversations,
        }

        target_modules = modules or list(search_fns.keys())

        for module_name in target_modules:
            fn = search_fns.get(module_name)
            if fn:
                try:
                    module_results = await fn(user_id, query, session, limit=limit)
                    for r in module_results:
                        r["_module"] = module_name
                    results.extend(module_results)
                    facets[module_name] = len(module_results)
                except Exception as e:
                    logger.debug(f"search_{module_name}_failed", error=str(e))
                    facets[module_name] = 0

        # Sort all results by score descending
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return {
            "query": query,
            "total": len(results),
            "results": results[:limit],
            "facets": facets,
        }

    @staticmethod
    async def search_and_answer(
        user_id: UUID,
        query: str,
        session: AsyncSession,
    ) -> dict:
        """Cross-module RAG: search all modules, then synthesize an answer."""
        search_results = await UnifiedSearchService.search(user_id, query, session, limit=10)

        if not search_results["results"]:
            return {
                "query": query,
                "answer": "No relevant content found across your platform data.",
                "sources": [],
            }

        # Build context from top results
        context_parts = []
        for r in search_results["results"][:5]:
            source = f"[{r['_module']}] {r.get('title', r.get('filename', 'untitled'))}"
            content = r.get("content", r.get("text", ""))[:500]
            context_parts.append(f"{source}:\n{content}")

        context = "\n\n".join(context_parts)

        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"""Answer this question using the cross-platform search results below.
Cite which sources you used.

Question: {query}

Search results from platform:
{context}

Answer:""",
                task="cross_module_rag",
                provider_name="gemini",
                user_id=user_id,
                module="unified_search",
            )
            answer = result.get("processed_text", "")
        except Exception as e:
            answer = f"Search found {len(search_results['results'])} results but couldn't synthesize an answer: {str(e)[:200]}"

        return {
            "query": query,
            "answer": answer,
            "sources": search_results["results"][:5],
            "facets": search_results["facets"],
        }

    # ------------------------------------------------------------------
    # Meilisearch helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def index_document(
        module: str,
        doc_id: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Index a single document into Meilisearch.

        Each module gets its own Meilisearch index (e.g. ``us_transcriptions``,
        ``us_knowledge``).  Documents are identified by ``doc_id`` so calling
        this again with the same id updates the existing entry.

        Returns True on success, False when Meilisearch is unavailable.
        """
        client = _get_meilisearch_client()
        if client is None:
            return False

        index_name = f"us_{module}"
        meta = metadata or {}

        doc = {
            "id": doc_id,
            "module": module,
            "content": content[:50_000],  # Meilisearch default max ~100 KB
            "title": meta.get("title", ""),
            "type": meta.get("type", module),
            "url": meta.get("url", ""),
            "user_id": meta.get("user_id", ""),
            "created_at": meta.get("created_at", datetime.now(UTC).isoformat()),
        }
        # Preserve any extra metadata keys
        for k, v in meta.items():
            if k not in doc:
                doc[k] = v

        try:
            index = client.index(index_name)
            index.add_documents([doc], primary_key="id")
            logger.debug("meilisearch_indexed", module=module, doc_id=doc_id)
            return True
        except Exception as e:
            logger.warning("meilisearch_index_failed", module=module, doc_id=doc_id, error=str(e))
            return False

    @staticmethod
    async def _search_meilisearch(
        query: str,
        modules: Optional[list[str]],
        limit: int,
        user_id: Optional[UUID] = None,
    ) -> dict:
        """Search across module-specific Meilisearch indexes.

        Queries each target module's index and merges results by score.
        """
        client = _get_meilisearch_client()
        if client is None:
            return {"query": query, "total": 0, "results": [], "facets": {}}

        all_module_names = ["transcriptions", "knowledge", "content", "conversations"]
        target_modules = modules or all_module_names

        results = []
        facets = {}

        for module_name in target_modules:
            index_name = f"us_{module_name}"
            try:
                index = client.index(index_name)
                search_params = {"limit": limit}
                # Scope to user if provided
                if user_id:
                    search_params["filter"] = f'user_id = "{str(user_id)}"'
                ms_results = index.search(query, search_params)

                hits = ms_results.get("hits", [])
                for hit in hits:
                    # Meilisearch provides _rankingScore when showRankingScore is true,
                    # but it's not guaranteed.  Estimate from position otherwise.
                    estimated_score = hit.get("_rankingScore", 0.8)
                    results.append({
                        "id": hit.get("id", ""),
                        "type": hit.get("type", module_name),
                        "title": hit.get("title", ""),
                        "content": (hit.get("content", "") or "")[:300],
                        "score": estimated_score,
                        "url": hit.get("url", ""),
                        "_module": module_name,
                    })
                facets[module_name] = len(hits)
            except Exception as e:
                logger.debug("meilisearch_module_search_failed", module=module_name, error=str(e))
                facets[module_name] = 0

        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        return {
            "query": query,
            "total": len(results),
            "results": results[:limit],
            "facets": facets,
        }

    @staticmethod
    async def reindex_module(
        module_name: str,
        session: AsyncSession,
    ) -> dict:
        """Rebuild the Meilisearch index for a given module.

        Fetches all relevant rows from PostgreSQL and pushes them into a
        fresh Meilisearch index.  Returns stats about the operation.

        Falls back gracefully if Meilisearch is not available.
        """
        client = _get_meilisearch_client()
        if client is None:
            return {"status": "skipped", "reason": "meilisearch_unavailable"}

        index_name = f"us_{module_name}"

        # Delete existing index to start fresh
        try:
            client.delete_index(index_name)
        except Exception:
            pass  # Index may not exist yet

        # Create index with filterable attributes
        try:
            client.create_index(index_name, {"primaryKey": "id"})
            index = client.index(index_name)
            index.update_filterable_attributes(["user_id", "module", "type"])
            index.update_searchable_attributes(["title", "content"])
        except Exception as e:
            logger.warning("meilisearch_create_index_failed", index=index_name, error=str(e))
            return {"status": "error", "reason": str(e)}

        # Fetch documents from DB per module
        indexed = 0
        try:
            if module_name == "transcriptions":
                from app.models.transcription import Transcription, TranscriptionStatus
                result = await session.execute(
                    select(Transcription).where(
                        Transcription.status == TranscriptionStatus.COMPLETED,
                    )
                )
                docs = []
                for t in result.scalars().all():
                    docs.append({
                        "id": str(t.id),
                        "module": "transcriptions",
                        "type": "transcription",
                        "title": t.original_filename or (t.video_url or "")[:60],
                        "content": (t.text or "")[:50_000],
                        "user_id": str(t.user_id),
                        "url": f"/transcription?id={t.id}",
                        "created_at": t.created_at.isoformat() if t.created_at else "",
                    })
                if docs:
                    index.add_documents(docs, primary_key="id")
                indexed = len(docs)

            elif module_name == "content":
                from app.models.content_studio import GeneratedContent
                result = await session.execute(select(GeneratedContent))
                docs = []
                for c in result.scalars().all():
                    docs.append({
                        "id": str(c.id),
                        "module": "content",
                        "type": "content",
                        "title": c.title or c.format,
                        "content": (c.content or "")[:50_000],
                        "user_id": str(c.user_id),
                        "url": "/content-studio",
                        "format": c.format if hasattr(c, "format") else "",
                    })
                if docs:
                    index.add_documents(docs, primary_key="id")
                indexed = len(docs)

            elif module_name == "conversations":
                from app.models.conversation import Message, Conversation
                result = await session.execute(
                    select(Message, Conversation.user_id)
                    .join(Conversation, Message.conversation_id == Conversation.id)
                )
                docs = []
                for m, uid in result.all():
                    docs.append({
                        "id": str(m.id) if hasattr(m, "id") else "",
                        "module": "conversations",
                        "type": "conversation",
                        "title": "Chat message",
                        "content": (m.content if hasattr(m, "content") else "")[:50_000],
                        "user_id": str(uid),
                        "url": "/chat",
                    })
                if docs:
                    index.add_documents(docs, primary_key="id")
                indexed = len(docs)

            elif module_name == "knowledge":
                # Knowledge base chunks
                import sqlalchemy as sa
                result = await session.execute(
                    sa.text(
                        "SELECT dc.id, dc.content, dc.document_id, d.filename, d.user_id "
                        "FROM document_chunks dc "
                        "JOIN documents d ON dc.document_id = d.id"
                    )
                )
                docs = []
                for row in result.all():
                    docs.append({
                        "id": str(row[0]),
                        "module": "knowledge",
                        "type": "document",
                        "title": row[3] or "Document",
                        "content": (row[1] or "")[:50_000],
                        "user_id": str(row[4]),
                        "document_id": str(row[2]),
                        "url": "/knowledge",
                    })
                if docs:
                    index.add_documents(docs, primary_key="id")
                indexed = len(docs)

            else:
                return {"status": "error", "reason": f"unknown module: {module_name}"}

        except Exception as e:
            logger.error("meilisearch_reindex_failed", module=module_name, error=str(e))
            return {"status": "error", "reason": str(e)}

        logger.info("meilisearch_reindex_complete", module=module_name, indexed=indexed)
        return {"status": "ok", "module": module_name, "indexed": indexed}

    # ------------------------------------------------------------------
    # PostgreSQL per-module search helpers (original implementation)
    # ------------------------------------------------------------------

    @staticmethod
    async def _search_transcriptions(
        user_id: UUID, query: str, session: AsyncSession, limit: int = 10,
    ) -> list[dict]:
        """Search transcriptions by text content."""
        from app.models.transcription import Transcription, TranscriptionStatus
        import sqlalchemy as sa

        result = await session.execute(
            select(Transcription)
            .where(
                Transcription.user_id == user_id,
                Transcription.status == TranscriptionStatus.COMPLETED,
                sa.cast(Transcription.text, sa.Text).ilike(f"%{query[:100]}%"),
            )
            .order_by(Transcription.created_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": str(t.id), "type": "transcription",
                "title": t.original_filename or t.video_url[:60],
                "content": (t.text or "")[:300],
                "score": 0.7,
                "created_at": t.created_at.isoformat(),
                "url": f"/transcription?id={t.id}",
            }
            for t in result.scalars().all()
        ]

    @staticmethod
    async def _search_knowledge(
        user_id: UUID, query: str, session: AsyncSession, limit: int = 10,
    ) -> list[dict]:
        """Search knowledge base (uses hybrid search if available)."""
        try:
            from app.modules.knowledge.service import KnowledgeService
            results = await KnowledgeService.search(user_id, query, session, limit)
            return [
                {
                    "id": str(r["chunk_id"]), "type": "document",
                    "title": r.get("filename", "Document"),
                    "content": r.get("content", "")[:300],
                    "score": r.get("score", 0.5),
                    "document_id": str(r.get("document_id", "")),
                    "url": "/knowledge",
                }
                for r in results
            ]
        except Exception:
            return []

    @staticmethod
    async def _search_content(
        user_id: UUID, query: str, session: AsyncSession, limit: int = 10,
    ) -> list[dict]:
        """Search generated content from content studio."""
        from app.models.content_studio import GeneratedContent
        import sqlalchemy as sa

        result = await session.execute(
            select(GeneratedContent)
            .where(
                GeneratedContent.user_id == user_id,
                or_(
                    sa.cast(GeneratedContent.content, sa.Text).ilike(f"%{query[:100]}%"),
                    sa.cast(GeneratedContent.title, sa.Text).ilike(f"%{query[:100]}%"),
                ),
            )
            .order_by(GeneratedContent.created_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": str(c.id), "type": "content",
                "title": c.title or c.format,
                "content": c.content[:300],
                "format": c.format,
                "score": 0.6,
                "url": "/content-studio",
            }
            for c in result.scalars().all()
        ]

    @staticmethod
    async def _search_conversations(
        user_id: UUID, query: str, session: AsyncSession, limit: int = 10,
    ) -> list[dict]:
        """Search conversation messages."""
        from app.models.conversation import Message, Conversation
        import sqlalchemy as sa

        result = await session.execute(
            select(Message, Conversation.id.label("conv_id"))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Conversation.user_id == user_id,
                sa.cast(Message.content, sa.Text).ilike(f"%{query[:100]}%"),
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": str(m.id) if hasattr(m, 'id') else "", "type": "conversation",
                "title": f"Chat message",
                "content": (m.content if hasattr(m, 'content') else "")[:300],
                "score": 0.5,
                "url": "/chat",
            }
            for m, _ in result.all()
        ]
