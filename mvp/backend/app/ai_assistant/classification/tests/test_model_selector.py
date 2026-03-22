"""
Unit Tests for ModelSelector - Grade S++

Tests model selection logic, strategies, and fallback mechanisms.
"""

import pytest
from app.ai_assistant.classification.model_selector import ModelSelector
from app.ai_assistant.classification.content_classifier import ContentClassifier
from app.ai_assistant.classification.enums import SelectionStrategy, SensitivityLevel


class TestModelSelector:
    """Test suite for ModelSelector"""
    
    def test_select_model_for_religious_content(self):
        """Test model selection for religious content (should use conservative)"""
        classification = {
            "primary_domain": "religious",
            "confidence": 0.85,
            "sensitivity": {
                "level": SensitivityLevel.HIGH,
                "requires_strict_mode": True,
                "reasons": ["religious_content"]
            },
            "is_mixed_content": False
        }
        
        result = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED
        )
        
        # Should force conservative for high sensitivity
        assert result["strategy_used"] == SelectionStrategy.CONSERVATIVE
        assert result["confidence_adjustment"] is True
        assert result["model"] in ["groq", "gpt-4", "claude-3-opus"]
    
    def test_select_model_balanced_strategy(self):
        """Test balanced strategy for general content"""
        classification = {
            "primary_domain": "general",
            "confidence": 0.75,
            "sensitivity": {
                "level": SensitivityLevel.LOW,
                "requires_strict_mode": False,
                "reasons": []
            },
            "is_mixed_content": False
        }
        
        result = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED
        )
        
        assert result["strategy_used"] == SelectionStrategy.BALANCED
        assert result["confidence_adjustment"] is False
        assert result["model"] in ["gemini-flash", "groq"]
    
    def test_select_model_cost_optimized(self):
        """Test cost-optimized strategy"""
        classification = {
            "primary_domain": "narrative",
            "confidence": 0.80,
            "sensitivity": {
                "level": SensitivityLevel.LOW,
                "requires_strict_mode": False,
                "reasons": []
            },
            "is_mixed_content": False
        }
        
        result = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.COST_OPTIMIZED
        )
        
        assert result["strategy_used"] == SelectionStrategy.COST_OPTIMIZED
        # Should prefer free models
        assert result["model"] in ["gemini-flash", "groq"]
    
    def test_manual_override(self):
        """Test manual model override"""
        classification = {
            "primary_domain": "religious",
            "confidence": 0.85,
            "sensitivity": {
                "level": SensitivityLevel.HIGH,
                "requires_strict_mode": True,
                "reasons": []
            },
            "is_mixed_content": False
        }
        
        result = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED,
            override="claude"
        )
        
        assert result["model"] == "claude"
        assert result["strategy_used"] == "manual_override"
        assert result["fallback_used"] is False
    
    def test_low_confidence_forces_conservative(self):
        """Test that low confidence forces conservative strategy"""
        classification = {
            "primary_domain": "general",
            "confidence": 0.15,  # Very low
            "sensitivity": {
                "level": SensitivityLevel.LOW,
                "requires_strict_mode": False,
                "reasons": []
            },
            "is_mixed_content": False
        }
        
        result = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.COST_OPTIMIZED
        )
        
        # Should force conservative due to low confidence
        assert result["strategy_used"] == SelectionStrategy.CONSERVATIVE
        assert result["confidence_adjustment"] is True
    
    def test_compare_strategies(self):
        """Test strategy comparison"""
        classification = {
            "primary_domain": "scientific",
            "confidence": 0.75,
            "sensitivity": {
                "level": SensitivityLevel.MEDIUM,
                "requires_strict_mode": False,
                "reasons": []
            },
            "is_mixed_content": False
        }
        
        comparison = ModelSelector.compare_strategies(classification)
        
        assert SelectionStrategy.CONSERVATIVE in comparison
        assert SelectionStrategy.BALANCED in comparison
        assert SelectionStrategy.COST_OPTIMIZED in comparison
        
        # Each should have a model selected
        for strategy, result in comparison.items():
            assert "model" in result
            assert result["model"] is not None
    
    def test_get_available_models(self):
        """Test getting list of available models"""
        models = ModelSelector.get_available_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert "groq" in models or "gemini-flash" in models
    
    def test_get_strategy_for_domain(self):
        """Test getting strategy for specific domain"""
        models = ModelSelector.get_strategy_for_domain(
            domain="religious",
            strategy=SelectionStrategy.CONSERVATIVE
        )
        
        assert isinstance(models, list)
        assert len(models) > 0
    
    def test_mixed_content_selection(self):
        """Test model selection for mixed content"""
        classification = {
            "primary_domain": "religious",
            "secondary_domain": "scientific",
            "confidence": 0.70,
            "sensitivity": {
                "level": SensitivityLevel.MEDIUM,
                "requires_strict_mode": False,
                "reasons": ["mixed_sensitive_content"]
            },
            "is_mixed_content": True
        }
        
        result = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED
        )
        
        assert "mixed" in result["reason"].lower() or "religious" in result["reason"].lower()
    
    def test_selection_reason_generation(self):
        """Test that selection reasons are meaningful"""
        classification = {
            "primary_domain": "technical",
            "confidence": 0.80,
            "sensitivity": {
                "level": SensitivityLevel.LOW,
                "requires_strict_mode": False,
                "reasons": []
            },
            "is_mixed_content": False
        }
        
        result = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED
        )
        
        assert len(result["reason"]) > 10  # Should have meaningful reason
        assert "technical" in result["reason"].lower()
    
    def test_fallback_mechanism(self):
        """Test fallback when preferred model unavailable"""
        classification = {
            "primary_domain": "general",
            "confidence": 0.75,
            "sensitivity": {
                "level": SensitivityLevel.LOW,
                "requires_strict_mode": False,
                "reasons": []
            },
            "is_mixed_content": False
        }
        
        # Simulate limited availability
        result = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED,
            available_models=["groq"]  # Only groq available
        )
        
        assert result["model"] == "groq"
    
    def test_critical_sensitivity_selection(self):
        """Test selection for critical sensitivity content"""
        classification = {
            "primary_domain": "medical",
            "confidence": 0.85,
            "sensitivity": {
                "level": SensitivityLevel.CRITICAL,
                "requires_strict_mode": True,
                "reasons": ["medical_content", "high_sensitivity_keywords"]
            },
            "is_mixed_content": False
        }
        
        result = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.COST_OPTIMIZED
        )
        
        # Should force conservative even with cost_optimized
        assert result["strategy_used"] == SelectionStrategy.CONSERVATIVE
        assert result["confidence_adjustment"] is True

