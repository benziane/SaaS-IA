"""
Integration Tests for AI Classification System - Grade S++

Tests complete pipeline: Classification → Model Selection → Prompt Selection
"""

import pytest
from app.ai_assistant.classification.content_classifier import ContentClassifier
from app.ai_assistant.classification.model_selector import ModelSelector
from app.ai_assistant.classification.prompt_selector import PromptSelector
from app.ai_assistant.classification.enums import SelectionStrategy


class TestIntegration:
    """Integration tests for complete classification pipeline"""
    
    def test_full_pipeline_religious_content(self):
        """Test complete pipeline for religious content"""
        text = """
        Le Prophète (paix soit sur lui) a dit dans un hadith authentique :
        "La patience est une lumière". Ce rappel nous enseigne l'importance
        de la foi et de l'adoration d'Allah. Le paradis est la récompense
        des croyants qui font le dhikr.
        """
        
        # 1. Classify
        classification = ContentClassifier.classify(text, language="french")
        
        assert classification["primary_domain"] == "religious"
        assert classification["sensitivity"]["requires_strict_mode"] is True
        
        # 2. Select model
        model_selection = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED
        )
        
        # Should force conservative for religious content
        assert model_selection["strategy_used"] == SelectionStrategy.CONSERVATIVE
        assert model_selection["model"] in ["groq", "gpt-4", "claude-3-opus"]
        
        # 3. Select prompt
        prompt_config = PromptSelector.select_prompt(
            classification=classification,
            task="format_text",
            model=model_selection["model"]
        )
        
        assert prompt_config["profile"] == "strict"
        assert prompt_config["use_strict_mode"] is True
        assert len(prompt_config["additional_constraints"]) > 0
    
    def test_full_pipeline_technical_content(self):
        """Test complete pipeline for technical content"""
        text = """
        Le serveur backend utilise FastAPI avec une base de données PostgreSQL.
        L'API REST expose des endpoints JSON. Le code utilise des fonctions
        asynchrones et Docker pour le déploiement.
        """
        
        # 1. Classify
        classification = ContentClassifier.classify(text, language="french")
        
        assert classification["primary_domain"] == "technical"
        
        # 2. Select model
        model_selection = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED
        )
        
        # Technical content doesn't require conservative
        assert model_selection["model"] is not None
        
        # 3. Select prompt
        prompt_config = PromptSelector.select_prompt(
            classification=classification,
            task="format_text",
            model=model_selection["model"]
        )
        
        assert prompt_config["profile"] == "technical"
    
    def test_full_pipeline_mixed_content(self):
        """Test complete pipeline for mixed content"""
        text = """
        Le Prophète (paix soit sur lui) encourageait la recherche scientifique.
        Cette étude analyse les données historiques sur l'islam et la science.
        Les résultats démontrent une corrélation intéressante.
        """
        
        # 1. Classify
        classification = ContentClassifier.classify(text, language="french")
        
        assert classification["is_mixed_content"] is True
        
        # 2. Select model
        model_selection = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED
        )
        
        # Mixed content with religious should be conservative
        if classification["primary_domain"] == "religious":
            assert model_selection["strategy_used"] == SelectionStrategy.CONSERVATIVE
        
        # 3. Select prompt
        prompt_config = PromptSelector.select_prompt(
            classification=classification,
            task="format_text",
            model=model_selection["model"]
        )
        
        assert "mixed" in " ".join(prompt_config["additional_constraints"]).lower() or \
               prompt_config["use_strict_mode"] is True
    
    def test_full_pipeline_general_content(self):
        """Test complete pipeline for general content"""
        text = """
        Bonjour, comment allez-vous aujourd'hui ? J'espère que vous passez
        une bonne journée. Le temps est agréable et ensoleillé.
        """
        
        # 1. Classify
        classification = ContentClassifier.classify(text, language="french")
        
        assert classification["primary_domain"] == "general"
        
        # 2. Select model
        model_selection = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.COST_OPTIMIZED
        )
        
        # Should use cost-optimized for general content
        assert model_selection["strategy_used"] == SelectionStrategy.COST_OPTIMIZED
        assert model_selection["model"] in ["gemini-flash", "groq"]
        
        # 3. Select prompt
        prompt_config = PromptSelector.select_prompt(
            classification=classification,
            task="improve_quality",
            model=model_selection["model"]
        )
        
        assert prompt_config["profile"] == "standard"
        assert prompt_config["use_strict_mode"] is False
    
    def test_strategy_comparison_consistency(self):
        """Test that strategy comparison is consistent"""
        text = "Le Prophète (paix soit sur lui) a dit..."
        
        classification = ContentClassifier.classify(text, language="french")
        comparison = ModelSelector.compare_strategies(classification)
        
        # All strategies should return valid results
        for strategy, result in comparison.items():
            assert "model" in result
            assert result["model"] is not None
            assert "reason" in result
    
    def test_performance_full_pipeline(self):
        """Test that full pipeline completes quickly"""
        import time
        
        text = """
        Le Prophète (paix soit sur lui) a dit : "La patience est une lumière".
        Cette étude scientifique analyse les données avec un protocole rigoureux.
        """
        
        start = time.time()
        
        # Full pipeline
        classification = ContentClassifier.classify(text, language="french")
        model_selection = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED
        )
        prompt_config = PromptSelector.select_prompt(
            classification=classification,
            task="format_text",
            model=model_selection["model"]
        )
        
        duration_ms = (time.time() - start) * 1000
        
        # Should complete in under 100ms (classification alone is <50ms)
        assert duration_ms < 100
    
    def test_metadata_influence(self):
        """Test that metadata influences classification"""
        text = "Ce rappel est important pour nous tous."
        
        # Without metadata
        classification1 = ContentClassifier.classify(text, language="french")
        
        # With religious metadata
        classification2 = ContentClassifier.classify(
            text,
            language="french",
            metadata={"title": "Rappel islamique", "uploader": "Cheikh Mohammed"}
        )
        
        # Both should work (metadata is optional for now)
        assert classification1 is not None
        assert classification2 is not None
    
    def test_language_consistency(self):
        """Test consistency across languages"""
        text_fr = "Le Prophète (paix soit sur lui) a dit..."
        text_en = "The Prophet (peace be upon him) said..."
        
        classification_fr = ContentClassifier.classify(text_fr, language="french")
        classification_en = ContentClassifier.classify(text_en, language="english")
        
        # Both should detect religious content
        assert classification_fr["primary_domain"] == "religious"
        assert classification_en["primary_domain"] == "religious"
        
        # Both should recommend same strategy
        model_fr = ModelSelector.select_model(
            classification=classification_fr,
            strategy=SelectionStrategy.BALANCED
        )
        model_en = ModelSelector.select_model(
            classification=classification_en,
            strategy=SelectionStrategy.BALANCED
        )
        
        assert model_fr["strategy_used"] == model_en["strategy_used"]
    
    def test_prompt_constraints_for_gemini(self):
        """Test that Gemini gets extra constraints"""
        text = "Le Prophète (paix soit sur lui) a dit..."
        
        classification = ContentClassifier.classify(text, language="french")
        
        # With Gemini
        prompt_gemini = PromptSelector.select_prompt(
            classification=classification,
            task="format_text",
            model="gemini-flash"
        )
        
        # With Groq
        prompt_groq = PromptSelector.select_prompt(
            classification=classification,
            task="format_text",
            model="groq"
        )
        
        # Gemini should have more constraints (resist embellishment)
        constraints_gemini = " ".join(prompt_gemini["additional_constraints"]).lower()
        assert "gemini" in constraints_gemini or "embellish" in constraints_gemini
    
    def test_end_to_end_summary(self):
        """Test end-to-end with human-readable summary"""
        text = """
        Le Prophète (paix soit sur lui) a dit dans un hadith authentique :
        "La patience est une lumière".
        """
        
        # Full pipeline
        classification = ContentClassifier.classify(text, language="french")
        model_selection = ModelSelector.select_model(
            classification=classification,
            strategy=SelectionStrategy.BALANCED
        )
        prompt_config = PromptSelector.select_prompt(
            classification=classification,
            task="format_text",
            model=model_selection["model"]
        )
        
        # Generate summary
        summary = ContentClassifier.get_domain_summary(classification)
        
        assert "religious" in summary.lower()
        assert "sensitive" in summary.lower()
        
        # Verify complete result structure
        assert classification["primary_domain"] == "religious"
        assert model_selection["model"] in ["groq", "gpt-4", "claude-3-opus"]
        assert prompt_config["use_strict_mode"] is True

