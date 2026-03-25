"""
Conversation service - Business logic for contextual post-transcription chat
"""

from datetime import UTC, datetime
from typing import Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.conversation import Conversation, Message
from app.models.transcription import Transcription

logger = structlog.get_logger(__name__)


class ConversationService:
    """
    Service for managing conversations and messages.

    Handles creation of conversations (optionally linked to transcriptions),
    message persistence, history retrieval, and conversation lifecycle.
    """

    @staticmethod
    async def create_conversation(
        session: AsyncSession,
        user_id: UUID,
        transcription_id: Optional[UUID] = None,
    ) -> Conversation:
        """
        Create a new conversation, optionally seeded with transcription context.

        When a transcription_id is provided, the completed transcription text is
        injected as a system message so the AI assistant has full context for
        subsequent questions.

        Args:
            session: Database session.
            user_id: Owner of the conversation.
            transcription_id: Optional transcription to attach as context.

        Returns:
            The newly created Conversation.

        Raises:
            ValueError: If the transcription is not found or not owned by user.
        """
        conversation = Conversation(
            user_id=user_id,
            transcription_id=transcription_id,
        )
        session.add(conversation)
        await session.flush()

        # If a transcription is linked, inject its text as a system message
        if transcription_id is not None:
            transcription = await session.get(Transcription, transcription_id)
            if transcription is None or transcription.user_id != user_id:
                raise ValueError(
                    f"Transcription {transcription_id} not found or not owned by user"
                )

            if transcription.text:
                system_content = (
                    "The following is the transcription text for context. "
                    "Use it to answer the user's questions accurately.\n\n"
                    f"--- TRANSCRIPTION START ---\n{transcription.text}\n--- TRANSCRIPTION END ---"
                )
                system_message = Message(
                    conversation_id=conversation.id,
                    role="system",
                    content=system_content,
                )
                session.add(system_message)

        await session.commit()
        await session.refresh(conversation)

        logger.info(
            "conversation_created",
            conversation_id=str(conversation.id),
            user_id=str(user_id),
            transcription_id=str(transcription_id) if transcription_id else None,
        )

        return conversation

    @staticmethod
    async def add_message(
        session: AsyncSession,
        conversation_id: UUID,
        role: str,
        content: str,
        provider: Optional[str] = None,
        tokens_used: Optional[int] = None,
    ) -> Message:
        """
        Append a message to a conversation and update the conversation timestamp.

        On the first user message, the conversation title is auto-generated from
        the message content (truncated to 80 characters).

        Args:
            session: Database session.
            conversation_id: Target conversation.
            role: Message role ("user", "assistant", "system").
            content: Message body.
            provider: AI provider used (for assistant messages).
            tokens_used: Token count (for assistant messages).

        Returns:
            The persisted Message.
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            provider=provider,
            tokens_used=tokens_used,
        )
        session.add(message)

        # Update conversation timestamp
        conversation = await session.get(Conversation, conversation_id)
        if conversation is not None:
            conversation.updated_at = datetime.now(UTC)

            # Auto-generate title from first user message if title is empty
            if conversation.title is None and role == "user":
                truncated = content[:80].strip()
                if len(content) > 80:
                    truncated += "..."
                conversation.title = truncated

        await session.commit()
        await session.refresh(message)

        logger.info(
            "message_added",
            message_id=str(message.id),
            conversation_id=str(conversation_id),
            role=role,
            content_length=len(content),
        )

        return message

    @staticmethod
    async def get_conversation(
        session: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Optional[Dict]:
        """
        Retrieve a conversation with all its messages, scoped to the owning user.

        Args:
            session: Database session.
            conversation_id: Conversation to retrieve.
            user_id: Owner for access control.

        Returns:
            Dict with conversation data and messages list, or None if not found.
        """
        conversation = await session.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            return None

        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        result = await session.execute(statement)
        messages = result.scalars().all()

        return {
            "id": conversation.id,
            "title": conversation.title,
            "transcription_id": conversation.transcription_id,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "provider": msg.provider,
                    "created_at": msg.created_at,
                }
                for msg in messages
            ],
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        }

    @staticmethod
    async def list_conversations(
        session: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[Dict], int]:
        """
        List conversations for a user with pagination and message counts.

        Args:
            session: Database session.
            user_id: Owner filter.
            skip: Pagination offset.
            limit: Page size.

        Returns:
            Tuple of (conversation list with message_count, total count).
        """
        # Total count
        count_stmt = (
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.user_id == user_id)
        )
        count_result = await session.execute(count_stmt)
        total = count_result.scalar_one()

        # Fetch conversations
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        conversations = result.scalars().all()

        # Fetch message counts in bulk
        if conversations:
            conv_ids = [c.id for c in conversations]
            msg_count_stmt = (
                select(
                    Message.conversation_id,
                    func.count().label("cnt"),
                )
                .where(Message.conversation_id.in_(conv_ids))
                .group_by(Message.conversation_id)
            )
            msg_count_result = await session.execute(msg_count_stmt)
            count_map = {row.conversation_id: row.cnt for row in msg_count_result.all()}
        else:
            count_map = {}

        items = [
            {
                "id": conv.id,
                "title": conv.title,
                "transcription_id": conv.transcription_id,
                "message_count": count_map.get(conv.id, 0),
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
            }
            for conv in conversations
        ]

        return items, total

    @staticmethod
    async def delete_conversation(
        session: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Delete a conversation and all its messages, scoped to the owning user.

        Args:
            session: Database session.
            conversation_id: Conversation to delete.
            user_id: Owner for access control.

        Returns:
            True if deleted, False if not found or not owned.
        """
        conversation = await session.get(Conversation, conversation_id)
        if conversation is None or conversation.user_id != user_id:
            return False

        # Delete all messages first
        msg_stmt = select(Message).where(Message.conversation_id == conversation_id)
        msg_result = await session.execute(msg_stmt)
        messages = msg_result.scalars().all()
        for msg in messages:
            await session.delete(msg)

        await session.delete(conversation)
        await session.commit()

        logger.info(
            "conversation_deleted",
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            messages_deleted=len(messages),
        )

        return True

    @staticmethod
    async def get_conversation_history(
        session: AsyncSession,
        conversation_id: UUID,
    ) -> List[Dict[str, str]]:
        """
        Retrieve the conversation history formatted for AI provider consumption.

        Returns messages in chronological order as a list of {role, content} dicts,
        suitable for passing directly to BaseAIProvider.stream_chat() as
        conversation_history.

        Args:
            session: Database session.
            conversation_id: Target conversation.

        Returns:
            List of dicts with 'role' and 'content' keys.
        """
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        result = await session.execute(statement)
        messages = result.scalars().all()

        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
