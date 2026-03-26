"""
AI Memory Service - Mem0-style persistent memory for personalized AI.

Stores user preferences, facts, and context that get injected
into all AI prompts across the platform.

Supports Mem0 for enhanced semantic recall (auto-detection + fallback to DB queries).
"""

import json
import os
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlalchemy import update
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.ai_memory import MemoryType, UserMemory

try:
    from mem0 import Memory
    HAS_MEM0 = True
except ImportError:
    HAS_MEM0 = False

logger = structlog.get_logger()

# Lazy singleton for Mem0 client
_mem0_client = None


def _get_mem0_client():
    """Create or return the Mem0 Memory client (lazy singleton).

    Configuration is read from environment variables:
    - MEM0_VECTOR_STORE: vector store provider (default: "qdrant")
    - MEM0_VECTOR_URL: vector store URL
    - MEM0_EMBEDDING_MODEL: embedding model name
    - MEM0_LLM_PROVIDER: LLM provider for extraction (default: "openai")
    - MEM0_LLM_MODEL: LLM model for extraction
    """
    global _mem0_client
    if _mem0_client is not None:
        return _mem0_client

    if not HAS_MEM0:
        return None

    try:
        config = {}

        # Vector store config
        vector_store = os.getenv("MEM0_VECTOR_STORE")
        if vector_store:
            vector_config = {"provider": vector_store}
            vector_url = os.getenv("MEM0_VECTOR_URL")
            if vector_url:
                vector_config["config"] = {vector_store: {"url": vector_url}}
            config["vector_store"] = vector_config

        # Embedding model config
        embedding_model = os.getenv("MEM0_EMBEDDING_MODEL")
        if embedding_model:
            config["embedder"] = {
                "provider": "openai",
                "config": {"model": embedding_model},
            }

        # LLM config for memory extraction
        llm_provider = os.getenv("MEM0_LLM_PROVIDER")
        llm_model = os.getenv("MEM0_LLM_MODEL")
        if llm_provider or llm_model:
            llm_cfg = {}
            if llm_provider:
                llm_cfg["provider"] = llm_provider
            if llm_model:
                llm_cfg["config"] = {"model": llm_model}
            config["llm"] = llm_cfg

        _mem0_client = Memory.from_config(config) if config else Memory()
        logger.info("mem0_client_initialized", config_keys=list(config.keys()))
        return _mem0_client
    except Exception as e:
        logger.warning("mem0_client_init_failed", error=str(e))
        return None


class AIMemoryService:
    """Service for persistent AI memory."""

    @staticmethod
    async def add_memory(
        user_id: UUID, content: str, memory_type: str,
        category: Optional[str], source: str,
        session: AsyncSession,
    ) -> UserMemory:
        """Add a memory entry (dual-write: DB + Mem0 if available)."""
        mem = UserMemory(
            user_id=user_id,
            content=content[:2000],
            memory_type=MemoryType(memory_type) if memory_type in [m.value for m in MemoryType] else MemoryType.FACT,
            category=category,
            source=source,
        )
        session.add(mem)
        await session.commit()
        await session.refresh(mem)

        # Dual-write to Mem0 for enhanced semantic recall
        if HAS_MEM0:
            try:
                client = _get_mem0_client()
                if client:
                    metadata = {
                        "memory_type": memory_type,
                        "source": source,
                        "db_id": str(mem.id),
                    }
                    if category:
                        metadata["category"] = category
                    client.add(
                        content,
                        user_id=str(user_id),
                        metadata=metadata,
                    )
                    logger.debug("mem0_memory_stored", memory_id=str(mem.id))
            except Exception as e:
                logger.debug("mem0_store_failed", error=str(e), memory_id=str(mem.id))

        return mem

    @staticmethod
    async def list_memories(
        user_id: UUID, session: AsyncSession,
        memory_type: Optional[str] = None, active_only: bool = True,
    ) -> list[UserMemory]:
        """List user memories."""
        query = select(UserMemory).where(UserMemory.user_id == user_id)
        if memory_type:
            query = query.where(UserMemory.memory_type == memory_type)
        if active_only:
            query = query.where(UserMemory.active == True)
        query = query.order_by(UserMemory.updated_at.desc())
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def recall_memories(
        user_id: UUID, query: str, session: AsyncSession,
        limit: int = 10,
    ) -> list[dict]:
        """Recall memories relevant to a query.

        Uses Mem0 semantic search if available for better relevance,
        falls back to DB listing (most recent + most used).
        Returns a list of dicts with 'content', 'memory_type', 'score', 'source'.
        """
        # Try Mem0 semantic search first
        if HAS_MEM0:
            mem0_results = AIMemoryService._search_mem0(str(user_id), query, limit)
            if mem0_results:
                logger.debug(
                    "recall_via_mem0", user_id=str(user_id),
                    query=query[:50], count=len(mem0_results),
                )
                return mem0_results

        # Fallback: DB query (most used + most recent)
        logger.debug("recall_via_db_fallback", user_id=str(user_id), query=query[:50])
        memories = await AIMemoryService.list_memories(user_id, session)
        results = []
        for mem in memories[:limit]:
            results.append({
                "content": mem.content,
                "memory_type": mem.memory_type.value if hasattr(mem.memory_type, 'value') else mem.memory_type,
                "score": None,
                "source": "db",
                "id": str(mem.id),
                "category": mem.category,
            })
        return results

    @staticmethod
    def _search_mem0(user_id: str, query: str, limit: int = 10) -> list[dict]:
        """Search Mem0 for semantically relevant memories.

        Returns a list of dicts with content, metadata, and relevance score.
        Returns empty list on failure (caller falls back to DB).
        """
        try:
            client = _get_mem0_client()
            if not client:
                return []

            results = client.search(query, user_id=user_id, limit=limit)

            memories = []
            # Mem0 returns a list of dicts (or object with 'results' key)
            items = results if isinstance(results, list) else results.get("results", [])
            for item in items:
                memory_data = {
                    "content": item.get("memory", item.get("text", "")),
                    "score": item.get("score"),
                    "source": "mem0",
                    "id": item.get("id", ""),
                }
                metadata = item.get("metadata", {})
                if metadata:
                    memory_data["memory_type"] = metadata.get("memory_type", "fact")
                    memory_data["category"] = metadata.get("category")
                    memory_data["db_id"] = metadata.get("db_id")
                else:
                    memory_data["memory_type"] = "fact"
                    memory_data["category"] = None
                memories.append(memory_data)

            return memories
        except Exception as e:
            logger.debug("mem0_search_failed", error=str(e), user_id=user_id)
            return []

    @staticmethod
    async def sync_to_mem0(user_id: UUID, session: AsyncSession) -> dict:
        """Bulk-sync existing DB memories to Mem0.

        Useful for bootstrapping Mem0 with existing data or re-syncing after
        Mem0 storage is reset. DB remains the source of truth.

        Returns: {"synced": int, "failed": int, "skipped": int}
        """
        if not HAS_MEM0:
            return {"synced": 0, "failed": 0, "skipped": 0, "error": "mem0 not installed"}

        client = _get_mem0_client()
        if not client:
            return {"synced": 0, "failed": 0, "skipped": 0, "error": "mem0 client unavailable"}

        memories = await AIMemoryService.list_memories(user_id, session, active_only=True)
        synced = 0
        failed = 0

        for mem in memories:
            try:
                metadata = {
                    "memory_type": mem.memory_type.value if hasattr(mem.memory_type, 'value') else mem.memory_type,
                    "source": mem.source,
                    "db_id": str(mem.id),
                }
                if mem.category:
                    metadata["category"] = mem.category
                client.add(
                    mem.content,
                    user_id=str(user_id),
                    metadata=metadata,
                )
                synced += 1
            except Exception as e:
                logger.debug("mem0_sync_item_failed", error=str(e), memory_id=str(mem.id))
                failed += 1

        logger.info(
            "mem0_bulk_sync_complete",
            user_id=str(user_id), synced=synced, failed=failed, total=len(memories),
        )
        return {"synced": synced, "failed": failed, "skipped": 0}

    @staticmethod
    async def delete_memory(
        memory_id: UUID, user_id: UUID, session: AsyncSession,
    ) -> bool:
        """Delete (deactivate) a memory."""
        mem = await session.get(UserMemory, memory_id)
        if not mem or mem.user_id != user_id:
            return False
        mem.active = False
        mem.updated_at = datetime.now(UTC)
        session.add(mem)
        await session.commit()
        return True

    @staticmethod
    async def get_context_injection(
        user_id: UUID, session: AsyncSession, max_memories: int = 10,
    ) -> str:
        """Build a context string from user memories for prompt injection.

        This is the key method: called before every AI prompt to personalize responses.
        """
        memories = await AIMemoryService.list_memories(user_id, session)
        if not memories:
            return ""

        # Select most relevant memories (most used + most recent)
        sorted_mems = sorted(
            memories,
            key=lambda m: (m.use_count, m.updated_at.timestamp() if m.updated_at else 0),
            reverse=True,
        )[:max_memories]

        parts = []
        for mem in sorted_mems:
            prefix = {
                "preference": "User prefers",
                "fact": "Known fact",
                "context": "Current context",
                "instruction": "User instruction",
            }.get(mem.memory_type.value if hasattr(mem.memory_type, 'value') else mem.memory_type, "Note")
            parts.append(f"- {prefix}: {mem.content}")

        # Update usage stats in bulk
        await session.execute(
            update(UserMemory)
            .where(UserMemory.id.in_([m.id for m in sorted_mems]))
            .values(use_count=UserMemory.use_count + 1, last_used_at=datetime.now(UTC))
        )
        await session.commit()

        return "User profile & context:\n" + "\n".join(parts)

    @staticmethod
    async def auto_extract_memories(
        user_id: UUID, text: str, source: str, session: AsyncSession,
    ) -> list[UserMemory]:
        """Auto-extract memories from text using AI (Mem0-style)."""
        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"""Extract user preferences, facts, and instructions from this text.
Only extract clear, actionable items that would help personalize future AI interactions.

Text: {text[:3000]}

Respond with a JSON array: [{{"content": "...", "type": "preference|fact|context|instruction", "category": "...", "confidence": 0.9}}]
If nothing useful, respond with: []""",
                task="memory_extraction",
                provider_name="gemini",
                user_id=user_id,
                module="ai_memory",
            )

            response = result.get("processed_text", "[]")
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                items = json.loads(response[start:end])
                created = []
                for item in items[:5]:
                    if isinstance(item, dict) and item.get("content"):
                        mem = await AIMemoryService.add_memory(
                            user_id=user_id,
                            content=item["content"],
                            memory_type=item.get("type", "fact"),
                            category=item.get("category"),
                            source=source,
                            session=session,
                        )
                        created.append(mem)
                return created
        except Exception as e:
            logger.debug("auto_memory_extraction_failed", error=str(e))
        return []

    @staticmethod
    async def forget_all(user_id: UUID, session: AsyncSession) -> int:
        """RGPD: deactivate all memories for a user."""
        result = await session.execute(
            select(UserMemory).where(UserMemory.user_id == user_id, UserMemory.active == True)
        )
        count = 0
        for mem in result.scalars().all():
            mem.active = False
            session.add(mem)
            count += 1
        await session.commit()
        logger.info("memories_forgotten", user_id=str(user_id), count=count)
        return count
