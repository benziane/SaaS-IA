"""Base AI Provider interface - Grade S++"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseAIProvider(ABC):
    """
    Base class for AI providers.
    
    All AI providers must implement this interface to ensure consistency
    across different AI services (Gemini, Claude, Groq, etc.).
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get provider name.
        
        Returns:
            str: Provider identifier (e.g., "gemini", "claude", "groq")
        """
        pass
    
    @property
    @abstractmethod
    def is_free(self) -> bool:
        """
        Check if provider is free to use.
        
        Returns:
            bool: True if free, False if paid
        """
        pass
    
    @property
    @abstractmethod
    def cost_tier(self) -> str:
        """
        Get cost tier of provider.
        
        Returns:
            str: "free", "low", "medium", "high"
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Get model name used by provider.
        
        Returns:
            str: Model identifier (e.g., "gemini-2.5-flash", "claude-3-5-sonnet")
        """
        pass
    
    @abstractmethod
    async def stream_chat(
        self,
        message: str,
        conversation_history: list[dict[str, str]] | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from AI provider.
        
        Args:
            message: User message to send to AI
            conversation_history: Optional conversation history
                Format: [{"role": "user", "content": "..."}, ...]
        
        Yields:
            str: Response chunks as they arrive
            
        Raises:
            Exception: If provider API call fails
        """
        pass
    
    async def complete(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """
        Get a complete response (non-streaming).
        
        Args:
            prompt: The prompt to send to the AI
            max_tokens: Maximum tokens in response
            temperature: Creativity level (0.0-1.0)
        
        Returns:
            str: Complete response text
        """
        # Default implementation: collect all chunks
        chunks = []
        async for chunk in self.stream_chat(prompt):
            chunks.append(chunk)
        return "".join(chunks)

