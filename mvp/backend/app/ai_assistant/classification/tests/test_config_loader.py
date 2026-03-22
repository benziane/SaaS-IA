"""
Unit Tests for ConfigLoader - Grade S++

Tests configuration loading, caching, and validation.
"""

import pytest
from app.ai_assistant.classification.config_loader import ConfigLoader
from app.ai_assistant.classification.enums import ContentDomain


class TestConfigLoader:
    """Test suite for ConfigLoader"""
    
    def test_load_config(self):
        """Test basic config loading"""
        config = ConfigLoader.load_config()
        
        assert config is not None
        assert "version" in config
        assert "domains" in config
        assert "model_selection" in config
    
    def test_config_caching(self):
        """Test that config is cached"""
        config1 = ConfigLoader.load_config()
        config2 = ConfigLoader.load_config()
        
        # Should return same object (cached)
        assert config1 is config2
    
    def test_force_reload(self):
        """Test force reload bypasses cache"""
        config1 = ConfigLoader.load_config()
        config2 = ConfigLoader.load_config(force_reload=True)
        
        # Should be different objects
        assert config1 is not config2
        # But should have same content
        assert config1["version"] == config2["version"]
    
    def test_get_domain_config(self):
        """Test getting domain configuration"""
        domain_config = ConfigLoader.get_domain_config("religious")
        
        assert domain_config is not None
        assert "keywords" in domain_config
        assert "weight" in domain_config
    
    def test_get_domain_keywords(self):
        """Test getting domain keywords"""
        keywords = ConfigLoader.get_domain_keywords("religious", "french")
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "allah" in keywords
        assert "prophète" in keywords
    
    def test_get_domain_weight(self):
        """Test getting domain weight"""
        weight = ConfigLoader.get_domain_weight("religious")
        
        assert isinstance(weight, float)
        assert weight > 0
    
    def test_get_strategy_config(self):
        """Test getting strategy configuration"""
        strategy = ConfigLoader.get_strategy_config("balanced")
        
        assert isinstance(strategy, dict)
        assert "religious" in strategy
        assert "general" in strategy
    
    def test_get_tone_patterns(self):
        """Test getting tone patterns"""
        patterns = ConfigLoader.get_tone_patterns()
        
        assert isinstance(patterns, dict)
        assert "academic" in patterns
        assert "formal" in patterns
        assert "popular" in patterns
    
    def test_get_sensitivity_keywords(self):
        """Test getting sensitivity keywords"""
        high_keywords = ConfigLoader.get_sensitivity_keywords("high")
        medium_keywords = ConfigLoader.get_sensitivity_keywords("medium")
        
        assert isinstance(high_keywords, list)
        assert isinstance(medium_keywords, list)
        assert len(high_keywords) > 0
    
    def test_get_prompt_profile_for_domain(self):
        """Test getting prompt profile for domain"""
        profile = ConfigLoader.get_prompt_profile_for_domain("religious")
        
        assert profile == "strict"
        
        profile_general = ConfigLoader.get_prompt_profile_for_domain("general")
        assert profile_general == "standard"
    
    def test_get_confidence_thresholds(self):
        """Test getting confidence thresholds"""
        thresholds = ConfigLoader.get_confidence_thresholds()
        
        assert "high" in thresholds
        assert "medium" in thresholds
        assert "low" in thresholds
        assert thresholds["high"] > thresholds["medium"] > thresholds["low"]
    
    def test_get_performance_settings(self):
        """Test getting performance settings"""
        settings = ConfigLoader.get_performance_settings()
        
        assert "max_text_length" in settings
        assert "cache_ttl" in settings
        assert "min_keywords_match" in settings
    
    def test_get_all_domains(self):
        """Test getting all configured domains"""
        domains = ConfigLoader.get_all_domains()
        
        assert isinstance(domains, list)
        assert len(domains) > 0
        assert "religious" in domains
        assert "scientific" in domains
        assert "technical" in domains
    
    def test_get_all_models(self):
        """Test getting all configured models"""
        models = ConfigLoader.get_all_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
    
    def test_reload_config(self):
        """Test config reload"""
        config1 = ConfigLoader.load_config()
        config2 = ConfigLoader.reload_config()
        
        assert config1 is not config2
        assert config1["version"] == config2["version"]
    
    def test_missing_domain_returns_empty(self):
        """Test that missing domain returns empty dict"""
        config = ConfigLoader.get_domain_config("nonexistent_domain")
        
        assert config == {}
    
    def test_missing_language_returns_empty_list(self):
        """Test that missing language returns empty list"""
        keywords = ConfigLoader.get_domain_keywords("religious", "nonexistent_language")
        
        assert keywords == []
    
    def test_config_has_all_required_domains(self):
        """Test that config has all required domains"""
        required_domains = [
            "religious", "scientific", "technical", 
            "administrative", "narrative", "general"
        ]
        
        domains = ConfigLoader.get_all_domains()
        
        for required in required_domains:
            assert required in domains
    
    def test_config_has_all_strategies(self):
        """Test that config has all strategies"""
        required_strategies = ["conservative", "balanced", "cost_optimized"]
        
        config = ConfigLoader.load_config()
        strategies = config["model_selection"]["strategies"]
        
        for required in required_strategies:
            assert required in strategies
    
    def test_domain_keywords_not_empty(self):
        """Test that domain keywords are not empty"""
        domains = ["religious", "scientific", "technical"]
        
        for domain in domains:
            keywords = ConfigLoader.get_domain_keywords(domain, "french")
            assert len(keywords) > 0, f"Domain {domain} has no French keywords"

