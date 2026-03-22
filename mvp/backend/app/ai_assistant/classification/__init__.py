"""
AI Assistant Classification Module - Grade S++

This module provides intelligent content classification and model selection
for optimal AI processing across all SaaS modules.

Components:
- ContentClassifier: Analyzes content domain, tone, and sensitivity
- ModelSelector: Selects optimal AI model based on classification
- PromptSelector: Configures appropriate prompt for the task
- ConfigLoader: Loads and caches YAML configuration

Usage:
    from app.ai_assistant.classification import ContentClassifier, ModelSelector
    
    classification = ContentClassifier.classify(text, language="french")
    selection = ModelSelector.select_model(classification)
"""

from app.ai_assistant.classification.enums import (
    ContentDomain,
    ContentTone,
    SensitivityLevel,
    AIModel,
    SelectionStrategy,
    PromptProfile
)

__all__ = [
    "ContentDomain",
    "ContentTone",
    "SensitivityLevel",
    "AIModel",
    "SelectionStrategy",
    "PromptProfile"
]

