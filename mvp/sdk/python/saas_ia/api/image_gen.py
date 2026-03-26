"""Image Gen API — AI image generation (10 styles) + Real-ESRGAN upscaling."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class ImageGenAPI(BaseAPI):
    """Wraps ``/api/images`` endpoints."""

    async def generate(
        self,
        prompt: str,
        *,
        style: str | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> dict[str, Any]:
        """Generate an image from a prompt."""
        body: dict[str, Any] = {"prompt": prompt}
        if style:
            body["style"] = style
        if width:
            body["width"] = width
        if height:
            body["height"] = height
        return await self._post("/api/images/generate", json=body)

    async def thumbnail(
        self,
        title: str,
        *,
        style: str | None = None,
        transcription_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate a YouTube thumbnail."""
        body: dict[str, Any] = {"title": title}
        if style:
            body["style"] = style
        if transcription_id:
            body["transcription_id"] = transcription_id
        return await self._post("/api/images/thumbnail", json=body)

    async def bulk(
        self,
        prompts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Bulk generate multiple images."""
        return await self._post("/api/images/bulk", json={"prompts": prompts})

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[dict[str, Any]]:
        """List generated images."""
        return await self._get(
            "/api/images/",
            params={"limit": limit, "offset": offset},
        )

    async def delete(self, image_id: str) -> None:
        """Delete an image."""
        await self._delete(f"/api/images/{image_id}")

    async def upscale(self, image_id: str) -> dict[str, Any]:
        """Upscale an image with Real-ESRGAN."""
        return await self._post(f"/api/images/{image_id}/upscale")

    async def list_styles(self) -> list[dict[str, Any]]:
        """List available image styles."""
        return await self._get("/api/images/styles")
