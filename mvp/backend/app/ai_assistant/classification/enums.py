"""
Enumerations for AI Classification System - Grade S++

Defines all enums used across the classification module.
"""

from enum import Enum


class ContentDomain(str, Enum):
    """
    Content domain classification.
    Determines the subject matter and context of the text.
    """
    RELIGIOUS = "religious"
    SCIENTIFIC = "scientific"
    TECHNICAL = "technical"
    ADMINISTRATIVE = "administrative"
    NARRATIVE = "narrative"
    MEDICAL = "medical"
    LEGAL = "legal"
    FINANCIAL = "financial"
    GENERAL = "general"


class ContentTone(str, Enum):
    """
    Content tone classification.
    Determines the style and formality level of the text.
    """
    POPULAR = "popular"              # Conversational, informal
    NEUTRAL = "neutral"              # Standard, informative
    ACADEMIC = "academic"            # Scholarly, referenced
    FORMAL = "formal"                # Official, institutional
    CONVERSATIONAL = "conversational"  # Friendly, engaging


class SensitivityLevel(str, Enum):
    """
    Content sensitivity level.
    Determines how carefully the content must be handled.
    """
    LOW = "low"          # General content, no special care needed
    MEDIUM = "medium"    # Some care needed
    HIGH = "high"        # Requires strict mode, careful handling
    CRITICAL = "critical"  # Maximum care, conservative approach


class AIModel(str, Enum):
    """
    Available AI models for processing.
    Maps to actual provider implementations.
    """
    GEMINI_FLASH = "gemini-flash"
    GEMINI_PRO = "gemini-pro"
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"
    CLAUDE_3 = "claude-3"
    CLAUDE_3_OPUS = "claude-3-opus"
    GROQ = "groq"


class SelectionStrategy(str, Enum):
    """
    Model selection strategy.
    Determines the trade-off between quality and cost.
    """
    CONSERVATIVE = "conservative"      # Maximum quality, higher cost
    BALANCED = "balanced"              # Balance quality/cost (default)
    COST_OPTIMIZED = "cost_optimized"  # Minimum cost


class PromptProfile(str, Enum):
    """
    Prompt profile for different content types.
    Determines which prompt template to use.
    """
    STRICT = "strict"              # STRICT MODE for sensitive content
    STANDARD = "standard"          # Normal prompt
    CREATIVE = "creative"          # More freedom for narrative
    TECHNICAL = "technical"        # Precision for technical content
    TRANSLATION = "translation"    # Translation-specific

