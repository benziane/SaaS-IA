"""
AI Memory Service - Mem0-style persistent memory for personalized AI.

Stores user preferences, facts, and context that get injected
into all AI prompts across the platform.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.ai_memory import MemoryType, UserMemory

logger = structlog.get_logger()


class AIMemoryService:
    """Service for persistent AI memory."""

    @staticmethod
    async def add_memory(
        user_id: UUID, content: str, memory_type: str,
        category: Optional[str], source: str,
        session: AsyncSession,
    ) -> UserMemory:
        """Add a memory entry."""
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
    async def delete_memory(
        memory_id: UUID, user_id: UUID, session: AsyncSession,
    ) -> bool:
        """Delete (deactivate) a memory."""
        mem = await session.get(UserMemory, memory_id)
        if not mem or mem.user_id != user_id:
            return False
        mem.active = False
        mem.updated_at = datetime.utcnow()
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

        # Update usage stats
        for mem in sorted_mems:
            mem.use_count += 1
            mem.last_used_at = datetime.utcnow()
            session.add(mem)
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
