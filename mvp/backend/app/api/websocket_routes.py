"""
WebSocket endpoints and notification REST API.

Provides:
- WS /ws/{token} - Main WebSocket endpoint with JWT auth via URL path
- GET /api/notifications - List notifications
- PUT /api/notifications/{id}/read - Mark notification read
- PUT /api/notifications/read-all - Mark all read
- GET /api/notifications/unread-count - Unread count
"""

import json
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user, get_user_by_email
from app.config import settings
from app.core.notifications import NotificationService
from app.core.token_blacklist import is_blacklisted, is_user_tokens_revoked
from app.core.websocket_manager import manager, build_message
from app.database import get_session, get_session_context
from app.models.user import User
from app.rate_limit import limiter

logger = structlog.get_logger()

router = APIRouter()


# ---------------------------------------------------------------------------
# WebSocket auth helper
# ---------------------------------------------------------------------------

async def _authenticate_ws_token(token: str) -> tuple[str, str]:
    """
    Validate a JWT token for WebSocket authentication.

    Returns (user_id_str, user_name) on success.
    Raises ValueError on invalid/expired/revoked tokens.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}")

    email: str = payload.get("sub")
    if not email:
        raise ValueError("Token missing subject claim")

    # Reject refresh tokens
    if payload.get("type") == "refresh":
        raise ValueError("Refresh tokens cannot be used for WebSocket auth")

    # Check blacklist
    jti = payload.get("jti")
    if jti and await is_blacklisted(jti):
        raise ValueError("Token has been revoked")

    iat = payload.get("iat")
    if await is_user_tokens_revoked(email, iat):
        raise ValueError("User tokens have been revoked")

    # Fetch user from DB to get ID and verify active status
    async with get_session_context() as session:
        user = await get_user_by_email(session, email)
        if user is None:
            raise ValueError("User not found")
        if not user.is_active:
            raise ValueError("User is inactive")
        return str(user.id), user.full_name or user.email


# ---------------------------------------------------------------------------
# WS /ws/{token} - Main WebSocket endpoint
# ---------------------------------------------------------------------------

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Main WebSocket endpoint.

    Authentication is done via JWT token in the URL path since
    browsers do not support Authorization headers on WebSocket upgrades.

    On connect, the user is added to the 'global' room.

    Message types handled:
    - chat: broadcast to room
    - typing: broadcast typing indicator to room
    - join_room: add user to a specific room
    - leave_room: remove user from a room
    - presence: update presence status
    - ping: respond with pong (keepalive)
    """
    # Authenticate
    try:
        user_id, user_name = await _authenticate_ws_token(token)
    except ValueError as e:
        logger.warning("ws_auth_failed", error=str(e))
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # Connect to global room
    await manager.connect(websocket, user_id, "global", user_name=user_name)

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(
                    build_message("system", {"error": "Invalid JSON"}, user_id=user_id)
                )
                continue

            msg_type = data.get("type", "")
            room_id = data.get("room_id", "global")
            payload = data.get("data", {})

            # -----------------------------------------------------------
            # Route by message type
            # -----------------------------------------------------------

            if msg_type == "chat":
                chat_msg = build_message(
                    "chat",
                    {
                        "content": payload.get("content", ""),
                        "sender_name": user_name,
                    },
                    room_id=room_id,
                    user_id=user_id,
                )
                await manager.broadcast_room(room_id, chat_msg, exclude_user=user_id)

            elif msg_type == "typing":
                typing_msg = build_message(
                    "typing",
                    {
                        "is_typing": payload.get("is_typing", True),
                        "sender_name": user_name,
                    },
                    room_id=room_id,
                    user_id=user_id,
                )
                await manager.broadcast_room(room_id, typing_msg, exclude_user=user_id)

            elif msg_type == "join_room":
                target_room = payload.get("room_id", "")
                if target_room:
                    await manager.connect(websocket, user_id, target_room, user_name=user_name)
                    # Confirm join to the user
                    await websocket.send_text(
                        build_message(
                            "system",
                            {
                                "action": "joined_room",
                                "room_id": target_room,
                                "users": await manager.get_room_users(target_room),
                            },
                            room_id=target_room,
                            user_id=user_id,
                        )
                    )

            elif msg_type == "leave_room":
                target_room = payload.get("room_id", "")
                if target_room and target_room != "global":
                    await manager.disconnect(user_id, target_room)
                    await websocket.send_text(
                        build_message(
                            "system",
                            {"action": "left_room", "room_id": target_room},
                            room_id=target_room,
                            user_id=user_id,
                        )
                    )

            elif msg_type == "presence":
                new_status = payload.get("status", "online")
                if new_status in ("online", "away", "busy"):
                    await manager.update_presence(user_id, new_status, payload.get("metadata"))

            elif msg_type == "ping":
                await websocket.send_text(
                    build_message("pong", {}, user_id=user_id)
                )

            else:
                await websocket.send_text(
                    build_message(
                        "system",
                        {"error": f"Unknown message type: {msg_type}"},
                        user_id=user_id,
                    )
                )

    except WebSocketDisconnect:
        logger.info("ws_client_disconnected", user_id=user_id)
    except Exception as e:
        logger.error("ws_error", user_id=user_id, error=str(e), error_type=type(e).__name__)
    finally:
        await manager.disconnect_all(user_id)


# ---------------------------------------------------------------------------
# REST API - Notifications
# ---------------------------------------------------------------------------

@router.get("/api/notifications", tags=["Notifications"])
@limiter.limit("30/minute")
async def list_notifications(
    request: Request,
    unread_only: bool = Query(False, description="Filter to unread notifications only"),
    limit: int = Query(50, ge=1, le=200, description="Maximum items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    List notifications for the current user.

    Rate limit: 30 requests/minute
    """
    notifications = await NotificationService.get_notifications(
        user_id=current_user.id,
        session=session,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return {
        "items": notifications,
        "count": len(notifications),
    }


@router.put("/api/notifications/{notification_id}/read", tags=["Notifications"])
@limiter.limit("60/minute")
async def mark_notification_read(
    request: Request,
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Mark a single notification as read.

    Rate limit: 60 requests/minute
    """
    success = await NotificationService.mark_read(
        user_id=current_user.id,
        notification_id=notification_id,
        session=session,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return {"message": "Notification marked as read"}


@router.put("/api/notifications/read-all", tags=["Notifications"])
@limiter.limit("10/minute")
async def mark_all_notifications_read(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Mark all unread notifications as read.

    Rate limit: 10 requests/minute
    """
    count = await NotificationService.mark_all_read(
        user_id=current_user.id,
        session=session,
    )
    return {"message": f"{count} notifications marked as read", "count": count}


@router.get("/api/notifications/unread-count", tags=["Notifications"])
@limiter.limit("60/minute")
async def get_unread_count(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get the count of unread notifications.

    Rate limit: 60 requests/minute
    """
    count = await NotificationService.get_unread_count(
        user_id=current_user.id,
        session=session,
    )
    return {"unread_count": count}
