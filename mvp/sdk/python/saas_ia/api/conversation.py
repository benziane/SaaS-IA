"""Conversation API — contextual AI chat with history."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class ConversationAPI(BaseAPI):
    """Wraps ``/api/conversations`` endpoints."""

    async def create(
        self,
        *,
        transcription_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new conversation (optionally linked to a transcription)."""
        body: dict[str, Any] = {}
        if transcription_id:
            body["transcription_id"] = transcription_id
        return await self._post("/api/conversations/", json=body)

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """List conversations (paginated)."""
        return await self._get(
            "/api/conversations/",
            params={"limit": limit, "offset": offset},
        )

    async def get(self, conversation_id: str) -> dict[str, Any]:
        """Get a conversation with its full message history."""
        return await self._get(f"/api/conversations/{conversation_id}")

    async def delete(self, conversation_id: str) -> None:
        """Delete a conversation and all its messages."""
        await self._delete(f"/api/conversations/{conversation_id}")

    async def send_message(
        self,
        conversation_id: str,
        content: str,
    ) -> dict[str, Any]:
        """Send a message and receive the AI response."""
        return await self._post(
            f"/api/conversations/{conversation_id}/messages",
            json={"content": content},
        )
