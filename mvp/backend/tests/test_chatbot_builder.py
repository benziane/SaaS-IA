"""
Tests for the AI Chatbot Builder module - service, publish/unpublish, public chat, analytics.

All tests mock DB and AI providers. Uses pytest-asyncio.
"""

import json
import secrets
from datetime import UTC, datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.ai_chatbot_builder import Chatbot, ChatbotConversation


# ---------------------------------------------------------------------------
# Helper to create a chatbot in the DB
# ---------------------------------------------------------------------------


async def _create_chatbot(
    session,
    user_id,
    name="Test Bot",
    system_prompt="You are a helpful assistant.",
    is_published=False,
    embed_token=None,
):
    chatbot = Chatbot(
        user_id=user_id,
        name=name,
        description="A test chatbot",
        system_prompt=system_prompt,
        model="gemini",
        personality="professional",
        welcome_message="Hello! How can I help?",
        is_published=is_published,
        embed_token=embed_token,
        channels="[]",
        conversations_count=0,
    )
    session.add(chatbot)
    await session.commit()
    await session.refresh(chatbot)
    return chatbot


# ---------------------------------------------------------------------------
# ChatbotBuilderService tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestChatbotBuilderService:
    """Tests for ChatbotBuilderService business logic."""

    async def test_create_chatbot(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()

        chatbot = await service.create_chatbot(
            user_id=user_id,
            data={
                "name": "My Support Bot",
                "system_prompt": "You are a customer support agent.",
                "model": "gemini",
                "personality": "friendly",
                "welcome_message": "Hi there!",
            },
        )

        assert chatbot.name == "My Support Bot"
        assert chatbot.system_prompt == "You are a customer support agent."
        assert chatbot.user_id == user_id
        assert chatbot.is_published is False
        assert chatbot.embed_token is None

    async def test_list_chatbots(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()

        await _create_chatbot(session, user_id, name="Bot 1")
        await _create_chatbot(session, user_id, name="Bot 2")

        bots = await service.list_chatbots(user_id)
        assert len(bots) == 2

    async def test_list_chatbots_excludes_deleted(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()

        bot = await _create_chatbot(session, user_id, name="Active Bot")
        deleted_bot = await _create_chatbot(session, user_id, name="Deleted Bot")
        deleted_bot.is_deleted = True
        session.add(deleted_bot)
        await session.commit()

        bots = await service.list_chatbots(user_id)
        assert len(bots) == 1
        assert bots[0].name == "Active Bot"

    async def test_get_chatbot(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()

        bot = await _create_chatbot(session, user_id)
        result = await service.get_chatbot(user_id, bot.id)
        assert result is not None
        assert result.id == bot.id

    async def test_get_chatbot_wrong_user(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()

        bot = await _create_chatbot(session, user_id)
        result = await service.get_chatbot(uuid4(), bot.id)
        assert result is None

    async def test_publish_chatbot_generates_token(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()

        bot = await _create_chatbot(session, user_id)
        assert bot.embed_token is None

        published = await service.publish_chatbot(user_id, bot.id)
        assert published is not None
        assert published.is_published is True
        assert published.embed_token is not None
        assert len(published.embed_token) > 10

    async def test_unpublish_chatbot_revokes_token(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()

        token = secrets.token_urlsafe(32)
        bot = await _create_chatbot(
            session, user_id, is_published=True, embed_token=token
        )

        unpublished = await service.unpublish_chatbot(user_id, bot.id)
        assert unpublished is not None
        assert unpublished.is_published is False
        assert unpublished.embed_token is None

    async def test_chat_public_valid_token(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()
        token = secrets.token_urlsafe(32)

        bot = await _create_chatbot(
            session, user_id, is_published=True, embed_token=token
        )

        with patch(
            "app.ai_assistant.service.AIAssistantService"
        ) as mock_ai:
            mock_ai.process_text_with_provider = AsyncMock(
                return_value={"processed_text": "Hello! I can help you with that."}
            )

            result = await service.chat(
                chatbot_id=bot.id,
                embed_token=token,
                message="How do I get started?",
            )

        assert "error" not in result
        assert "session_id" in result
        assert result["message"]["role"] == "assistant"
        assert "Hello!" in result["message"]["content"]

    async def test_chat_invalid_token(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)

        result = await service.chat(
            chatbot_id=uuid4(),
            embed_token="invalid_token_xyz",
            message="Hello",
        )

        assert "error" in result

    async def test_chat_ai_response_fallback_on_error(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()
        token = secrets.token_urlsafe(32)

        bot = await _create_chatbot(
            session, user_id, is_published=True, embed_token=token
        )

        with patch(
            "app.ai_assistant.service.AIAssistantService"
        ) as mock_ai:
            mock_ai.process_text_with_provider = AsyncMock(
                side_effect=Exception("LLM service unavailable")
            )

            result = await service.chat(
                chatbot_id=bot.id,
                embed_token=token,
                message="Tell me something",
            )

        assert "error" not in result
        assert "technical difficulties" in result["message"]["content"]

    async def test_chat_history(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()
        token = secrets.token_urlsafe(32)

        bot = await _create_chatbot(
            session, user_id, is_published=True, embed_token=token
        )

        # Create a conversation with some messages
        conv = ChatbotConversation(
            chatbot_id=bot.id,
            session_id="test_session_123",
            messages=json.dumps([
                {"id": "m1", "role": "user", "content": "Hi", "created_at": "2025-01-01T00:00:00"},
                {"id": "m2", "role": "assistant", "content": "Hello!", "created_at": "2025-01-01T00:00:01"},
            ]),
        )
        session.add(conv)
        await session.commit()

        history = await service.get_chat_history(bot.id, "test_session_123")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    async def test_chat_history_empty_session(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)

        history = await service.get_chat_history(uuid4(), "nonexistent_session")
        assert history == []

    async def test_embed_code_published(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()
        token = secrets.token_urlsafe(32)

        bot = await _create_chatbot(
            session, user_id, is_published=True, embed_token=token
        )

        embed = await service.get_embed_code(user_id, bot.id)
        assert embed is not None
        assert embed["embed_token"] == token
        assert "<script" in embed["html_snippet"]
        assert token in embed["html_snippet"]
        assert "script_url" in embed

    async def test_embed_code_unpublished(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()

        bot = await _create_chatbot(session, user_id, is_published=False)

        embed = await service.get_embed_code(user_id, bot.id)
        assert embed is None

    async def test_analytics(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()

        bot = await _create_chatbot(session, user_id)

        # Create some conversations
        for i in range(3):
            conv = ChatbotConversation(
                chatbot_id=bot.id,
                session_id=f"session_{i}",
                messages=json.dumps([
                    {"role": "user", "content": f"Question {i}"},
                    {"role": "assistant", "content": f"Answer {i}"},
                ]),
            )
            session.add(conv)
        await session.commit()

        analytics = await service.get_analytics(user_id, bot.id)
        assert analytics is not None
        assert analytics["total_conversations"] == 3
        assert analytics["total_messages"] == 6
        assert analytics["avg_messages_per_conversation"] == 2.0

    async def test_analytics_not_found(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        analytics = await service.get_analytics(uuid4(), uuid4())
        assert analytics is None

    async def test_delete_chatbot(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()

        bot = await _create_chatbot(
            session, user_id, is_published=True, embed_token="tok123"
        )

        deleted = await service.delete_chatbot(user_id, bot.id)
        assert deleted is True

        await session.refresh(bot)
        assert bot.is_deleted is True
        assert bot.is_published is False
        assert bot.embed_token is None

    async def test_update_chatbot(self, session):
        from app.modules.ai_chatbot_builder.service import ChatbotBuilderService

        service = ChatbotBuilderService(session)
        user_id = uuid4()

        bot = await _create_chatbot(session, user_id, name="Original Name")

        updated = await service.update_chatbot(
            user_id, bot.id, {"name": "New Name", "personality": "casual"}
        )
        assert updated is not None
        assert updated.name == "New Name"
        assert updated.personality == "casual"


# ---------------------------------------------------------------------------
# Route-level auth tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestChatbotRoutesAuth:
    """Test that authenticated chatbot endpoints require authentication."""

    async def test_create_chatbot_requires_auth(self, client):
        resp = await client.post("/api/chatbots", json={
            "name": "test",
            "system_prompt": "You are a test bot",
        })
        assert resp.status_code in (401, 403)

    async def test_list_chatbots_requires_auth(self, client):
        resp = await client.get("/api/chatbots")
        assert resp.status_code in (401, 403)

    async def test_publish_chatbot_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.post(f"/api/chatbots/{fake_id}/publish")
        assert resp.status_code in (401, 403)

    async def test_analytics_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.get(f"/api/chatbots/{fake_id}/analytics")
        assert resp.status_code in (401, 403)

    async def test_embed_code_requires_auth(self, client):
        fake_id = str(uuid4())
        resp = await client.get(f"/api/chatbots/{fake_id}/embed-code")
        assert resp.status_code in (401, 403)
