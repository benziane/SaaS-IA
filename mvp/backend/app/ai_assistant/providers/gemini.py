"""Google Gemini AI Provider"""

import structlog
from typing import AsyncGenerator
import google.generativeai as genai

from app.ai_assistant.providers.base import BaseAIProvider
from app.config import settings

logger = structlog.get_logger(__name__)


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini AI Provider.

    Uses Google's Generative AI API for chat completions with streaming support.
    Requires GEMINI_API_KEY to be set in environment or .env file.
    """

    def __init__(self):
        """Initialize Gemini provider with API key from settings."""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured. "
                "Set it in your .env file or environment variables."
            )

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("gemini_provider_initialized", model="gemini-2.5-flash")

    @property
    def name(self) -> str:
        """Get provider name."""
        return "gemini"

    @property
    def is_free(self) -> bool:
        """Check if provider is free."""
        return True

    @property
    def cost_tier(self) -> str:
        """Get cost tier."""
        return "free"

    @property
    def model_name(self) -> str:
        """Get model name."""
        return "gemini-2.5-flash"

    async def stream_chat(
        self,
        message: str,
        conversation_history: list[dict[str, str]] | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from Gemini.

        Args:
            message: User message
            conversation_history: Optional conversation history

        Yields:
            str: Response chunks
        """
        prompt = message
        if conversation_history:
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-5:]
            ])
            prompt = f"{history_text}\nuser: {message}"

        logger.info(
            "gemini_stream_started",
            message_length=len(message),
            has_history=conversation_history is not None
        )

        response = await self.model.generate_content_async(
            prompt,
            stream=True
        )

        chunk_count = 0
        async for chunk in response:
            if chunk.text:
                chunk_count += 1
                yield chunk.text

        logger.info("gemini_stream_completed", chunk_count=chunk_count)
