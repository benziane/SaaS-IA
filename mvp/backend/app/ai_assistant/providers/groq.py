"""Groq AI Provider - Grade S++"""

import structlog
from typing import AsyncGenerator
from openai import AsyncOpenAI

from app.ai_assistant.providers.base import BaseAIProvider
from app.config import settings

logger = structlog.get_logger(__name__)


class GroqProvider(BaseAIProvider):
    """
    Groq AI Provider.
    
    Uses Groq's ultra-fast inference API with Llama models.
    Free tier available with excellent performance.
    """
    
    def __init__(self):
        """Initialize Groq provider with API key from settings."""
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured")
        
        self.client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        logger.info("groq_provider_initialized", model="llama-3.3-70b-versatile")
    
    @property
    def name(self) -> str:
        """Get provider name."""
        return "groq"
    
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
        return "llama-3.3-70b-versatile"
    
    async def stream_chat(
        self,
        message: str,
        conversation_history: list[dict[str, str]] | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from Groq.
        
        Args:
            message: User message
            conversation_history: Optional conversation history
            
        Yields:
            str: Response chunks
            
        Raises:
            Exception: If Groq API call fails
        """
        try:
            logger.info(
                "groq_stream_started",
                message_length=len(message),
                has_history=conversation_history is not None
            )
            
            # Build messages array
            messages = []
            if conversation_history:
                messages.extend(conversation_history[-5:])  # Last 5 messages
            messages.append({"role": "user", "content": message})
            
            # Stream response
            stream = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                stream=True,
                max_tokens=2000,
                temperature=0.7
            )
            
            chunk_count = 0
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    chunk_count += 1
                    yield chunk.choices[0].delta.content
            
            logger.info(
                "groq_stream_completed",
                chunk_count=chunk_count
            )
            
        except Exception as e:
            logger.error(
                "groq_stream_error",
                error=str(e),
                error_type=type(e).__name__
            )
            raise

