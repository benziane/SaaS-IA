"""
AI Chatbot Builder service - Create, configure, and deploy custom chatbots with RAG.
"""

import json
import secrets
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.ai_chatbot_builder import Chatbot, ChatbotConversation

logger = structlog.get_logger()


class ChatbotBuilderService:
    """Service for chatbot builder operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chatbot(self, user_id: UUID, data: dict) -> Chatbot:
        """Create a new chatbot with system prompt and config."""
        kb_ids = data.get("knowledge_base_ids")
        chatbot = Chatbot(
            user_id=user_id,
            name=data["name"],
            description=data.get("description"),
            system_prompt=data["system_prompt"],
            model=data.get("model", "gemini"),
            knowledge_base_ids=json.dumps([str(uid) for uid in kb_ids]) if kb_ids else None,
            personality=data.get("personality", "professional"),
            welcome_message=data.get("welcome_message"),
            theme=json.dumps(data.get("theme")) if data.get("theme") else None,
            is_published=False,
            channels=json.dumps([]),
            conversations_count=0,
        )
        self.session.add(chatbot)
        await self.session.commit()
        await self.session.refresh(chatbot)

        logger.info("chatbot_created", chatbot_id=str(chatbot.id), name=chatbot.name)
        return chatbot

    async def list_chatbots(self, user_id: UUID) -> list[Chatbot]:
        """List all chatbots for a user."""
        result = await self.session.execute(
            select(Chatbot)
            .where(Chatbot.user_id == user_id, Chatbot.is_deleted == False)
            .order_by(Chatbot.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_chatbot(self, user_id: UUID, chatbot_id: UUID) -> Optional[Chatbot]:
        """Get chatbot details, verifying ownership."""
        chatbot = await self.session.get(Chatbot, chatbot_id)
        if not chatbot or chatbot.user_id != user_id or chatbot.is_deleted:
            return None
        return chatbot

    async def update_chatbot(self, user_id: UUID, chatbot_id: UUID, data: dict) -> Optional[Chatbot]:
        """Update chatbot settings."""
        chatbot = await self.get_chatbot(user_id, chatbot_id)
        if not chatbot:
            return None

        for field in ["name", "description", "system_prompt", "model", "personality", "welcome_message"]:
            if field in data and data[field] is not None:
                setattr(chatbot, field, data[field])

        if "theme" in data and data["theme"] is not None:
            chatbot.theme = json.dumps(data["theme"])

        chatbot.updated_at = datetime.utcnow()
        self.session.add(chatbot)
        await self.session.commit()
        await self.session.refresh(chatbot)

        logger.info("chatbot_updated", chatbot_id=str(chatbot_id))
        return chatbot

    async def delete_chatbot(self, user_id: UUID, chatbot_id: UUID) -> bool:
        """Soft delete a chatbot."""
        chatbot = await self.get_chatbot(user_id, chatbot_id)
        if not chatbot:
            return False

        chatbot.is_deleted = True
        chatbot.is_published = False
        chatbot.embed_token = None
        chatbot.updated_at = datetime.utcnow()
        self.session.add(chatbot)
        await self.session.commit()

        logger.info("chatbot_deleted", chatbot_id=str(chatbot_id))
        return True

    async def publish_chatbot(self, user_id: UUID, chatbot_id: UUID) -> Optional[Chatbot]:
        """Generate embed_token and mark chatbot as published."""
        chatbot = await self.get_chatbot(user_id, chatbot_id)
        if not chatbot:
            return None

        if not chatbot.embed_token:
            chatbot.embed_token = secrets.token_urlsafe(32)

        chatbot.is_published = True
        chatbot.updated_at = datetime.utcnow()
        self.session.add(chatbot)
        await self.session.commit()
        await self.session.refresh(chatbot)

        logger.info("chatbot_published", chatbot_id=str(chatbot_id), embed_token=chatbot.embed_token)
        return chatbot

    async def unpublish_chatbot(self, user_id: UUID, chatbot_id: UUID) -> Optional[Chatbot]:
        """Revoke embed_token and unpublish chatbot."""
        chatbot = await self.get_chatbot(user_id, chatbot_id)
        if not chatbot:
            return None

        chatbot.is_published = False
        chatbot.embed_token = None
        chatbot.updated_at = datetime.utcnow()
        self.session.add(chatbot)
        await self.session.commit()
        await self.session.refresh(chatbot)

        logger.info("chatbot_unpublished", chatbot_id=str(chatbot_id))
        return chatbot

    async def _get_chatbot_by_token(self, embed_token: str) -> Optional[Chatbot]:
        """Retrieve a published chatbot by its embed token."""
        result = await self.session.execute(
            select(Chatbot).where(
                Chatbot.embed_token == embed_token,
                Chatbot.is_published == True,
                Chatbot.is_deleted == False,
            )
        )
        return result.scalars().first()

    async def _build_rag_context(self, knowledge_base_ids: list[str], message: str) -> tuple[str, list[dict]]:
        """Query knowledge module for RAG context from linked knowledge bases."""
        context_parts = []
        sources = []

        try:
            from app.modules.knowledge.service import KnowledgeService

            for kb_user_id in knowledge_base_ids:
                try:
                    results = await KnowledgeService.search(
                        user_id=UUID(kb_user_id),
                        query=message,
                        session=self.session,
                        limit=3,
                    )
                    for r in results:
                        context_parts.append(f"[{r['filename']}]: {r['content']}")
                        sources.append({
                            "filename": r["filename"],
                            "content": r["content"][:200],
                            "score": r["score"],
                        })
                except Exception as e:
                    logger.debug("rag_kb_search_failed", kb_id=kb_user_id, error=str(e))
        except ImportError:
            logger.debug("knowledge_module_not_available")

        context = "\n\n".join(context_parts) if context_parts else ""
        return context, sources

    async def chat(
        self,
        chatbot_id: UUID,
        embed_token: str,
        message: str,
        session_id: Optional[str] = None,
    ) -> dict:
        """Public chat endpoint - validates embed_token, no auth required.

        Uses AIAssistantService for LLM calls with the chatbot's system_prompt.
        If knowledge_base_ids are set, queries knowledge module for RAG context.
        """
        chatbot = await self._get_chatbot_by_token(embed_token)
        if not chatbot:
            return {"error": "Invalid or inactive chatbot"}

        # Generate session_id if not provided
        if not session_id:
            session_id = secrets.token_urlsafe(16)

        # Load or create conversation
        result = await self.session.execute(
            select(ChatbotConversation).where(
                ChatbotConversation.chatbot_id == chatbot_id,
                ChatbotConversation.session_id == session_id,
            )
        )
        conversation = result.scalars().first()

        if not conversation:
            conversation = ChatbotConversation(
                chatbot_id=chatbot_id,
                session_id=session_id,
                messages=json.dumps([]),
            )
            self.session.add(conversation)
            await self.session.flush()

        # Parse existing messages
        messages = json.loads(conversation.messages) if conversation.messages else []

        # Build RAG context if knowledge bases are linked
        rag_context = ""
        sources = []
        if chatbot.knowledge_base_ids:
            kb_ids = json.loads(chatbot.knowledge_base_ids)
            if kb_ids:
                rag_context, sources = await self._build_rag_context(kb_ids, message)

        # Build the full prompt
        system_parts = [chatbot.system_prompt]
        if chatbot.personality and chatbot.personality != "professional":
            system_parts.append(f"Personality: {chatbot.personality}")
        if rag_context:
            system_parts.append(
                f"Use the following knowledge base context to help answer:\n{rag_context}"
            )

        system_prompt = "\n\n".join(system_parts)

        # Build conversation history for context (last 10 messages)
        history_text = ""
        recent_messages = messages[-10:]
        if recent_messages:
            history_parts = [f"{m['role']}: {m['content']}" for m in recent_messages]
            history_text = "\n".join(history_parts)

        full_prompt = f"{system_prompt}\n\n"
        if history_text:
            full_prompt += f"Conversation history:\n{history_text}\n\n"
        full_prompt += f"User: {message}\n\nAssistant:"

        # Call LLM
        assistant_response = ""
        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=full_prompt,
                task="chatbot_response",
                provider_name=chatbot.model or "gemini",
                user_id=chatbot.user_id,
                module="ai_chatbot_builder",
            )
            assistant_response = result.get("processed_text", "I'm sorry, I couldn't process your request.")
        except Exception as e:
            logger.error("chatbot_llm_call_failed", error=str(e), chatbot_id=str(chatbot_id))
            assistant_response = "I'm experiencing technical difficulties. Please try again later."

        # Store messages
        now = datetime.utcnow().isoformat()
        user_msg = {
            "id": str(uuid4()),
            "role": "user",
            "content": message,
            "created_at": now,
        }
        assistant_msg = {
            "id": str(uuid4()),
            "role": "assistant",
            "content": assistant_response,
            "sources": sources if sources else None,
            "created_at": now,
        }
        messages.append(user_msg)
        messages.append(assistant_msg)

        conversation.messages = json.dumps(messages)
        conversation.updated_at = datetime.utcnow()
        self.session.add(conversation)

        # Update conversation count
        chatbot.conversations_count = await self._count_conversations(chatbot_id)
        self.session.add(chatbot)
        await self.session.commit()

        return {
            "session_id": session_id,
            "message": assistant_msg,
            "sources": sources,
        }

    async def _count_conversations(self, chatbot_id: UUID) -> int:
        """Count unique conversations for a chatbot."""
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count(ChatbotConversation.id)).where(
                ChatbotConversation.chatbot_id == chatbot_id
            )
        )
        return result.scalar() or 0

    async def get_chat_history(self, chatbot_id: UUID, session_id: str) -> list[dict]:
        """Return conversation history for a session."""
        result = await self.session.execute(
            select(ChatbotConversation).where(
                ChatbotConversation.chatbot_id == chatbot_id,
                ChatbotConversation.session_id == session_id,
            )
        )
        conversation = result.scalars().first()
        if not conversation:
            return []

        messages = json.loads(conversation.messages) if conversation.messages else []
        return messages

    async def add_channel(self, user_id: UUID, chatbot_id: UUID, channel_config: dict) -> Optional[Chatbot]:
        """Add a deployment channel to a chatbot."""
        chatbot = await self.get_chatbot(user_id, chatbot_id)
        if not chatbot:
            return None

        channels = json.loads(chatbot.channels) if chatbot.channels else []

        # Remove existing channel of same type
        channels = [c for c in channels if c.get("type") != channel_config["type"]]
        channels.append(channel_config)

        chatbot.channels = json.dumps(channels)
        chatbot.updated_at = datetime.utcnow()
        self.session.add(chatbot)
        await self.session.commit()
        await self.session.refresh(chatbot)

        logger.info("channel_added", chatbot_id=str(chatbot_id), channel_type=channel_config["type"])
        return chatbot

    async def remove_channel(self, user_id: UUID, chatbot_id: UUID, channel_type: str) -> Optional[Chatbot]:
        """Remove a deployment channel from a chatbot."""
        chatbot = await self.get_chatbot(user_id, chatbot_id)
        if not chatbot:
            return None

        channels = json.loads(chatbot.channels) if chatbot.channels else []
        channels = [c for c in channels if c.get("type") != channel_type]

        chatbot.channels = json.dumps(channels)
        chatbot.updated_at = datetime.utcnow()
        self.session.add(chatbot)
        await self.session.commit()
        await self.session.refresh(chatbot)

        logger.info("channel_removed", chatbot_id=str(chatbot_id), channel_type=channel_type)
        return chatbot

    async def get_analytics(self, user_id: UUID, chatbot_id: UUID) -> Optional[dict]:
        """Return conversation analytics for a chatbot."""
        chatbot = await self.get_chatbot(user_id, chatbot_id)
        if not chatbot:
            return None

        # Gather conversation stats
        result = await self.session.execute(
            select(ChatbotConversation).where(
                ChatbotConversation.chatbot_id == chatbot_id
            )
        )
        conversations = list(result.scalars().all())

        total_conversations = len(conversations)
        total_messages = 0
        satisfaction_scores = []
        question_counts: dict[str, int] = {}

        for conv in conversations:
            messages = json.loads(conv.messages) if conv.messages else []
            total_messages += len(messages)
            if conv.satisfaction_score is not None:
                satisfaction_scores.append(conv.satisfaction_score)

            # Extract user questions for top_questions
            for msg in messages:
                if msg.get("role") == "user":
                    q = msg.get("content", "")[:100]
                    question_counts[q] = question_counts.get(q, 0) + 1

        avg_messages = total_messages / total_conversations if total_conversations > 0 else 0.0
        avg_satisfaction = (
            sum(satisfaction_scores) / len(satisfaction_scores)
            if satisfaction_scores
            else None
        )

        top_questions = sorted(question_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_questions_list = [{"question": q, "count": c} for q, c in top_questions]

        return {
            "chatbot_id": str(chatbot_id),
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "avg_messages_per_conversation": round(avg_messages, 2),
            "satisfaction_score": round(avg_satisfaction, 2) if avg_satisfaction is not None else None,
            "top_questions": top_questions_list,
        }

    async def get_embed_code(self, user_id: UUID, chatbot_id: UUID) -> Optional[dict]:
        """Return HTML/JS embed snippet for website integration."""
        chatbot = await self.get_chatbot(user_id, chatbot_id)
        if not chatbot:
            return None

        if not chatbot.is_published or not chatbot.embed_token:
            return None

        token = chatbot.embed_token
        script_url = f"/api/chatbots/widget/{token}/loader.js"

        html_snippet = (
            f'<!-- {chatbot.name} Chatbot Widget -->\n'
            f'<script src="{script_url}" async></script>\n'
            f'<div id="saas-chatbot-widget" data-token="{token}"></div>'
        )

        return {
            "embed_token": token,
            "html_snippet": html_snippet,
            "script_url": script_url,
        }
