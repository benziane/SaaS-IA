"""AI Chatbot Builder API — RAG chatbots with embed widget deployment."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class ChatbotAPI(BaseAPI):
    """Wraps ``/api/chatbots`` endpoints."""

    # -- CRUD ---------------------------------------------------------------

    async def create(
        self,
        name: str,
        *,
        system_prompt: str | None = None,
        model_provider: str | None = None,
        knowledge_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a chatbot."""
        body: dict[str, Any] = {"name": name}
        if system_prompt:
            body["system_prompt"] = system_prompt
        if model_provider:
            body["model_provider"] = model_provider
        if knowledge_ids:
            body["knowledge_ids"] = knowledge_ids
        return await self._post("/api/chatbots", json=body)

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List chatbots."""
        return await self._get(
            "/api/chatbots",
            params={"limit": limit, "offset": offset},
        )

    async def get(self, chatbot_id: str) -> dict[str, Any]:
        """Get chatbot details."""
        return await self._get(f"/api/chatbots/{chatbot_id}")

    async def update(
        self,
        chatbot_id: str,
        *,
        name: str | None = None,
        system_prompt: str | None = None,
        model_provider: str | None = None,
        knowledge_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update chatbot settings."""
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if system_prompt is not None:
            body["system_prompt"] = system_prompt
        if model_provider is not None:
            body["model_provider"] = model_provider
        if knowledge_ids is not None:
            body["knowledge_ids"] = knowledge_ids
        return await self._put(f"/api/chatbots/{chatbot_id}", json=body)

    async def delete(self, chatbot_id: str) -> None:
        """Soft-delete a chatbot."""
        await self._delete(f"/api/chatbots/{chatbot_id}")

    # -- Publishing ---------------------------------------------------------

    async def publish(self, chatbot_id: str) -> dict[str, Any]:
        """Publish chatbot and generate an embed token."""
        return await self._post(f"/api/chatbots/{chatbot_id}/publish")

    async def unpublish(self, chatbot_id: str) -> None:
        """Unpublish chatbot and revoke embed token."""
        await self._post(f"/api/chatbots/{chatbot_id}/unpublish")

    # -- Channels -----------------------------------------------------------

    async def add_channel(
        self,
        chatbot_id: str,
        channel_type: str,
        *,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a deployment channel."""
        body: dict[str, Any] = {"type": channel_type}
        if config:
            body["config"] = config
        return await self._post(
            f"/api/chatbots/{chatbot_id}/channels",
            json=body,
        )

    async def remove_channel(
        self, chatbot_id: str, channel_type: str
    ) -> None:
        """Remove a deployment channel."""
        await self._delete(f"/api/chatbots/{chatbot_id}/channels/{channel_type}")

    # -- Analytics ----------------------------------------------------------

    async def analytics(self, chatbot_id: str) -> dict[str, Any]:
        """Get chatbot analytics."""
        return await self._get(f"/api/chatbots/{chatbot_id}/analytics")

    async def embed_code(self, chatbot_id: str) -> dict[str, Any]:
        """Get embed HTML/JS snippet."""
        return await self._get(f"/api/chatbots/{chatbot_id}/embed-code")

    # -- Public widget (no auth) --------------------------------------------

    async def widget_chat(
        self,
        token: str,
        message: str,
        *,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Chat with a published chatbot via its embed token."""
        body: dict[str, Any] = {"message": message}
        if session_id:
            body["session_id"] = session_id
        return await self._post(f"/api/chatbots/widget/{token}/chat", json=body)

    async def widget_history(
        self, token: str, session_id: str
    ) -> list[dict[str, Any]]:
        """Get chat history for a widget session."""
        return await self._get(
            f"/api/chatbots/widget/{token}/history/{session_id}"
        )

    async def widget_config(self, token: str) -> dict[str, Any]:
        """Get widget configuration."""
        return await self._get(f"/api/chatbots/widget/{token}/config")
