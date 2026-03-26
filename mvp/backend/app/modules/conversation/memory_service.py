"""
Conversation Memory Service - Long-term memory for chat sessions.

Inspired by Zep (3K+ stars) - provides hierarchical memory:
1. Short-term: sliding window of recent messages
2. Summary: periodic AI-generated summaries of older messages
3. Long-term: vector search over all conversation history (via knowledge base)

Falls back to simple message history if no memory backend is configured.
The existing ConversationService message handling is PRESERVED.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

import structlog

logger = structlog.get_logger()


class ConversationMemory:
    """Hierarchical memory manager for a conversation."""

    def __init__(
        self,
        conversation_id: UUID,
        user_id: UUID,
        window_size: int = 20,
    ):
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.window_size = window_size
        self.summaries: list[str] = []

    async def build_context(
        self,
        messages: list[dict],
        current_query: str,
    ) -> str:
        """Build optimized context from conversation history.

        Strategy:
        1. Keep last N messages verbatim (short-term window)
        2. Summarize older messages (if > window_size)
        3. Optionally search knowledge base for relevant context (RAG)
        """
        parts = []

        # Summary of older messages (if conversation is long)
        if len(messages) > self.window_size:
            older = messages[:-self.window_size]
            summary = await self._summarize_messages(older)
            if summary:
                parts.append(f"[Conversation summary]: {summary}")
                self.summaries.append(summary)

        # Recent messages (verbatim)
        recent = messages[-self.window_size:]
        if recent:
            history = "\n".join(
                f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('content', '')[:500]}"
                for m in recent
            )
            parts.append(f"[Recent conversation]:\n{history}")

        # Knowledge base context (RAG on conversation topic)
        kb_context = await self._search_relevant_knowledge(current_query)
        if kb_context:
            parts.append(f"[Relevant knowledge]: {kb_context}")

        return "\n\n".join(parts)

    async def _summarize_messages(self, messages: list[dict]) -> Optional[str]:
        """AI-summarize a batch of older messages."""
        if not messages:
            return None

        text = "\n".join(
            f"{'User' if m.get('role') == 'user' else 'AI'}: {m.get('content', '')[:300]}"
            for m in messages[:50]  # Limit to avoid huge prompts
        )

        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"Summarize this conversation concisely, preserving key facts and decisions:\n\n{text[:5000]}",
                task="summarize",
                provider_name="gemini",
                user_id=self.user_id,
                module="conversation_memory",
            )
            summary = result.get("processed_text", "")
            logger.info("conversation_summarized", messages=len(messages), summary_length=len(summary))
            return summary[:1000]
        except Exception as e:
            logger.debug("conversation_summary_failed", error=str(e))
            return None

    async def _search_relevant_knowledge(self, query: str) -> Optional[str]:
        """Search knowledge base for context relevant to the current query."""
        try:
            from app.modules.knowledge.service import KnowledgeService
            from app.database import get_session_context

            async with get_session_context() as session:
                results = await KnowledgeService.search(
                    user_id=self.user_id,
                    query=query[:200],
                    session=session,
                    limit=2,
                )

            if results:
                return "\n".join(
                    f"[{r.get('filename', '')}] {r.get('content', '')[:300]}"
                    for r in results
                )
        except Exception as e:
            logger.warning("knowledge_search_failed", conversation_id=str(self.conversation_id), error=str(e))
        return None

    async def extract_facts(self, messages: list[dict]) -> list[dict]:
        """Extract key facts and preferences from conversation (Zep-style).

        Returns a list of {fact, category, confidence}.
        """
        if not messages:
            return []

        recent_text = "\n".join(
            f"{'User' if m.get('role') == 'user' else 'AI'}: {m.get('content', '')[:200]}"
            for m in messages[-20:]
        )

        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=f"""Extract key facts, preferences, and decisions from this conversation.

Conversation:
{recent_text[:4000]}

Respond with a JSON array: [{{"fact": "...", "category": "preference|decision|information|context", "confidence": 0.9}}]
Only extract clear, useful facts. Respond ONLY with the JSON array.""",
                task="fact_extraction",
                provider_name="gemini",
                user_id=self.user_id,
                module="conversation_memory",
            )

            text = result.get("processed_text", "[]")
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                facts = json.loads(text[start:end])
                logger.info("facts_extracted", count=len(facts))
                return [f for f in facts if isinstance(f, dict)]
        except Exception as e:
            logger.debug("fact_extraction_failed", error=str(e))

        return []


def is_zep_available() -> bool:
    """Check if Zep client is installed for advanced memory."""
    try:
        from zep_python import ZepClient  # noqa: F401
        return True
    except ImportError:
        return False
