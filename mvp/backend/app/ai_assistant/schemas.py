"""Pydantic schemas for AI Assistant - Grade S++"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class TextProcessingRequest(BaseModel):
    """
    Request schema for text processing (correction, formatting, etc.).
    
    Attributes:
        text: Text to process
        task: Type of processing task
        provider: AI provider to use
        language: Language of the text
    """
    
    text: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Text to process"
    )
    task: Literal[
        "correct_spelling",
        "add_punctuation",
        "format_paragraphs",
        "improve_quality",
        "format_text",
        "translate"
    ] = Field(
        default="improve_quality",
        description="Processing task"
    )
    provider: Literal["gemini", "claude", "groq"] = Field(
        default="gemini",
        description="AI provider to use"
    )
    language: Optional[str] = Field(
        default=None,
        description="Language code (e.g., 'fr', 'en')"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "L IND plus grand tresor que lettres humain...",
                    "task": "improve_quality",
                    "provider": "gemini",
                    "language": "fr"
                }
            ]
        }
    }


class TextProcessingResponse(BaseModel):
    """
    Response schema for text processing.
    
    Attributes:
        original_text: Original input text
        processed_text: Processed output text
        provider_used: AI provider that was used
        task_performed: Task that was performed
        improvements: List of improvements made
    """
    
    original_text: str
    processed_text: str
    provider_used: str
    task_performed: str
    improvements: list[str] = Field(default_factory=list)


class ProviderInfo(BaseModel):
    """
    Provider information schema.
    
    Attributes:
        name: Provider identifier
        display_name: Human-readable provider name
        available: Whether provider is available
        is_free: Whether provider is free
        cost_tier: Cost tier (free, low, medium, high)
        cost_label: Visual label (FREE 🆓 or PAID 💰)
        model_name: Model name
        priority: Priority order (1=highest)
    """
    
    name: str = Field(..., description="Provider identifier")
    display_name: str = Field(..., description="Display name")
    available: bool = Field(default=True, description="Availability status")
    is_free: bool = Field(default=True, description="Free or paid")
    cost_tier: str = Field(default="free", description="Cost tier")
    cost_label: str = Field(default="FREE 🆓", description="Visual cost label")
    model_name: str = Field(default="", description="Model name")
    priority: int = Field(default=999, description="Priority (1=highest)")


class ProviderConfigUpdate(BaseModel):
    """
    Schema for updating provider configuration.
    
    Attributes:
        enabled: Enable/disable provider
        max_tokens: Maximum tokens per request
        temperature: Temperature for generation
    """
    
    enabled: Optional[bool] = None
    max_tokens: Optional[int] = Field(None, ge=100, le=10000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)

