"""
WebSocket Connection Manager with room support and presence tracking.

Manages bidirectional WebSocket connections, room-based messaging,
user presence, and typed message broadcasting.
"""

import asyncio
import json
from datetime import UTC, datetime
from typing import Any, Optional

import structlog
from fastapi import WebSocket

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Presence colors (deterministic per-user for UI consistency)
# ---------------------------------------------------------------------------

_PRESENCE_COLORS = [
    "#EF4444", "#F97316", "#F59E0B", "#84CC16", "#22C55E",
    "#14B8A6", "#06B6D4", "#3B82F6", "#6366F1", "#8B5CF6",
    "#A855F7", "#EC4899", "#F43F5E", "#0EA5E9", "#10B981",
]


def _color_for_user(user_id: str) -> str:
    """Return a deterministic color for a user based on their ID hash."""
    return _PRESENCE_COLORS[hash(user_id) % len(_PRESENCE_COLORS)]


# ---------------------------------------------------------------------------
# Message builder
# ---------------------------------------------------------------------------

def build_message(
    msg_type: str,
    data: dict[str, Any],
    room_id: str = "",
    user_id: str = "",
) -> str:
    """Build a standardized JSON message string."""
    return json.dumps({
        "type": msg_type,
        "data": data,
        "room_id": room_id,
        "user_id": user_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }, default=str)


# ---------------------------------------------------------------------------
# ConnectionManager
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Manages WebSocket connections with room support and presence tracking."""

    def __init__(self) -> None:
        # {room_id: {user_id: websocket}}
        self._connections: dict[str, dict[str, WebSocket]] = {}
        # {user_id: {room_ids}}
        self._user_rooms: dict[str, set[str]] = {}
        # {user_id: {name, status, last_seen, color}}
        self._presence: dict[str, dict[str, Any]] = {}
        # Lock for thread-safe mutations
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Connect / Disconnect
    # ------------------------------------------------------------------

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        room_id: str,
        user_name: str = "",
    ) -> None:
        """Accept the WebSocket and register the user in the given room."""
        await websocket.accept()

        async with self._lock:
            # Register in room
            if room_id not in self._connections:
                self._connections[room_id] = {}
            self._connections[room_id][user_id] = websocket

            # Track which rooms the user is in
            if user_id not in self._user_rooms:
                self._user_rooms[user_id] = set()
            self._user_rooms[user_id].add(room_id)

            # Update presence
            self._presence[user_id] = {
                "name": user_name or user_id,
                "status": "online",
                "last_seen": datetime.now(UTC).isoformat(),
                "color": _color_for_user(user_id),
            }

        logger.info(
            "ws_user_connected",
            user_id=user_id,
            room_id=room_id,
            room_size=len(self._connections.get(room_id, {})),
        )

        # Broadcast join event to room
        join_msg = build_message(
            "presence",
            {
                "action": "join",
                "user_id": user_id,
                "name": user_name or user_id,
                "color": _color_for_user(user_id),
                "online_users": await self.get_room_users(room_id),
            },
            room_id=room_id,
            user_id=user_id,
        )
        await self.broadcast_room(room_id, join_msg, exclude_user=user_id)

    async def disconnect(self, user_id: str, room_id: str) -> None:
        """Remove the user from the given room and broadcast leave event."""
        async with self._lock:
            # Remove from room
            if room_id in self._connections:
                self._connections[room_id].pop(user_id, None)
                if not self._connections[room_id]:
                    del self._connections[room_id]

            # Remove room from user tracking
            if user_id in self._user_rooms:
                self._user_rooms[user_id].discard(room_id)
                if not self._user_rooms[user_id]:
                    del self._user_rooms[user_id]
                    # User fully disconnected - update presence
                    if user_id in self._presence:
                        self._presence[user_id]["status"] = "offline"
                        self._presence[user_id]["last_seen"] = datetime.now(UTC).isoformat()

        logger.info(
            "ws_user_disconnected",
            user_id=user_id,
            room_id=room_id,
        )

        # Broadcast leave event
        leave_msg = build_message(
            "presence",
            {
                "action": "leave",
                "user_id": user_id,
                "online_users": await self.get_room_users(room_id),
            },
            room_id=room_id,
            user_id=user_id,
        )
        await self.broadcast_room(room_id, leave_msg, exclude_user=user_id)

    async def disconnect_all(self, user_id: str) -> None:
        """Remove the user from all rooms (called on WebSocket close)."""
        rooms = list(self._user_rooms.get(user_id, set()))
        for room_id in rooms:
            await self.disconnect(user_id, room_id)

    # ------------------------------------------------------------------
    # Sending messages
    # ------------------------------------------------------------------

    async def _safe_send(self, websocket: WebSocket, message: str) -> bool:
        """Send a message to a single WebSocket, returning False on failure."""
        try:
            await websocket.send_text(message)
            return True
        except Exception:
            return False

    async def send_personal(self, user_id: str, message: str) -> None:
        """Send a message to a specific user across all their rooms."""
        rooms = self._user_rooms.get(user_id, set())
        for room_id in rooms:
            ws = self._connections.get(room_id, {}).get(user_id)
            if ws:
                await self._safe_send(ws, message)
                return  # User has one WS connection; send once

    async def broadcast_room(
        self,
        room_id: str,
        message: str,
        exclude_user: Optional[str] = None,
    ) -> None:
        """Broadcast a message to all users in a room, optionally excluding one."""
        room = self._connections.get(room_id, {})
        disconnected: list[str] = []

        for uid, ws in room.items():
            if uid == exclude_user:
                continue
            success = await self._safe_send(ws, message)
            if not success:
                disconnected.append(uid)

        # Clean up disconnected users
        for uid in disconnected:
            await self.disconnect(uid, room_id)

    async def broadcast_all(self, message: str) -> None:
        """Broadcast a message to every connected user across all rooms."""
        sent_to: set[str] = set()
        for room_id, room in list(self._connections.items()):
            for uid, ws in list(room.items()):
                if uid in sent_to:
                    continue
                await self._safe_send(ws, message)
                sent_to.add(uid)

    # ------------------------------------------------------------------
    # Presence & room queries
    # ------------------------------------------------------------------

    async def get_room_users(self, room_id: str) -> list[dict[str, Any]]:
        """List users in a room with their presence info."""
        room = self._connections.get(room_id, {})
        users = []
        for uid in room:
            presence = self._presence.get(uid, {})
            users.append({
                "user_id": uid,
                "name": presence.get("name", uid),
                "status": presence.get("status", "online"),
                "color": presence.get("color", _color_for_user(uid)),
                "last_seen": presence.get("last_seen"),
            })
        return users

    async def get_user_rooms(self, user_id: str) -> list[str]:
        """List rooms a user is currently in."""
        return list(self._user_rooms.get(user_id, set()))

    async def get_online_users(self) -> list[dict[str, Any]]:
        """Return all online users with their presence info."""
        online = []
        for uid in self._user_rooms:
            presence = self._presence.get(uid, {})
            if presence.get("status") != "offline":
                online.append({
                    "user_id": uid,
                    "name": presence.get("name", uid),
                    "status": presence.get("status", "online"),
                    "color": presence.get("color", _color_for_user(uid)),
                    "rooms": list(self._user_rooms.get(uid, set())),
                })
        return online

    async def update_presence(
        self,
        user_id: str,
        status: str = "online",
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Update user presence status (online/away/busy)."""
        if user_id not in self._presence:
            return

        self._presence[user_id]["status"] = status
        self._presence[user_id]["last_seen"] = datetime.now(UTC).isoformat()
        if metadata:
            self._presence[user_id].update(metadata)

        # Broadcast presence update to all rooms the user is in
        rooms = self._user_rooms.get(user_id, set())
        msg = build_message(
            "presence",
            {
                "action": "update",
                "user_id": user_id,
                "status": status,
                "name": self._presence[user_id].get("name", user_id),
                "color": self._presence[user_id].get("color"),
            },
            user_id=user_id,
        )
        for room_id in rooms:
            await self.broadcast_room(room_id, msg, exclude_user=user_id)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def total_connections(self) -> int:
        """Total number of unique connected users."""
        return len(self._user_rooms)

    @property
    def total_rooms(self) -> int:
        """Total number of active rooms."""
        return len(self._connections)


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

manager = ConnectionManager()
