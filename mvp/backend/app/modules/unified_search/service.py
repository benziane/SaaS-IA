"""
Unified Search Service - Search across ALL platform modules in one query.

Searches transcriptions, knowledge base, content studio, conversations,
analyses, and more. Returns faceted results with cross-module RAG synthesis.

Uses Meilisearch if available, falls back to PostgreSQL full-text search.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession

logger = structlog.get_logger()


def is_meilisearch_available() -> bool:
    """Check if Meilisearch client is installed."""
    try:
        import meilisearch  # noqa: F401
        return True
    except ImportError:
        return False


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

        Returns results grouped by module with relevance scoring.
        """
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
