"""Sentiment API — text sentiment analysis (RoBERTa + LLM)."""

from __future__ import annotations

from typing import Any

from saas_ia.api.base import BaseAPI


class SentimentAPI(BaseAPI):
    """Wraps ``/api/sentiment`` endpoints."""

    async def analyze(self, text: str) -> dict[str, Any]:
        """Analyze text sentiment and emotions."""
        return await self._post("/api/sentiment/analyze", json={"text": text})

    async def analyze_transcription(
        self, transcription_id: str
    ) -> dict[str, Any]:
        """Analyze sentiment of a transcription."""
        return await self._post(
            "/api/sentiment/transcription",
            json={"transcription_id": transcription_id},
        )
