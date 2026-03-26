"""Transcription API — YouTube / audio / video transcription with speaker
diarization, chaptering, export, batch processing, and live-stream capture."""

from __future__ import annotations

from typing import Any, BinaryIO

from saas_ia.api.base import BaseAPI


class TranscriptionAPI(BaseAPI):
    """Wraps ``/api/transcription`` endpoints."""

    # -- CRUD ---------------------------------------------------------------

    async def create(
        self,
        source_url: str,
        *,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Create a transcription job from a URL."""
        body: dict[str, Any] = {"source_url": source_url}
        if language:
            body["language"] = language
        return await self._post("/api/transcription/", json=body)

    async def upload(
        self,
        file: BinaryIO,
        filename: str = "upload",
        *,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Upload an audio/video file for transcription."""
        files = {"file": (filename, file)}
        data = {"language": language} if language else None
        return await self._post("/api/transcription/upload", data=data, files=files)

    async def list(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """List transcriptions (paginated)."""
        return await self._get(
            "/api/transcription/",
            params={"limit": limit, "offset": offset},
        )

    async def get(self, job_id: str) -> dict[str, Any]:
        """Get transcription by ID."""
        return await self._get(f"/api/transcription/{job_id}")

    async def delete(self, job_id: str) -> None:
        """Delete a transcription."""
        await self._delete(f"/api/transcription/{job_id}")

    async def stats(self) -> dict[str, Any]:
        """Get transcription statistics."""
        return await self._get("/api/transcription/stats")

    # -- Speaker diarization ------------------------------------------------

    async def speakers(self, job_id: str) -> dict[str, Any]:
        """Get transcription with speaker diarization."""
        return await self._get(f"/api/transcription/{job_id}/speakers")

    # -- Smart transcription ------------------------------------------------

    async def smart_transcribe(
        self,
        source_url: str,
        *,
        language: str | None = None,
        enable_diarization: bool = False,
    ) -> dict[str, Any]:
        """Smart transcription with automatic provider routing."""
        body: dict[str, Any] = {"source_url": source_url}
        if language:
            body["language"] = language
        if enable_diarization:
            body["enable_diarization"] = True
        return await self._post("/api/transcription/smart-transcribe", json=body)

    # -- Chaptering & summary -----------------------------------------------

    async def chapters(self, job_id: str) -> dict[str, Any]:
        """Auto-generate chapters with summaries."""
        return await self._post(
            "/api/transcription/auto-chapter",
            json={"transcription_id": job_id},
        )

    async def summary(
        self,
        job_id: str,
        *,
        style: str | None = None,
    ) -> dict[str, Any]:
        """Generate a summary of a transcription."""
        body: dict[str, Any] = {}
        if style:
            body["style"] = style
        return await self._post(f"/api/transcription/{job_id}/summary", json=body)

    async def keywords(self, job_id: str) -> list[dict[str, Any]]:
        """Extract keywords from a transcription."""
        return await self._get(f"/api/transcription/{job_id}/keywords")

    # -- Export -------------------------------------------------------------

    async def export(
        self,
        job_id: str,
        format: str = "txt",
    ) -> str:
        """Export transcription in the given format (srt, vtt, txt, md, json)."""
        return await self._get(
            f"/api/transcription/{job_id}/export",
            params={"format": format},
        )

    # -- Batch --------------------------------------------------------------

    async def batch(self, urls: list[str]) -> dict[str, Any]:
        """Submit batch transcription jobs."""
        return await self._post("/api/transcription/batch", json={"urls": urls})

    # -- Metadata -----------------------------------------------------------

    async def metadata(self, url: str) -> dict[str, Any]:
        """Extract YouTube video metadata."""
        return await self._post("/api/transcription/metadata", json={"url": url})

    # -- Playlist -----------------------------------------------------------

    async def playlist(
        self,
        playlist_url: str,
        *,
        language: str | None = None,
        max_videos: int | None = None,
    ) -> dict[str, Any]:
        """Transcribe an entire YouTube playlist."""
        body: dict[str, Any] = {"playlist_url": playlist_url}
        if language:
            body["language"] = language
        if max_videos:
            body["max_videos"] = max_videos
        return await self._post("/api/transcription/playlist", json=body)

    # -- Live stream --------------------------------------------------------

    async def stream_status(self, url: str) -> dict[str, Any]:
        """Check if a live stream is active."""
        return await self._post(
            "/api/transcription/stream/status",
            json={"url": url},
        )

    async def stream_capture(
        self,
        url: str,
        *,
        duration_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Capture a segment of a live stream."""
        body: dict[str, Any] = {"url": url}
        if duration_seconds:
            body["duration_seconds"] = duration_seconds
        return await self._post("/api/transcription/stream/capture", json=body)

    # -- Video analysis -----------------------------------------------------

    async def analyze_video(
        self,
        source_url: str,
        *,
        interval_seconds: int | None = None,
        max_frames: int | None = None,
    ) -> dict[str, Any]:
        """Analyze video frames with Vision AI."""
        body: dict[str, Any] = {"source_url": source_url}
        if interval_seconds:
            body["interval_seconds"] = interval_seconds
        if max_frames:
            body["max_frames"] = max_frames
        return await self._post("/api/transcription/video/analyze", json=body)

    # -- Search -------------------------------------------------------------

    async def search(
        self,
        query: str,
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search across all transcriptions."""
        return await self._get(
            "/api/transcription/search",
            params={"query": query, "limit": limit},
        )
