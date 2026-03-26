"""Video Gen API — text-to-video generation (6 types) + ffmpeg."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class VideoGenAPI(BaseAPI):
    """Wraps ``/api/videos`` endpoints."""

    async def generate(
        self,
        prompt: str,
        *,
        video_type: str | None = None,
        duration_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Generate a video from a text prompt."""
        body: dict[str, Any] = {"prompt": prompt}
        if video_type:
            body["video_type"] = video_type
        if duration_seconds:
            body["duration_seconds"] = duration_seconds
        return await self._post("/api/videos/generate", json=body)

    async def clips(
        self,
        transcription_id: str,
        *,
        max_clips: int | None = None,
    ) -> list[dict[str, Any]]:
        """Generate highlight clips from a transcription."""
        body: dict[str, Any] = {"transcription_id": transcription_id}
        if max_clips:
            body["max_clips"] = max_clips
        return await self._post("/api/videos/clips", json=body)

    async def avatar(
        self,
        text: str,
        *,
        avatar_style: str | None = None,
    ) -> dict[str, Any]:
        """Generate a talking avatar video."""
        body: dict[str, Any] = {"text": text}
        if avatar_style:
            body["avatar_style"] = avatar_style
        return await self._post("/api/videos/avatar", json=body)

    async def from_source(
        self,
        source_id: str,
        source_type: str,
        *,
        video_type: str | None = None,
    ) -> dict[str, Any]:
        """Generate video from a transcription or document."""
        body: dict[str, Any] = {
            "source_id": source_id,
            "source_type": source_type,
        }
        if video_type:
            body["video_type"] = video_type
        return await self._post("/api/videos/from-source", json=body)

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List generated videos."""
        return await self._get(
            "/api/videos/",
            params={"limit": limit, "offset": offset},
        )

    async def delete(self, video_id: str) -> None:
        """Delete a video."""
        await self._delete(f"/api/videos/{video_id}")

    async def list_types(self) -> list[dict[str, Any]]:
        """List available video types."""
        return await self._get("/api/videos/types")
