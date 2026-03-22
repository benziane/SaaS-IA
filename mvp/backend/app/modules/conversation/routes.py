"""
Conversation API Routes - Chat with AI assistant about transcriptions.

Provides CRUD operations for conversations and SSE-streamed chat responses.
"""

import json
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import structlog

from app.auth import get_current_user
from app.database import get_session
from app.models.user import User
from app.models.transcription import Transcription, TranscriptionStatus
from app.models.conversation import Conversation, Message, MessageRole
from app.modules.conversation.schemas import (
    ConversationCreate,
    ConversationRead,
    ConversationWithMessages,
    MessageCreate,
    MessageRead,
    PaginatedConversations,
)
from app.ai_assistant.service import AIAssistantService
from app.ai_assistant.classification.enums import SelectionStrategy
from app.rate_limit import limiter

logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_conversation_or_404(
    conversation_id: UUID,
    user: User,
    session: AsyncSession,
) -> Conversation:
    """Fetch a conversation and verify ownership. Raises 404 / 403."""
    result = await session.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if conversation.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return conversation


async def _count_messages(conversation_id: UUID, session: AsyncSession) -> int:
    """Return the number of messages in a conversation."""
    result = await session.execute(
        select(sa_func.count()).select_from(Message).where(
            Message.conversation_id == conversation_id
        )
    )
    return result.scalar_one()


async def _fetch_messages(
    conversation_id: UUID,
    session: AsyncSession,
) -> list[Message]:
    """Return all messages for a conversation ordered by creation time."""
    result = await session.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


def _build_chat_prompt(messages: list[Message]) -> str:
    """
    Build a single prompt string from conversation history.

    The prompt includes the full conversation so the AI can maintain context.
    System messages are prepended as instructions.
    """
    parts: list[str] = []

    for msg in messages:
        if msg.role == MessageRole.SYSTEM:
            parts.append(f"[Context]\n{msg.content}\n")
        elif msg.role == MessageRole.USER:
            parts.append(f"[User]\n{msg.content}\n")
        elif msg.role == MessageRole.ASSISTANT:
            parts.append(f"[Assistant]\n{msg.content}\n")

    parts.append("[Assistant]\n")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# POST /api/conversations  -  Create a new conversation
# ---------------------------------------------------------------------------

@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_conversation(
    request: Request,
    body: ConversationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new conversation.

    If ``transcription_id`` is provided the transcription text is fetched and
    stored as an initial system message so the AI has context.

    Rate limit: 10 requests/minute
    """
    system_context: Optional[str] = None
    title: Optional[str] = None

    # If a transcription is referenced, pull its text as context.
    if body.transcription_id is not None:
        result = await session.execute(
            select(Transcription).where(Transcription.id == body.transcription_id)
        )
        transcription = result.scalar_one_or_none()

        if transcription is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription not found",
            )

        if transcription.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this transcription",
            )

        if transcription.status != TranscriptionStatus.COMPLETED or not transcription.text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcription is not yet completed or has no text",
            )

        system_context = (
            "The following is a transcription that the user wants to discuss. "
            "Use it as context when answering questions.\n\n"
            f"--- Transcription ---\n{transcription.text}\n--- End ---"
        )
        title = f"Chat about transcription"

    # Persist the conversation.
    conversation = Conversation(
        user_id=current_user.id,
        title=title,
        transcription_id=body.transcription_id,
    )
    session.add(conversation)
    await session.flush()

    # Persist the system context message if present.
    message_count = 0
    if system_context:
        system_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.SYSTEM,
            content=system_context,
        )
        session.add(system_msg)
        message_count = 1

    await session.commit()
    await session.refresh(conversation)

    logger.info(
        "conversation_created",
        user_id=str(current_user.id),
        conversation_id=str(conversation.id),
        has_transcription=body.transcription_id is not None,
    )

    return ConversationRead(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        transcription_id=conversation.transcription_id,
        message_count=message_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


# ---------------------------------------------------------------------------
# GET /api/conversations  -  List conversations
# ---------------------------------------------------------------------------

@router.get("/", response_model=PaginatedConversations)
@limiter.limit("30/minute")
async def list_conversations(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum items to return"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List conversations for the current user with message counts.

    Rate limit: 30 requests/minute
    """
    # Total count
    count_result = await session.execute(
        select(sa_func.count()).select_from(Conversation).where(
            Conversation.user_id == current_user.id
        )
    )
    total = count_result.scalar_one()

    # Fetch page
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    conversations = list(result.scalars().all())

    # Build response with message counts
    items: list[ConversationRead] = []
    for conv in conversations:
        msg_count = await _count_messages(conv.id, session)
        items.append(
            ConversationRead(
                id=conv.id,
                user_id=conv.user_id,
                title=conv.title,
                transcription_id=conv.transcription_id,
                message_count=msg_count,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
        )

    return PaginatedConversations(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total,
    )


# ---------------------------------------------------------------------------
# GET /api/conversations/{id}  -  Get conversation with messages
# ---------------------------------------------------------------------------

@router.get("/{conversation_id}", response_model=ConversationWithMessages)
@limiter.limit("30/minute")
async def get_conversation(
    request: Request,
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a single conversation with its full message history.

    Rate limit: 30 requests/minute
    """
    conversation = await _get_conversation_or_404(
        conversation_id, current_user, session
    )
    messages = await _fetch_messages(conversation.id, session)

    return ConversationWithMessages(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        transcription_id=conversation.transcription_id,
        messages=[MessageRead.model_validate(m) for m in messages],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


# ---------------------------------------------------------------------------
# DELETE /api/conversations/{id}  -  Delete conversation
# ---------------------------------------------------------------------------

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_conversation(
    request: Request,
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Delete a conversation and all its messages.

    Rate limit: 10 requests/minute
    """
    conversation = await _get_conversation_or_404(
        conversation_id, current_user, session
    )

    # Delete messages first (child rows).
    msg_result = await session.execute(
        select(Message).where(Message.conversation_id == conversation.id)
    )
    for msg in msg_result.scalars().all():
        await session.delete(msg)

    await session.delete(conversation)
    await session.commit()

    logger.info(
        "conversation_deleted",
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
    )

    return None


# ---------------------------------------------------------------------------
# POST /api/conversations/{id}/messages  -  Send message & stream AI reply
# ---------------------------------------------------------------------------

@router.post("/{conversation_id}/messages")
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    conversation_id: UUID,
    body: MessageCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Send a user message and receive the AI response via Server-Sent Events.

    The user message is persisted immediately. The assistant response is
    streamed token-by-token in SSE format and persisted once streaming
    completes.

    SSE event format::

        data: {"type": "token", "token": "chunk_text"}
        data: {"type": "done", "provider": "groq", "tokens_streamed": 123}

    Rate limit: 20 requests/minute
    """
    conversation = await _get_conversation_or_404(
        conversation_id, current_user, session
    )

    # 1. Persist the user message.
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=body.content,
    )
    session.add(user_message)

    # Touch conversation updated_at.
    conversation.updated_at = datetime.utcnow()

    # Auto-generate title from first user message if not set.
    if conversation.title is None:
        conversation.title = body.content[:80]

    session.add(conversation)
    await session.commit()
    await session.refresh(user_message)

    # 2. Fetch full conversation history for context.
    messages = await _fetch_messages(conversation.id, session)

    # 3. Build the prompt from history.
    prompt = _build_chat_prompt(messages)

    logger.info(
        "chat_message_received",
        user_id=str(current_user.id),
        conversation_id=str(conversation_id),
        message_length=len(body.content),
        history_length=len(messages),
    )

    # 4. Stream AI response via SSE.
    async def event_generator():
        tokens_streamed = 0
        provider_name = "unknown"
        collected_tokens: list[str] = []

        try:
            is_first = True
            async for chunk in AIAssistantService.stream_text(
                text=prompt,
                task="improve_quality",
                target_language="french",
                strategy=SelectionStrategy.BALANCED,
            ):
                # Check for client disconnect.
                if await request.is_disconnected():
                    logger.info(
                        "chat_stream_client_disconnected",
                        user_id=str(current_user.id),
                        conversation_id=str(conversation_id),
                        tokens_streamed=tokens_streamed,
                    )
                    break

                if is_first and "provider" in chunk:
                    provider_name = chunk["provider"]
                    is_first = False
                    continue

                if "token" in chunk:
                    token_text = chunk["token"]
                    tokens_streamed += 1
                    collected_tokens.append(token_text)
                    event_data = json.dumps(
                        {"type": "token", "token": token_text},
                        ensure_ascii=False,
                    )
                    yield f"data: {event_data}\n\n"

            # Final SSE event.
            done_data = json.dumps({
                "type": "done",
                "provider": provider_name,
                "tokens_streamed": tokens_streamed,
            })
            yield f"data: {done_data}\n\n"

            logger.info(
                "chat_stream_complete",
                user_id=str(current_user.id),
                conversation_id=str(conversation_id),
                provider=provider_name,
                tokens_streamed=tokens_streamed,
            )

            # 5. Persist the assistant response.
            assistant_text = "".join(collected_tokens)
            if assistant_text:
                from app.database import get_session_context

                async with get_session_context() as save_session:
                    assistant_message = Message(
                        conversation_id=conversation_id,
                        role=MessageRole.ASSISTANT,
                        content=assistant_text,
                    )
                    save_session.add(assistant_message)

                    # Update conversation timestamp.
                    conv_result = await save_session.execute(
                        select(Conversation).where(
                            Conversation.id == conversation_id
                        )
                    )
                    conv = conv_result.scalar_one_or_none()
                    if conv is not None:
                        conv.updated_at = datetime.utcnow()
                        save_session.add(conv)

                    await save_session.commit()

                logger.info(
                    "assistant_message_saved",
                    conversation_id=str(conversation_id),
                    content_length=len(assistant_text),
                )

        except Exception as e:
            logger.error(
                "chat_stream_error",
                user_id=str(current_user.id),
                conversation_id=str(conversation_id),
                error=str(e),
                error_type=type(e).__name__,
            )
            error_data = json.dumps(
                {"type": "error", "error": str(e)},
                ensure_ascii=False,
            )
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
