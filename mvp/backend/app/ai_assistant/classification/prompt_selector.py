"""
Prompt Selector for AI Router - Grade S++

Selects appropriate prompt profile and constraints based on content classification.
"""

from typing import Dict, List
import structlog

from app.ai_assistant.classification.enums import (
    PromptProfile,
    SensitivityLevel
)
from app.ai_assistant.classification.config_loader import ConfigLoader

logger = structlog.get_logger()


class PromptSelector:
    """
    Selects appropriate prompt profile based on content classification.
    
    Features:
    - Domain-specific prompt profiles
    - Sensitivity-aware prompt selection
    - Model-specific adjustments
    - Additional constraint injection
    
    Usage:
        prompt_config = PromptSelector.select_prompt(
            classification=classification_result,
            task="format_text",
            model="groq"
        )
    """
    
    @classmethod
    def select_prompt(
        cls,
        classification: Dict,
        task: str,
        model: str
    ) -> Dict:
        """
        Select prompt profile and configuration.
        
        Args:
            classification: Output from ContentClassifier.classify()
            task: Task name (format_text, improve_quality, translate, etc.)
            model: Selected AI model
        
        Returns:
            {
                "profile": "strict",
                "task_adjusted": "format_text_strict",
                "additional_constraints": [
                    "Religious content: preserve exact meaning",
                    "No poetic embellishment"
                ],
                "use_strict_mode": True,
                "reason": "High sensitivity religious content"
            }
        """
        # Extract classification info
        primary_domain = classification["primary_domain"]
        sensitivity = classification["sensitivity"]
        sensitivity_level = sensitivity["level"]
        is_mixed = classification["is_mixed_content"]
        
        # Get base profile for domain
        profile = cls._get_profile_for_domain(primary_domain)
        
        # Adjust for sensitivity
        if sensitivity["requires_strict_mode"]:
            profile = PromptProfile.STRICT
        
        # Generate additional constraints
        constraints = cls._generate_constraints(
            domain=primary_domain,
            sensitivity=sensitivity,
            is_mixed=is_mixed,
            model=model
        )
        
        # Adjust task name if strict mode
        task_adjusted = task
        use_strict_mode = (profile == PromptProfile.STRICT)
        
        # Generate selection reason
        reason = cls._generate_reason(
            profile=profile,
            domain=primary_domain,
            sensitivity_level=sensitivity_level
        )
        
        result = {
            "profile": profile,
            "task_adjusted": task_adjusted,
            "additional_constraints": constraints,
            "use_strict_mode": use_strict_mode,
            "reason": reason
        }
        
        logger.info(
            "prompt_selected",
            profile=profile,
            task=task,
            domain=primary_domain,
            strict_mode=use_strict_mode,
            constraints_count=len(constraints)
        )
        
        return result
    
    @classmethod
    def _get_profile_for_domain(cls, domain: str) -> PromptProfile:
        """
        Get recommended prompt profile for domain.
        
        Returns:
            PromptProfile enum value
        """
        profile_name = ConfigLoader.get_prompt_profile_for_domain(domain)
        
        # Map string to enum
        profile_map = {
            "strict": PromptProfile.STRICT,
            "standard": PromptProfile.STANDARD,
            "creative": PromptProfile.CREATIVE,
            "technical": PromptProfile.TECHNICAL,
            "translation": PromptProfile.TRANSLATION
        }
        
        return profile_map.get(profile_name, PromptProfile.STANDARD)
    
    @classmethod
    def _generate_constraints(
        cls,
        domain: str,
        sensitivity: Dict,
        is_mixed: bool,
        model: str
    ) -> List[str]:
        """
        Generate additional prompt constraints based on context.
        
        Returns:
            List of constraint strings
        """
        constraints = []
        
        # Domain-specific constraints
        domain_constraints = {
            "religious": [
                "Preserve exact religious meaning and context",
                "No interpretation or personal opinion",
                "Maintain reverence and respect"
            ],
            "scientific": [
                "Preserve technical accuracy",
                "Maintain scientific terminology",
                "No simplification that changes meaning"
            ],
            "medical": [
                "Preserve medical accuracy",
                "No diagnosis or medical advice",
                "Maintain professional terminology"
            ],
            "legal": [
                "Preserve legal accuracy",
                "No legal interpretation",
                "Maintain formal legal language"
            ],
            "technical": [
                "Preserve technical accuracy",
                "Maintain technical terminology",
                "No oversimplification"
            ]
        }
        
        if domain in domain_constraints:
            constraints.extend(domain_constraints[domain])
        
        # Sensitivity-based constraints
        if sensitivity["requires_strict_mode"]:
            constraints.extend([
                "STRICT MODE: No embellishment or poetic language",
                "Preserve original tone and style exactly",
                "No additions beyond clarification"
            ])
        
        # Mixed content constraints
        if is_mixed:
            constraints.append(
                "Mixed content: maintain distinct treatment of each topic"
            )
        
        # Model-specific constraints (Gemini tends to embellish)
        if "gemini" in model.lower():
            constraints.extend([
                "Gemini: Resist natural tendency to embellish",
                "Keep language simple and direct"
            ])
        
        return constraints
    
    @classmethod
    def _generate_reason(
        cls,
        profile: PromptProfile,
        domain: str,
        sensitivity_level: str
    ) -> str:
        """
        Generate human-readable reason for prompt selection.
        
        Returns:
            Reason string
        """
        if profile == PromptProfile.STRICT:
            if sensitivity_level in [SensitivityLevel.HIGH, SensitivityLevel.CRITICAL]:
                return f"Strict mode for sensitive {domain} content"
            return f"Strict mode for {domain} content"
        
        if profile == PromptProfile.TECHNICAL:
            return f"Technical precision for {domain} content"
        
        if profile == PromptProfile.CREATIVE:
            return f"Creative freedom for {domain} content"
        
        return f"Standard prompt for {domain} content"
    
    @classmethod
    def get_prompt_modifiers(
        cls,
        classification: Dict,
        model: str
    ) -> Dict[str, bool]:
        """
        Get boolean flags for prompt modifiers.
        Useful for template rendering.
        
        Args:
            classification: Classification result
            model: Selected model
        
        Returns:
            {
                "use_strict_mode": True,
                "preserve_religious_context": True,
                "resist_embellishment": True,
                "maintain_technical_accuracy": False,
                "allow_creative_freedom": False
            }
        """
        domain = classification["primary_domain"]
        sensitivity = classification["sensitivity"]
        
        modifiers = {
            "use_strict_mode": sensitivity["requires_strict_mode"],
            "preserve_religious_context": domain == "religious",
            "resist_embellishment": "gemini" in model.lower(),
            "maintain_technical_accuracy": domain in ["technical", "scientific"],
            "allow_creative_freedom": domain == "narrative" and sensitivity["level"] == SensitivityLevel.LOW,
            "preserve_medical_accuracy": domain == "medical",
            "preserve_legal_accuracy": domain == "legal"
        }
        
        return modifiers
    
    @classmethod
    def format_constraints_for_prompt(
        cls,
        constraints: List[str]
    ) -> str:
        """
        Format constraints list for inclusion in prompt.
        
        Args:
            constraints: List of constraint strings
        
        Returns:
            Formatted string for prompt injection
        """
        if not constraints:
            return ""
        
        formatted = "\n\nADDITIONAL CONSTRAINTS:\n"
        for i, constraint in enumerate(constraints, 1):
            formatted += f"{i}. {constraint}\n"
        
        return formatted
    
    @classmethod
    def get_all_profiles(cls) -> List[str]:
        """
        Get list of all available prompt profiles.
        
        Returns:
            List of profile names
        """
        return [profile.value for profile in PromptProfile]

