"""
Realtime AI service - Live voice and vision AI sessions.

Manages real-time AI interaction sessions with streaming,
knowledge base RAG, and conversation history.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.realtime_ai import RealtimeSession, SessionMode, SessionStatus

try:
    from livekit import api as livekit_api
    HAS_LIVEKIT = True
except ImportError:
    HAS_LIVEKIT = False

logger = structlog.get_logger()

REALTIME_CONFIG = {
    "providers": [
        {"id": "gemini", "name": "Gemini 2.0 Flash", "supports": ["voice", "vision", "voice_vision"], "speed": "fast"},
        {"id": "groq", "name": "Groq Llama 3.3", "supports": ["voice"], "speed": "ultra-fast"},
        {"id": "claude", "name": "Claude Sonnet", "supports": ["voice", "vision"], "speed": "medium"},
    ],
    "modes": [
        {"id": "voice", "name": "Voice Chat", "description": "Real-time voice conversation with AI"},
        {"id": "vision", "name": "Vision Analysis", "description": "Share screen/camera for AI analysis"},
        {"id": "voice_vision", "name": "Voice + Vision", "description": "Voice conversation with visual context"},
        {"id": "meeting", "name": "Meeting Assistant", "description": "AI joins and assists in meetings"},
    ],
    "languages": [
        {"code": "auto", "name": "Auto-detect"},
        {"code": "en", "name": "English"},
        {"code": "fr", "name": "French"},
        {"code": "es", "name": "Spanish"},
        {"code": "de", "name": "German"},
        {"code": "ja", "name": "Japanese"},
        {"code": "zh", "name": "Chinese"},
    ],
    "livekit_available": HAS_LIVEKIT,
    "webrtc_enabled": HAS_LIVEKIT,
}


class RealtimeAIService:
    """Service for real-time AI interaction sessions."""

    @staticmethod
    def _create_livekit_room(session_id: str, user_id: str) -> Optional[dict]:
        """Create a LiveKit room and generate an access token for the user."""
        if not HAS_LIVEKIT:
            return None

        try:
            livekit_url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
            api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
            api_secret = os.getenv("LIVEKIT_API_SECRET", "devsecret")

            token = livekit_api.AccessToken(api_key, api_secret)
            token.identity = str(user_id)
            token.add_grant(livekit_api.VideoGrant(
                room_join=True,
                room=session_id,
                can_publish=True,
                can_subscribe=True,
            ))

            expires_at = datetime.utcnow() + timedelta(hours=6)
            jwt_token = token.to_jwt()

            return {
                "room_name": session_id,
                "token": jwt_token,
                "livekit_url": livekit_url,
                "expires_at": expires_at.isoformat(),
            }
        except Exception as e:
            logger.error("livekit_room_creation_failed", error=str(e))
            return None

    @staticmethod
    def _create_livekit_agent_token(session_id: str) -> Optional[dict]:
        """Create a LiveKit access token for the AI agent to join a room."""
        if not HAS_LIVEKIT:
            return None

        try:
            api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
            api_secret = os.getenv("LIVEKIT_API_SECRET", "devsecret")

            token = livekit_api.AccessToken(api_key, api_secret)
            token.identity = "ai-agent"
            token.add_grant(livekit_api.VideoGrant(
                room_join=True,
                room=session_id,
                can_publish=True,
                can_subscribe=True,
            ))

            jwt_token = token.to_jwt()

            return {
                "token": jwt_token,
                "identity": "ai-agent",
            }
        except Exception as e:
            logger.error("livekit_agent_token_failed", error=str(e))
            return None

    @staticmethod
    async def create_session(
        user_id: UUID, title: Optional[str], mode: str,
        provider: str, system_prompt: Optional[str],
        knowledge_base_id: Optional[str], config: dict,
        session: AsyncSession,
    ) -> RealtimeSession:
        """Create a new realtime AI session."""
        rt_session = RealtimeSession(
            user_id=user_id,
            title=title,
            mode=SessionMode(mode) if mode in [m.value for m in SessionMode] else SessionMode.VOICE,
            provider=provider,
            system_prompt=system_prompt,
            knowledge_base_id=knowledge_base_id,
            config_json=json.dumps(config, ensure_ascii=False),
            messages_json="[]",
        )
        session.add(rt_session)
        await session.commit()
        await session.refresh(rt_session)

        # Attach LiveKit WebRTC room for voice/vision modes
        livekit_info = None
        if HAS_LIVEKIT and mode in ("voice", "voice_vision", "meeting"):
            livekit_info = RealtimeAIService._create_livekit_room(
                session_id=str(rt_session.id), user_id=str(user_id),
            )
            if livekit_info:
                # Persist livekit info in session config
                existing_config = json.loads(rt_session.config_json) if rt_session.config_json else {}
                existing_config["livekit"] = livekit_info
                rt_session.config_json = json.dumps(existing_config, ensure_ascii=False)
                session.add(rt_session)
                await session.commit()
                await session.refresh(rt_session)
                logger.info("livekit_room_attached", session_id=str(rt_session.id))

        logger.info("realtime_session_created", session_id=str(rt_session.id), mode=mode,
                     livekit=livekit_info is not None)
        return rt_session

    @staticmethod
    async def send_message(
        session_id: UUID, user_id: UUID, content: str,
        content_type: str, session: AsyncSession,
    ) -> dict:
        """Process a message in a realtime session and get AI response."""
        rt_session = await session.get(RealtimeSession, session_id)
        if not rt_session or rt_session.user_id != user_id:
            return {"error": "Session not found"}

        if rt_session.status != SessionStatus.ACTIVE:
            return {"error": "Session is not active"}

        messages = json.loads(rt_session.messages_json)

        # Add user message
        user_msg = {
            "role": "user",
            "content": content[:10000],
            "content_type": content_type,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {},
        }
        messages.append(user_msg)

        # Build context for AI
        ai_context = await RealtimeAIService._build_context(
            rt_session, messages, content
        )

        # Get AI response
        try:
            from app.ai_assistant.service import AIAssistantService
            result = await AIAssistantService.process_text_with_provider(
                text=ai_context,
                task="conversation",
                provider_name=rt_session.provider,
                user_id=user_id,
                module="realtime_ai",
            )
            ai_response = result.get("processed_text", "")
        except Exception as e:
            ai_response = f"I encountered an error: {str(e)[:200]}"
            logger.error("realtime_ai_error", error=str(e))

        # Add AI message
        ai_msg = {
            "role": "assistant",
            "content": ai_response,
            "content_type": "text",
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {"provider": rt_session.provider},
        }
        messages.append(ai_msg)

        # Update session
        rt_session.messages_json = json.dumps(messages, ensure_ascii=False)
        rt_session.total_turns += 1
        session.add(rt_session)
        await session.commit()

        return {
            "user_message": user_msg,
            "ai_message": ai_msg,
            "turn": rt_session.total_turns,
        }

    @staticmethod
    async def _build_context(
        rt_session: RealtimeSession, messages: list[dict], current_input: str,
    ) -> str:
        """Build conversation context with system prompt and RAG if linked."""
        parts = []

        # System prompt
        if rt_session.system_prompt:
            parts.append(f"System: {rt_session.system_prompt}")

        # RAG context from knowledge base
        if rt_session.knowledge_base_id:
            try:
                from app.modules.knowledge.service import KnowledgeService
                from app.database import get_session_context

                async with get_session_context() as kb_session:
                    results = await KnowledgeService.search(
                        user_id=rt_session.user_id,
                        query=current_input[:300],
                        session=kb_session,
                        limit=3,
                    )
                if results:
                    kb_context = "\n".join(
                        f"[{r.get('filename', '')}] {r.get('content', '')[:400]}"
                        for r in results
                    )
                    parts.append(f"Relevant knowledge base context:\n{kb_context}")
            except Exception:
                pass

        # Recent conversation history (last 10 turns)
        recent = messages[-20:]  # Last 20 messages = ~10 turns
        if recent:
            history = "\n".join(
                f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content'][:500]}"
                for m in recent[:-1]  # Exclude the just-added user message
            )
            if history:
                parts.append(f"Conversation history:\n{history}")

        # Current user input
        parts.append(f"User: {current_input}")

        return "\n\n".join(parts)

    @staticmethod
    async def end_session(
        session_id: UUID, user_id: UUID, session: AsyncSession,
        generate_summary: bool = True,
    ) -> Optional[RealtimeSession]:
        """End a realtime session and optionally generate summary."""
        rt_session = await session.get(RealtimeSession, session_id)
        if not rt_session or rt_session.user_id != user_id:
            return None

        rt_session.status = SessionStatus.ENDED
        rt_session.ended_at = datetime.utcnow()

        # Generate transcript
        messages = json.loads(rt_session.messages_json)
        transcript = "\n\n".join(
            f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}"
            for m in messages
        )
        rt_session.transcript = transcript[:50000]

        # Generate summary
        if generate_summary and messages:
            try:
                from app.ai_assistant.service import AIAssistantService
                result = await AIAssistantService.process_text_with_provider(
                    text=f"Summarize this conversation concisely:\n\n{transcript[:8000]}",
                    task="summarize",
                    provider_name="gemini",
                    user_id=user_id,
                    module="realtime_ai",
                )
                rt_session.summary = result.get("processed_text", "")
            except Exception:
                pass

        session.add(rt_session)
        await session.commit()
        await session.refresh(rt_session)
        return rt_session

    @staticmethod
    async def get_session(
        session_id: UUID, user_id: UUID, session: AsyncSession,
    ) -> Optional[RealtimeSession]:
        rt_session = await session.get(RealtimeSession, session_id)
        if rt_session and rt_session.user_id != user_id:
            return None
        return rt_session

    @staticmethod
    async def list_sessions(
        user_id: UUID, session: AsyncSession, limit: int = 20,
    ) -> list[RealtimeSession]:
        result = await session.execute(
            select(RealtimeSession).where(RealtimeSession.user_id == user_id)
            .order_by(RealtimeSession.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_transcript(
        session_id: UUID, user_id: UUID, session: AsyncSession,
    ) -> Optional[dict]:
        rt_session = await session.get(RealtimeSession, session_id)
        if not rt_session or rt_session.user_id != user_id:
            return None
        messages = json.loads(rt_session.messages_json)
        return {
            "session_id": str(rt_session.id),
            "title": rt_session.title,
            "mode": rt_session.mode.value if hasattr(rt_session.mode, "value") else rt_session.mode,
            "messages": messages,
            "summary": rt_session.summary,
            "total_turns": rt_session.total_turns,
            "duration_s": (
                (rt_session.ended_at - rt_session.started_at).total_seconds()
                if rt_session.ended_at else 0
            ),
        }

    @staticmethod
    def get_config() -> dict:
        config = {**REALTIME_CONFIG}
        config["livekit_available"] = HAS_LIVEKIT
        config["webrtc_enabled"] = HAS_LIVEKIT
        if HAS_LIVEKIT:
            config["livekit_url"] = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        return config
