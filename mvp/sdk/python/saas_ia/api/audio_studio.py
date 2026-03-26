"""Audio Studio API — audio editing (pydub + noisereduce) stub."""

from __future__ import annotations

from typing import Any, BinaryIO

from saas_ia.api.base import BaseAPI


class AudioStudioAPI(BaseAPI):
    """Wraps ``/api/audio`` endpoints."""

    async def upload(
        self,
        file: BinaryIO,
        filename: str = "audio.wav",
    ) -> dict[str, Any]:
        """Upload an audio file for processing."""
        return await self._post(
            "/api/audio/upload",
            files={"file": (filename, file)},
        )

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List processed audio files."""
        return await self._get(
            "/api/audio/",
            params={"limit": limit, "offset": offset},
        )

    async def get(self, audio_id: str) -> dict[str, Any]:
        """Get audio result."""
        return await self._get(f"/api/audio/{audio_id}")

    async def delete(self, audio_id: str) -> None:
        """Delete an audio file."""
        await self._delete(f"/api/audio/{audio_id}")
