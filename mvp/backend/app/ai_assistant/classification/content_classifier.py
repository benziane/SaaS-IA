"""
Content Classifier for AI Router - Grade S++

Analyzes text content to determine domain, tone, and sensitivity.
Uses keyword-based classification with multi-domain scoring.

Zero external API cost. Fast (<50ms).
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import structlog

from app.ai_assistant.classification.enums import (
    ContentDomain,
    ContentTone,
    SensitivityLevel
)
from app.ai_assistant.classification.config_loader import ConfigLoader
from app.ai_assistant.classification import metrics

logger = structlog.get_logger()


class ContentClassifier:
    """
    Classifies content using keyword-based rules and patterns.
    
    Features:
    - Multi-domain scoring (not just single domain)
    - Tone detection via regex patterns
    - Sensitivity evaluation
    - Mixed content detection
    - Keyword extraction
    
    Performance: <50ms for typical content
    Cost: $0 (no external API calls)
    
    Usage:
        classification = ContentClassifier.classify(
            text="Le Prophète (paix soit sur lui) a dit...",
            language="french"
        )
    """
    
    @classmethod
    def classify(
        cls,
        text: str,
        language: str = "french",
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze text and return comprehensive classification.
        
        Args:
            text: Content to analyze
            language: Language code (french, english, arabic)
            metadata: Optional metadata (title, source, etc.)
        
        Returns:
            {
                "domains": {
                    "religious": 0.85,
                    "narrative": 0.45,
                    "general": 0.10
                },
                "primary_domain": "religious",
                "secondary_domain": "narrative",
                "is_mixed_content": True,
                "tone": "popular",
                "sensitivity": {
                    "level": "high",
                    "reasons": ["religious_content", "emotional_topics"],
                    "requires_strict_mode": True
                },
                "confidence": 0.85,
                "keywords_found": {
                    "religious": ["allah", "prophète", "hadith"],
                    "narrative": ["histoire", "récit"]
                },
                "language_detected": "french",
                "text_length": 1250,
                "processing_time_ms": 23
            }
        """
        start_time = datetime.utcnow()
        
        # Validate input
        if not text or not text.strip():
            return cls._empty_classification()
        
        text_length = len(text)
        
        # Check max length
        perf_settings = ConfigLoader.get_performance_settings()
        max_length = perf_settings.get("max_text_length", 50000)
        if text_length > max_length:
            text = text[:max_length]
            logger.warning(
                "text_truncated_for_classification",
                original_length=text_length,
                truncated_to=max_length
            )
        
        # 1. Calculate domain scores
        domain_scores, keywords_found = cls._calculate_domain_scores(text, language)
        
        # 2. Determine primary and secondary domains
        primary_domain, secondary_domain, is_mixed = cls._determine_domains(domain_scores)
        
        # 3. Detect tone
        tone = cls._detect_tone(text)
        
        # 4. Evaluate sensitivity
        sensitivity = cls._evaluate_sensitivity(
            domain_scores=domain_scores,
            tone=tone,
            text=text,
            keywords_found=keywords_found
        )
        
        # 5. Calculate overall confidence
        confidence = domain_scores.get(primary_domain, 0.0)
        
        # Processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        result = {
            "domains": domain_scores,
            "primary_domain": primary_domain,
            "secondary_domain": secondary_domain,
            "is_mixed_content": is_mixed,
            "tone": tone,
            "sensitivity": sensitivity,
            "confidence": round(confidence, 3),
            "keywords_found": keywords_found,
            "language_detected": language,
            "text_length": text_length,
            "processing_time_ms": round(processing_time, 2)
        }
        
        # Log classification
        if ConfigLoader.load_config().get("logging", {}).get("log_classifications", True):
            logger.info(
                "content_classified",
                primary_domain=primary_domain,
                confidence=result["confidence"],
                sensitivity_level=sensitivity["level"],
                is_mixed=is_mixed,
                processing_time_ms=result["processing_time_ms"]
            )
        
        # Record Prometheus metrics
        try:
            total_keywords = sum(len(kw) for kw in keywords_found.values())
            metrics.record_classification(
                domain=primary_domain,
                language=language,
                sensitivity_level=sensitivity["level"],
                confidence=confidence,
                duration_seconds=processing_time / 1000,  # Convert ms to seconds
                tone=tone,
                is_mixed=is_mixed,
                secondary_domain=secondary_domain,
                keywords_count=total_keywords
            )
        except Exception as e:
            logger.warning("metrics_recording_failed", error=str(e))
        
        return result
    
    @classmethod
    def _calculate_domain_scores(
        cls,
        text: str,
        language: str
    ) -> Tuple[Dict[str, float], Dict[str, List[str]]]:
        """
        Calculate score for each domain based on keyword matching.
        
        Returns:
            (domain_scores, keywords_found)
        """
        text_lower = text.lower()
        domain_scores = {}
        keywords_found = {}
        
        all_domains = ConfigLoader.get_all_domains()
        perf_settings = ConfigLoader.get_performance_settings()
        min_keywords = perf_settings.get("min_keywords_match", 2)
        
        for domain in all_domains:
            keywords = ConfigLoader.get_domain_keywords(domain, language)
            weight = ConfigLoader.get_domain_weight(domain)
            
            if not keywords:
                continue
            
            # Find matching keywords
            matches = [kw for kw in keywords if kw in text_lower]
            
            # Only consider domain if minimum keywords matched
            if len(matches) < min_keywords:
                continue
            
            # Calculate normalized score with weight
            score = (len(matches) / len(keywords)) * weight
            domain_scores[domain] = round(score, 3)
            
            if matches:
                keywords_found[domain] = matches[:10]  # Limit to 10 keywords
        
        # Ensure at least "general" domain exists
        if not domain_scores:
            domain_scores[ContentDomain.GENERAL] = 1.0
        
        return domain_scores, keywords_found
    
    @classmethod
    def _determine_domains(
        cls,
        domain_scores: Dict[str, float]
    ) -> Tuple[str, Optional[str], bool]:
        """
        Determine primary and secondary domains.
        
        Returns:
            (primary_domain, secondary_domain, is_mixed_content)
        """
        if not domain_scores:
            return ContentDomain.GENERAL, None, False
        
        # Sort domains by score
        sorted_domains = sorted(
            domain_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        primary_domain = sorted_domains[0][0]
        primary_score = sorted_domains[0][1]
        
        # Check for secondary domain (score > 30% of primary)
        secondary_domain = None
        is_mixed = False
        
        if len(sorted_domains) > 1:
            secondary_score = sorted_domains[1][1]
            if secondary_score > (primary_score * 0.3):
                secondary_domain = sorted_domains[1][0]
                is_mixed = True
        
        return primary_domain, secondary_domain, is_mixed
    
    @classmethod
    def _detect_tone(cls, text: str) -> ContentTone:
        """
        Detect tone using regex patterns.
        
        Returns:
            ContentTone enum value
        """
        text_lower = text.lower()
        tone_patterns = ConfigLoader.get_tone_patterns()
        
        # Check patterns in priority order
        priority_order = [
            ContentTone.FORMAL,
            ContentTone.ACADEMIC,
            ContentTone.CONVERSATIONAL,
            ContentTone.POPULAR
        ]
        
        for tone in priority_order:
            patterns = tone_patterns.get(tone, [])
            for pattern in patterns:
                try:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        return tone
                except re.error:
                    logger.warning(
                        "invalid_tone_pattern",
                        tone=tone,
                        pattern=pattern
                    )
                    continue
        
        return ContentTone.NEUTRAL
    
    @classmethod
    def _evaluate_sensitivity(
        cls,
        domain_scores: Dict[str, float],
        tone: ContentTone,
        text: str,
        keywords_found: Dict[str, List[str]]
    ) -> Dict:
        """
        Evaluate content sensitivity level.
        
        Returns:
            {
                "level": "high",
                "reasons": ["religious_content", "emotional_topics"],
                "requires_strict_mode": True
            }
        """
        reasons = []
        level = SensitivityLevel.LOW
        text_lower = text.lower()
        
        # High sensitivity domains
        sensitive_domains = {
            ContentDomain.RELIGIOUS: "religious_content",
            ContentDomain.MEDICAL: "medical_content",
            ContentDomain.LEGAL: "legal_content"
        }
        
        for domain, reason in sensitive_domains.items():
            if domain_scores.get(domain, 0) > 0.5:
                reasons.append(reason)
                level = SensitivityLevel.HIGH
        
        # Check sensitivity keywords
        high_sensitivity_kw = ConfigLoader.get_sensitivity_keywords("high")
        medium_sensitivity_kw = ConfigLoader.get_sensitivity_keywords("medium")
        
        high_matches = [kw for kw in high_sensitivity_kw if kw in text_lower]
        medium_matches = [kw for kw in medium_sensitivity_kw if kw in text_lower]
        
        if high_matches:
            reasons.append("high_sensitivity_keywords")
            level = max(level, SensitivityLevel.HIGH)
        elif medium_matches:
            reasons.append("medium_sensitivity_keywords")
            level = max(level, SensitivityLevel.MEDIUM)
        
        # Mixed content with sensitive domain
        if any(domain in domain_scores for domain in sensitive_domains.keys()):
            if len(domain_scores) > 2:  # Multiple domains
                reasons.append("mixed_sensitive_content")
                level = max(level, SensitivityLevel.MEDIUM)
        
        # Determine if strict mode required
        requires_strict = level in [SensitivityLevel.HIGH, SensitivityLevel.CRITICAL]
        
        return {
            "level": level,
            "reasons": list(set(reasons)),  # Remove duplicates
            "requires_strict_mode": requires_strict
        }
    
    @classmethod
    def _empty_classification(cls) -> Dict:
        """Return empty classification for invalid input."""
        return {
            "domains": {ContentDomain.GENERAL: 1.0},
            "primary_domain": ContentDomain.GENERAL,
            "secondary_domain": None,
            "is_mixed_content": False,
            "tone": ContentTone.NEUTRAL,
            "sensitivity": {
                "level": SensitivityLevel.LOW,
                "reasons": [],
                "requires_strict_mode": False
            },
            "confidence": 0.0,
            "keywords_found": {},
            "language_detected": "unknown",
            "text_length": 0,
            "processing_time_ms": 0
        }
    
    @classmethod
    def classify_batch(
        cls,
        texts: List[str],
        language: str = "french"
    ) -> List[Dict]:
        """
        Classify multiple texts in batch.
        
        Args:
            texts: List of texts to classify
            language: Language code
        
        Returns:
            List of classification results
        """
        return [cls.classify(text, language) for text in texts]
    
    @classmethod
    def get_domain_summary(cls, classification: Dict) -> str:
        """
        Get human-readable summary of classification.
        
        Args:
            classification: Classification result
        
        Returns:
            Summary string
        """
        primary = classification["primary_domain"]
        confidence = classification["confidence"]
        sensitivity = classification["sensitivity"]["level"]
        
        summary = f"Domain: {primary} (confidence: {confidence:.0%})"
        
        if classification["is_mixed_content"]:
            secondary = classification["secondary_domain"]
            summary += f" + {secondary}"
        
        if sensitivity in ["high", "critical"]:
            summary += f" [SENSITIVE: {sensitivity}]"
        
        return summary

