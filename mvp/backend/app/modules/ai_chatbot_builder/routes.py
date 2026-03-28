"""
AI Chatbot Builder API routes - CRUD, publish/unpublish, public chat, channels, analytics.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user
from app.modules.auth_guards.middleware import require_verified_email
from app.database import get_session
from app.models.user import User
from app.modules.ai_chatbot_builder.schemas import (
    ChannelConfig,
    ChatbotAnalytics,
    ChatbotCreate,
    ChatbotRead,
    ChatbotUpdate,
    ChatMessageCreate,
    ChatMessageRead,
    EmbedCodeResponse,
)
from app.modules.ai_chatbot_builder.service import ChatbotBuilderService
from app.rate_limit import limiter

router = APIRouter()


def _chatbot_to_read(chatbot) -> dict:
    """Convert Chatbot model to ChatbotRead-compatible dict."""
    import json
    return {
        "id": chatbot.id,
        "user_id": chatbot.user_id,
        "name": chatbot.name,
        "description": chatbot.description,
        "system_prompt": chatbot.system_prompt,
        "model": chatbot.model,
        "knowledge_base_ids": json.loads(chatbot.knowledge_base_ids) if chatbot.knowledge_base_ids else None,
        "personality": chatbot.personality,
        "welcome_message": chatbot.welcome_message,
        "theme": json.loads(chatbot.theme) if chatbot.theme else None,
        "is_published": chatbot.is_published,
        "embed_token": chatbot.embed_token,
        "channels": json.loads(chatbot.channels) if chatbot.channels else [],
        "conversations_count": chatbot.conversations_count,
        "created_at": chatbot.created_at,
        "updated_at": chatbot.updated_at,
    }


# ─── Authenticated CRUD endpoints ──────────────────────────────────────────────


@router.post("", response_model=ChatbotRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_chatbot(
    request: Request,
    body: ChatbotCreate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Create a new chatbot with system prompt and configuration."""
    service = ChatbotBuilderService(session)
    chatbot = await service.create_chatbot(current_user.id, body.model_dump())
    return _chatbot_to_read(chatbot)


@router.get("", response_model=list[ChatbotRead])
@limiter.limit("20/minute")
async def list_chatbots(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List all chatbots for the current user."""
    service = ChatbotBuilderService(session)
    chatbots = await service.list_chatbots(current_user.id)
    return [_chatbot_to_read(c) for c in chatbots]


@router.get("/{chatbot_id}", response_model=ChatbotRead)
@limiter.limit("20/minute")
async def get_chatbot(
    request: Request,
    chatbot_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get chatbot details."""
    service = ChatbotBuilderService(session)
    chatbot = await service.get_chatbot(current_user.id, chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return _chatbot_to_read(chatbot)


@router.put("/{chatbot_id}", response_model=ChatbotRead)
@limiter.limit("10/minute")
async def update_chatbot(
    request: Request,
    chatbot_id: UUID,
    body: ChatbotUpdate,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Update chatbot settings."""
    service = ChatbotBuilderService(session)
    chatbot = await service.update_chatbot(
        current_user.id, chatbot_id, body.model_dump(exclude_unset=True)
    )
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return _chatbot_to_read(chatbot)


@router.delete("/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_chatbot(
    request: Request,
    chatbot_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Soft delete a chatbot."""
    service = ChatbotBuilderService(session)
    deleted = await service.delete_chatbot(current_user.id, chatbot_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return None


# ─── Publish / Unpublish ────────────────────────────────────────────────────────


@router.post("/{chatbot_id}/publish", response_model=ChatbotRead)
@limiter.limit("5/minute")
async def publish_chatbot(
    request: Request,
    chatbot_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Publish chatbot and generate embed token."""
    service = ChatbotBuilderService(session)
    chatbot = await service.publish_chatbot(current_user.id, chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return _chatbot_to_read(chatbot)


@router.post("/{chatbot_id}/unpublish", response_model=ChatbotRead)
@limiter.limit("5/minute")
async def unpublish_chatbot(
    request: Request,
    chatbot_id: UUID,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Unpublish chatbot and revoke embed token."""
    service = ChatbotBuilderService(session)
    chatbot = await service.unpublish_chatbot(current_user.id, chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return _chatbot_to_read(chatbot)


# ─── Channels ───────────────────────────────────────────────────────────────────


@router.post("/{chatbot_id}/channels", response_model=ChatbotRead)
@limiter.limit("10/minute")
async def add_channel(
    request: Request,
    chatbot_id: UUID,
    body: ChannelConfig,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Add a deployment channel to a chatbot."""
    service = ChatbotBuilderService(session)
    chatbot = await service.add_channel(current_user.id, chatbot_id, body.model_dump())
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return _chatbot_to_read(chatbot)


@router.delete("/{chatbot_id}/channels/{channel_type}", response_model=ChatbotRead)
@limiter.limit("10/minute")
async def remove_channel(
    request: Request,
    chatbot_id: UUID,
    channel_type: str,
    current_user: User = Depends(require_verified_email),
    session: AsyncSession = Depends(get_session),
):
    """Remove a deployment channel from a chatbot."""
    service = ChatbotBuilderService(session)
    chatbot = await service.remove_channel(current_user.id, chatbot_id, channel_type)
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return _chatbot_to_read(chatbot)


# ─── Analytics & Embed Code ─────────────────────────────────────────────────────


@router.get("/{chatbot_id}/analytics", response_model=ChatbotAnalytics)
@limiter.limit("20/minute")
async def get_analytics(
    request: Request,
    chatbot_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get chatbot conversation analytics."""
    service = ChatbotBuilderService(session)
    analytics = await service.get_analytics(current_user.id, chatbot_id)
    if not analytics:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return analytics


@router.get("/{chatbot_id}/embed-code", response_model=EmbedCodeResponse)
@limiter.limit("20/minute")
async def get_embed_code(
    request: Request,
    chatbot_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get the HTML/JS embed snippet for website integration."""
    service = ChatbotBuilderService(session)
    embed = await service.get_embed_code(current_user.id, chatbot_id)
    if not embed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found or not published",
        )
    return embed


# ─── Public Chat endpoints (no auth, validate embed_token) ──────────────────────


@router.post("/widget/{embed_token}/chat")
@limiter.limit("30/minute")
async def public_chat(
    request: Request,
    embed_token: str,
    body: ChatMessageCreate,
    session: AsyncSession = Depends(get_session),
):
    """Public chat endpoint for embedded widgets. No auth required.

    Validates the embed_token to identify the chatbot.
    """
    service = ChatbotBuilderService(session)

    # Find chatbot by embed_token
    chatbot = await service._get_chatbot_by_token(embed_token)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found or not published",
        )

    result = await service.chat(
        chatbot_id=chatbot.id,
        embed_token=embed_token,
        message=body.message,
        session_id=body.session_id,
    )

    if "error" in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])

    return result


@router.get("/widget/{embed_token}/history/{session_id}")
@limiter.limit("20/minute")
async def public_chat_history(
    request: Request,
    embed_token: str,
    session_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get chat history for a public widget session. No auth required."""
    service = ChatbotBuilderService(session)

    chatbot = await service._get_chatbot_by_token(embed_token)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found or not published",
        )

    messages = await service.get_chat_history(chatbot.id, session_id)
    return {"session_id": session_id, "messages": messages}


@router.get("/widget/{embed_token}/config")
@limiter.limit("30/minute")
async def public_widget_config(
    request: Request,
    embed_token: str,
    session: AsyncSession = Depends(get_session),
):
    """Get public widget configuration (name, welcome message, theme). No auth required."""
    import json
    service = ChatbotBuilderService(session)

    chatbot = await service._get_chatbot_by_token(embed_token)
    if not chatbot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found or not published",
        )

    return {
        "name": chatbot.name,
        "welcome_message": chatbot.welcome_message,
        "theme": json.loads(chatbot.theme) if chatbot.theme else None,
        "personality": chatbot.personality,
    }
