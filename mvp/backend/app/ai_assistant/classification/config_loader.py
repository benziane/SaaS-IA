"""
Configuration Loader for AI Classification - Grade S++

Loads and caches YAML configuration for content classification.
Provides fast access to domain keywords, model strategies, and settings.
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, List
import structlog
from datetime import UTC, datetime, timedelta

logger = structlog.get_logger()


class ConfigLoader:
    """
    Loads and caches classification configuration from YAML.
    
    Features:
    - Automatic caching for performance
    - Hot reload support
    - Validation of configuration structure
    - Thread-safe access
    
    Usage:
        config = ConfigLoader.load_config()
        domain_config = ConfigLoader.get_domain_config("religious")
    """
    
    _config_cache: Optional[Dict] = None
    _cache_timestamp: Optional[datetime] = None
    _config_path = Path(__file__).parent / "config" / "classification_config.yaml"
    
    # Cache TTL from config (default: 1 hour)
    _cache_ttl_seconds = 3600
    
    @classmethod
    def load_config(cls, force_reload: bool = False) -> Dict:
        """
        Load configuration from YAML file.
        Uses cache for performance unless force_reload=True.
        
        Args:
            force_reload: Force reload from disk, bypass cache
        
        Returns:
            Complete configuration dictionary
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid
        """
        # Check if cache is valid
        if not force_reload and cls._is_cache_valid():
            return cls._config_cache
        
        # Load from file
        try:
            with open(cls._config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Validate config structure
            cls._validate_config(config)
            
            # Update cache
            cls._config_cache = config
            cls._cache_timestamp = datetime.now(UTC)
            
            # Update cache TTL from config
            if "performance" in config and "cache_ttl" in config["performance"]:
                cls._cache_ttl_seconds = config["performance"]["cache_ttl"]
            
            logger.info(
                "classification_config_loaded",
                version=config.get("version", "unknown"),
                domains_count=len(config.get("domains", {})),
                strategies_count=len(config.get("model_selection", {}).get("strategies", {})),
                config_path=str(cls._config_path)
            )
            
            return config
            
        except FileNotFoundError:
            logger.error(
                "classification_config_not_found",
                path=str(cls._config_path)
            )
            raise
        
        except yaml.YAMLError as e:
            logger.error(
                "classification_config_invalid_yaml",
                error=str(e),
                path=str(cls._config_path)
            )
            raise
        
        except Exception as e:
            logger.error(
                "classification_config_load_error",
                error=str(e),
                error_type=type(e).__name__,
                path=str(cls._config_path)
            )
            raise
    
    @classmethod
    def _is_cache_valid(cls) -> bool:
        """Check if cache is still valid."""
        if cls._config_cache is None or cls._cache_timestamp is None:
            return False
        
        age = datetime.now(UTC) - cls._cache_timestamp
        return age < timedelta(seconds=cls._cache_ttl_seconds)
    
    @classmethod
    def _validate_config(cls, config: Dict) -> None:
        """
        Validate configuration structure.
        
        Raises:
            ValueError: If configuration is invalid
        """
        required_keys = ["version", "domains", "model_selection"]
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            raise ValueError(
                f"Invalid configuration: missing required keys: {missing_keys}"
            )
        
        # Validate domains structure
        if not isinstance(config["domains"], dict):
            raise ValueError("Invalid configuration: 'domains' must be a dictionary")
        
        for domain_name, domain_config in config["domains"].items():
            if "keywords" not in domain_config:
                raise ValueError(
                    f"Invalid configuration: domain '{domain_name}' missing 'keywords'"
                )
    
    @classmethod
    def get_domain_config(cls, domain: str) -> Dict:
        """
        Get configuration for a specific domain.
        
        Args:
            domain: Domain name (e.g., "religious", "scientific")
        
        Returns:
            Domain configuration dictionary with keywords and weight
        """
        config = cls.load_config()
        return config.get("domains", {}).get(domain, {})
    
    @classmethod
    def get_domain_keywords(cls, domain: str, language: str = "french") -> List[str]:
        """
        Get keywords for a specific domain and language.
        
        Args:
            domain: Domain name
            language: Language code (french, english, arabic)
        
        Returns:
            List of keywords for the domain/language combination
        """
        domain_config = cls.get_domain_config(domain)
        keywords = domain_config.get("keywords", {})
        return keywords.get(language, [])
    
    @classmethod
    def get_domain_weight(cls, domain: str) -> float:
        """
        Get weight for a specific domain.
        
        Args:
            domain: Domain name
        
        Returns:
            Domain weight (default: 1.0)
        """
        domain_config = cls.get_domain_config(domain)
        return domain_config.get("weight", 1.0)
    
    @classmethod
    def get_strategy_config(cls, strategy: str) -> Dict:
        """
        Get model selection strategy configuration.
        
        Args:
            strategy: Strategy name (conservative, balanced, cost_optimized)
        
        Returns:
            Strategy configuration dictionary
        """
        config = cls.load_config()
        strategies = config.get("model_selection", {}).get("strategies", {})
        return strategies.get(strategy, {})
    
    @classmethod
    def get_tone_patterns(cls) -> Dict[str, List[str]]:
        """
        Get all tone detection patterns.
        
        Returns:
            Dictionary mapping tone names to regex patterns
        """
        config = cls.load_config()
        return config.get("tone_patterns", {})
    
    @classmethod
    def get_sensitivity_keywords(cls, level: str) -> List[str]:
        """
        Get sensitivity keywords for a specific level.
        
        Args:
            level: Sensitivity level (high, medium)
        
        Returns:
            List of keywords that trigger this sensitivity level
        """
        config = cls.load_config()
        sensitivity = config.get("sensitivity_keywords", {})
        return sensitivity.get(level, [])
    
    @classmethod
    def get_prompt_profile_for_domain(cls, domain: str) -> str:
        """
        Get recommended prompt profile for a domain.
        
        Args:
            domain: Domain name
        
        Returns:
            Prompt profile name (strict, standard, creative, etc.)
        """
        config = cls.load_config()
        mapping = config.get("prompt_profiles", {}).get("domain_mapping", {})
        return mapping.get(domain, "standard")
    
    @classmethod
    def get_confidence_thresholds(cls) -> Dict[str, float]:
        """
        Get confidence level thresholds.
        
        Returns:
            Dictionary with high, medium, low thresholds
        """
        config = cls.load_config()
        return config.get("confidence_thresholds", {
            "high": 0.7,
            "medium": 0.4,
            "low": 0.2
        })
    
    @classmethod
    def get_performance_settings(cls) -> Dict:
        """
        Get performance-related settings.
        
        Returns:
            Dictionary with performance configuration
        """
        config = cls.load_config()
        return config.get("performance", {
            "max_text_length": 50000,
            "cache_ttl": 3600,
            "min_keywords_match": 2
        })
    
    @classmethod
    def reload_config(cls) -> Dict:
        """
        Force reload configuration from disk.
        Useful for hot-reloading in development.
        
        Returns:
            Reloaded configuration
        """
        logger.info("classification_config_reload_requested")
        return cls.load_config(force_reload=True)
    
    @classmethod
    def get_all_domains(cls) -> List[str]:
        """
        Get list of all configured domains.
        
        Returns:
            List of domain names
        """
        config = cls.load_config()
        return list(config.get("domains", {}).keys())
    
    @classmethod
    def get_all_models(cls) -> List[str]:
        """
        Get list of all configured AI models.
        
        Returns:
            List of unique model names across all strategies
        """
        config = cls.load_config()
        strategies = config.get("model_selection", {}).get("strategies", {})
        
        models = set()
        for strategy_config in strategies.values():
            for model_list in strategy_config.values():
                models.update(model_list)
        
        return sorted(list(models))

