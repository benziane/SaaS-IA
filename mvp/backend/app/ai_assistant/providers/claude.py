"""Anthropic Claude AI Provider - Grade S++"""

import asyncio

import structlog
from typing import AsyncGenerator
import httpx
from anthropic import AsyncAnthropic

from app.ai_assistant.providers.base import BaseAIProvider
from app.ai_assistant.retry import is_transient, MAX_RETRIES, BACKOFF_SECONDS
from app.config import settings

logger = structlog.get_logger(__name__)


class ClaudeProvider(BaseAIProvider):
    """
    Anthropic Claude AI Provider.
    
    Uses Anthropic's API for chat completions with streaming support.
    Paid service with high quality responses.
    """
    
    def __init__(self):
        """Initialize Claude provider with API key from settings."""
        if not settings.CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY not configured")
        
        self.client = AsyncAnthropic(
            api_key=settings.CLAUDE_API_KEY,
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
        logger.info("claude_provider_initialized", model="claude-3-5-sonnet-20241022")
    
    @property
    def name(self) -> str:
        """Get provider name."""
        return "claude"
    
    @property
    def is_free(self) -> bool:
        """Check if provider is free."""
        return False
    
    @property
    def cost_tier(self) -> str:
        """Get cost tier."""
        return "high"  # Claude est cher
    
    @property
    def model_name(self) -> str:
        """Get model name."""
        return "claude-3-5-sonnet-20241022"
    
    async def stream_chat(
        self,
        message: str,
        conversation_history: list[dict[str, str]] | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from Claude.
        
        Args:
            message: User message
            conversation_history: Optional conversation history
            
        Yields:
            str: Response chunks
            
        Raises:
            Exception: If Claude API call fails
        """
        logger.info(
            "claude_stream_started",
            message_length=len(message),
            has_history=conversation_history is not None
        )

        # Build messages array
        messages = []
        if conversation_history:
            messages.extend(conversation_history[-5:])  # Last 5 messages
        messages.append({"role": "user", "content": message})

        # Stream response with retry on transient errors
        last_exc = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with self.client.messages.stream(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    messages=messages
                ) as stream:
                    chunk_count = 0
                    async for text in stream.text_stream:
                        chunk_count += 1
                        yield text

                logger.info(
                    "claude_stream_completed",
                    chunk_count=chunk_count
                )
                return
            except httpx.TimeoutException:
                last_exc = TimeoutError("AI provider timed out after 60s")
                if attempt == MAX_RETRIES or not is_transient(last_exc):
                    raise last_exc
            except Exception as e:
                last_exc = e
                if attempt == MAX_RETRIES or not is_transient(e):
                    logger.error(
                        "claude_stream_error",
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    raise

            delay = BACKOFF_SECONDS[attempt - 1]
            logger.warning(
                "provider_retry",
                provider="claude",
                attempt=attempt,
                delay=delay,
                error=str(last_exc),
            )
            await asyncio.sleep(delay)

