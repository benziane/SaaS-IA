"""
Model Selector for AI Router - Grade S++

Selects optimal AI model based on content classification.
Supports multiple strategies and automatic fallback.
"""

from typing import Dict, List, Optional
import structlog

from app.ai_assistant.classification.enums import (
    AIModel,
    SelectionStrategy,
    SensitivityLevel
)
from app.ai_assistant.classification.config_loader import ConfigLoader

logger = structlog.get_logger()


class ModelSelector:
    """
    Selects optimal AI model based on content classification.
    
    Features:
    - Multiple selection strategies (conservative, balanced, cost_optimized)
    - Automatic fallback when model unavailable
    - Sensitivity-aware selection
    - Confidence-based strategy adjustment
    
    Usage:
        selection = ModelSelector.select_model(
            classification=classification_result,
            strategy=SelectionStrategy.BALANCED
        )
    """
    
    @classmethod
    def select_model(
        cls,
        classification: Dict,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED,
        available_models: Optional[List[str]] = None,
        override: Optional[str] = None
    ) -> Dict:
        """
        Select optimal model based on classification and strategy.
        
        Args:
            classification: Output from ContentClassifier.classify()
            strategy: Selection strategy to use
            available_models: List of currently available models (None = all)
            override: Manual model override (bypasses selection logic)
        
        Returns:
            {
                "model": "groq",
                "strategy_used": "balanced",
                "fallback_used": False,
                "reason": "Primary model for religious content",
                "alternatives": ["gpt-4", "claude-3"],
                "confidence_adjustment": False
            }
        """
        # Manual override
        if override:
            logger.info(
                "model_selection_override",
                model=override,
                reason="Manual override by user"
            )
            return {
                "model": override,
                "strategy_used": "manual_override",
                "fallback_used": False,
                "reason": "Manual override by user",
                "alternatives": [],
                "confidence_adjustment": False
            }
        
        # Extract classification info
        primary_domain = classification["primary_domain"]
        confidence = classification["confidence"]
        sensitivity_level = classification["sensitivity"]["level"]
        is_mixed = classification["is_mixed_content"]
        
        # Adjust strategy based on confidence and sensitivity
        original_strategy = strategy
        strategy, confidence_adjusted = cls._adjust_strategy(
            strategy=strategy,
            confidence=confidence,
            sensitivity_level=sensitivity_level
        )
        
        # Get candidate models for this domain and strategy
        candidates = cls._get_candidate_models(primary_domain, strategy)
        
        # Filter by availability
        if available_models:
            available_candidates = [m for m in candidates if m in available_models]
            if not available_candidates:
                logger.warning(
                    "no_available_models_for_strategy",
                    strategy=strategy,
                    domain=primary_domain,
                    requested_models=candidates,
                    available_models=available_models
                )
                # Fallback to any available model
                available_candidates = available_models
            candidates = available_candidates
        
        # Select first available model
        if not candidates:
            # Ultimate fallback
            selected = AIModel.GEMINI_FLASH
            fallback_used = True
            logger.warning(
                "ultimate_fallback_model_used",
                model=selected,
                domain=primary_domain
            )
        else:
            selected = candidates[0]
            fallback_used = (len(candidates) > 1 and strategy != original_strategy)
        
        # Generate selection reason
        reason = cls._generate_selection_reason(
            domain=primary_domain,
            model=selected,
            sensitivity=sensitivity_level,
            is_mixed=is_mixed,
            strategy=strategy
        )
        
        result = {
            "model": selected,
            "strategy_used": strategy,
            "fallback_used": fallback_used,
            "reason": reason,
            "alternatives": candidates[1:3] if len(candidates) > 1 else [],
            "confidence_adjustment": confidence_adjusted
        }
        
        # Log selection
        if ConfigLoader.load_config().get("logging", {}).get("log_model_selections", True):
            logger.info(
                "model_selected",
                model=selected,
                strategy=strategy,
                domain=primary_domain,
                sensitivity=sensitivity_level,
                confidence=confidence,
                fallback=fallback_used
            )
        
        return result
    
    @classmethod
    def _adjust_strategy(
        cls,
        strategy: SelectionStrategy,
        confidence: float,
        sensitivity_level: str
    ) -> tuple[SelectionStrategy, bool]:
        """
        Adjust strategy based on confidence and sensitivity.
        
        Returns:
            (adjusted_strategy, was_adjusted)
        """
        original_strategy = strategy
        adjusted = False
        
        # Get confidence thresholds
        thresholds = ConfigLoader.get_confidence_thresholds()
        
        # Force conservative for high/critical sensitivity
        if sensitivity_level in [SensitivityLevel.HIGH, SensitivityLevel.CRITICAL]:
            if strategy != SelectionStrategy.CONSERVATIVE:
                strategy = SelectionStrategy.CONSERVATIVE
                adjusted = True
                logger.info(
                    "strategy_adjusted_for_sensitivity",
                    from_strategy=original_strategy,
                    to_strategy=strategy,
                    sensitivity=sensitivity_level
                )
        
        # Force conservative for low confidence
        elif confidence < thresholds.get("low", 0.2):
            if strategy != SelectionStrategy.CONSERVATIVE:
                strategy = SelectionStrategy.CONSERVATIVE
                adjusted = True
                logger.info(
                    "strategy_adjusted_for_confidence",
                    from_strategy=original_strategy,
                    to_strategy=strategy,
                    confidence=confidence
                )
        
        return strategy, adjusted
    
    @classmethod
    def _get_candidate_models(
        cls,
        domain: str,
        strategy: SelectionStrategy
    ) -> List[str]:
        """
        Get candidate models for domain and strategy.
        
        Returns:
            List of model names in priority order
        """
        strategy_config = ConfigLoader.get_strategy_config(strategy)
        
        # Get models for this domain
        candidates = strategy_config.get(domain, [])
        
        # Fallback to general if domain not found
        if not candidates:
            candidates = strategy_config.get("general", [AIModel.GEMINI_FLASH])
        
        return candidates
    
    @classmethod
    def _generate_selection_reason(
        cls,
        domain: str,
        model: str,
        sensitivity: str,
        is_mixed: bool,
        strategy: SelectionStrategy
    ) -> str:
        """
        Generate human-readable selection reason.
        
        Returns:
            Reason string
        """
        if sensitivity in [SensitivityLevel.HIGH, SensitivityLevel.CRITICAL]:
            return f"Conservative model for sensitive {domain} content"
        
        if is_mixed:
            return f"Balanced model for mixed content ({domain})"
        
        if strategy == SelectionStrategy.COST_OPTIMIZED:
            return f"Cost-optimized model for {domain} content"
        
        if strategy == SelectionStrategy.CONSERVATIVE:
            return f"High-quality model for {domain} content"
        
        return f"Optimal model for {domain} content"
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """
        Get list of all configured models across all strategies.
        
        Returns:
            List of unique model names
        """
        return ConfigLoader.get_all_models()
    
    @classmethod
    def get_strategy_for_domain(
        cls,
        domain: str,
        strategy: SelectionStrategy = SelectionStrategy.BALANCED
    ) -> List[str]:
        """
        Get recommended models for a specific domain and strategy.
        
        Args:
            domain: Domain name
            strategy: Selection strategy
        
        Returns:
            List of recommended models in priority order
        """
        return cls._get_candidate_models(domain, strategy)
    
    @classmethod
    def compare_strategies(
        cls,
        classification: Dict
    ) -> Dict[str, Dict]:
        """
        Compare what each strategy would select for given classification.
        Useful for debugging and analysis.
        
        Args:
            classification: Classification result
        
        Returns:
            Dictionary mapping strategy names to selection results
        """
        results = {}
        
        for strategy in [
            SelectionStrategy.CONSERVATIVE,
            SelectionStrategy.BALANCED,
            SelectionStrategy.COST_OPTIMIZED
        ]:
            results[strategy] = cls.select_model(
                classification=classification,
                strategy=strategy
            )
        
        return results

