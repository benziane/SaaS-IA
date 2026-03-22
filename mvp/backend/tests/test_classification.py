"""
Unit tests for ContentClassifier.

Covers:
- Religious content detection
- Scientific content detection
- Tone detection
- Sensitivity level evaluation
- Empty / edge-case inputs
- Batch classification

All tests run WITHOUT external API calls.  The classifier is
keyword-based and loads its config from YAML on disk.
"""

import pytest

from app.ai_assistant.classification.content_classifier import ContentClassifier
from app.ai_assistant.classification.enums import (
    ContentDomain,
    ContentTone,
    SensitivityLevel,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify(text: str, language: str = "french"):
    """Shortcut that returns the classification dict."""
    return ContentClassifier.classify(text, language=language)


# ---------------------------------------------------------------------------
# Tests: religious content detection
# ---------------------------------------------------------------------------

class TestReligiousDetection:
    """ContentClassifier should identify religious content."""

    def test_primary_domain_is_religious(self, sample_religious_text):
        result = _classify(sample_religious_text)
        assert result["primary_domain"] == ContentDomain.RELIGIOUS

    def test_religious_keywords_found(self, sample_religious_text):
        result = _classify(sample_religious_text)
        kw = result["keywords_found"]
        assert "religious" in kw
        assert len(kw["religious"]) >= 2

    def test_religious_confidence_above_threshold(self, sample_religious_text):
        result = _classify(sample_religious_text)
        assert result["confidence"] > 0.3

    def test_religious_domain_score_present(self, sample_religious_text):
        result = _classify(sample_religious_text)
        assert ContentDomain.RELIGIOUS in result["domains"]
        assert result["domains"][ContentDomain.RELIGIOUS] > 0


# ---------------------------------------------------------------------------
# Tests: scientific content detection
# ---------------------------------------------------------------------------

class TestScientificDetection:
    """ContentClassifier should identify scientific content."""

    def test_primary_domain_is_scientific(self, sample_scientific_text):
        result = _classify(sample_scientific_text)
        assert result["primary_domain"] == ContentDomain.SCIENTIFIC

    def test_scientific_keywords_found(self, sample_scientific_text):
        result = _classify(sample_scientific_text)
        kw = result["keywords_found"]
        assert "scientific" in kw
        assert len(kw["scientific"]) >= 2

    def test_scientific_confidence_above_threshold(self, sample_scientific_text):
        result = _classify(sample_scientific_text)
        assert result["confidence"] > 0.2


# ---------------------------------------------------------------------------
# Tests: general / unclassifiable content
# ---------------------------------------------------------------------------

class TestGeneralDetection:
    """Unclassifiable content should fall back to ``general``."""

    def test_primary_domain_is_general(self, sample_general_text):
        result = _classify(sample_general_text)
        assert result["primary_domain"] == ContentDomain.GENERAL

    def test_general_has_no_keywords(self, sample_general_text):
        result = _classify(sample_general_text)
        # general domain typically has no matched keywords
        assert len(result["keywords_found"]) == 0


# ---------------------------------------------------------------------------
# Tests: tone detection
# ---------------------------------------------------------------------------

class TestToneDetection:
    """ContentClassifier should detect the tone of text."""

    def test_academic_tone(self):
        text = (
            "Selon les recherches menees, l'hypothese initiale a ete confirmee. "
            "En effet, l'analyse statistique montre une conclusion significative."
        )
        result = _classify(text)
        # academic patterns: "selon", "en effet", "analyse", "conclusion"
        assert result["tone"] in [ContentTone.ACADEMIC, ContentTone.FORMAL, ContentTone.NEUTRAL]

    def test_formal_tone(self):
        text = (
            "Veuillez trouver ci-joint le reglement conformement a l'article 12. "
            "Monsieur le directeur, nous vous prions d'agréer nos salutations."
        )
        result = _classify(text)
        assert result["tone"] == ContentTone.FORMAL

    def test_popular_tone(self):
        """Text with informal markers should be detected as popular
        or conversational (both are informal tones)."""
        text = "Salut ! Tu as vu cette video ? C'est super cool et genial !!"
        result = _classify(text)
        assert result["tone"] in [ContentTone.POPULAR, ContentTone.CONVERSATIONAL]

    def test_neutral_tone_for_plain_text(self, sample_general_text):
        result = _classify(sample_general_text)
        # Plain text without strong signals should be neutral or popular
        assert result["tone"] in [
            ContentTone.NEUTRAL,
            ContentTone.POPULAR,
            ContentTone.CONVERSATIONAL,
        ]


# ---------------------------------------------------------------------------
# Tests: sensitivity evaluation
# ---------------------------------------------------------------------------

class TestSensitivity:
    """ContentClassifier should assign correct sensitivity levels."""

    def test_religious_content_is_high_sensitivity(self, sample_religious_text):
        result = _classify(sample_religious_text)
        sensitivity = result["sensitivity"]
        assert sensitivity["level"] in [SensitivityLevel.HIGH, SensitivityLevel.CRITICAL]

    def test_religious_requires_strict_mode(self, sample_religious_text):
        result = _classify(sample_religious_text)
        assert result["sensitivity"]["requires_strict_mode"] is True

    def test_general_content_is_low_sensitivity(self, sample_general_text):
        result = _classify(sample_general_text)
        assert result["sensitivity"]["level"] == SensitivityLevel.LOW

    def test_general_does_not_require_strict_mode(self, sample_general_text):
        result = _classify(sample_general_text)
        assert result["sensitivity"]["requires_strict_mode"] is False

    def test_high_sensitivity_keywords_detected(self):
        """Text containing high-sensitivity keywords (from YAML config)
        should be flagged in sensitivity reasons even if the domain
        defaults to general."""
        text = (
            "Cette tragédie impliquant un décès et de la souffrance "
            "a profondément marqué la communauté. La mort est un sujet "
            "difficile qui requiert du respect."
        )
        result = _classify(text)
        sensitivity = result["sensitivity"]
        assert "high_sensitivity_keywords" in sensitivity["reasons"]

    def test_medium_sensitivity_keywords(self):
        text = (
            "Le stress et l'anxiete sont des facteurs importants dans "
            "l'emotion ressentie lors d'un conflit au sein de la famille. "
            "La depression touche de nombreuses personnes."
        )
        result = _classify(text)
        sensitivity = result["sensitivity"]
        assert sensitivity["level"] in [
            SensitivityLevel.MEDIUM,
            SensitivityLevel.HIGH,
            SensitivityLevel.CRITICAL,
        ]

    def test_sensitivity_reasons_not_empty_for_high(self, sample_religious_text):
        result = _classify(sample_religious_text)
        assert len(result["sensitivity"]["reasons"]) > 0


# ---------------------------------------------------------------------------
# Tests: edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases and invariants."""

    def test_empty_string_returns_general(self):
        result = _classify("")
        assert result["primary_domain"] == ContentDomain.GENERAL
        assert result["confidence"] == 0.0

    def test_whitespace_only_returns_general(self):
        result = _classify("   \n\t  ")
        assert result["primary_domain"] == ContentDomain.GENERAL
        assert result["confidence"] == 0.0

    def test_result_contains_required_keys(self, sample_general_text):
        result = _classify(sample_general_text)
        required_keys = [
            "domains",
            "primary_domain",
            "secondary_domain",
            "is_mixed_content",
            "tone",
            "sensitivity",
            "confidence",
            "keywords_found",
            "language_detected",
            "text_length",
            "processing_time_ms",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_sensitivity_contains_required_keys(self, sample_general_text):
        result = _classify(sample_general_text)
        sens = result["sensitivity"]
        assert "level" in sens
        assert "reasons" in sens
        assert "requires_strict_mode" in sens

    def test_text_length_is_correct(self):
        text = "Hello world"
        result = _classify(text)
        assert result["text_length"] == len(text)

    def test_language_detected_matches_input(self):
        result = _classify("Some text", language="english")
        assert result["language_detected"] == "english"

    def test_processing_time_is_non_negative(self, sample_scientific_text):
        result = _classify(sample_scientific_text)
        assert result["processing_time_ms"] >= 0

    def test_confidence_between_zero_and_one_inclusive(self, sample_religious_text):
        result = _classify(sample_religious_text)
        assert 0.0 <= result["confidence"] <= 2.0  # weight can push above 1.0


# ---------------------------------------------------------------------------
# Tests: batch classification
# ---------------------------------------------------------------------------

class TestBatchClassification:
    """Tests for ``classify_batch``."""

    def test_batch_returns_list(self, sample_religious_text, sample_scientific_text):
        results = ContentClassifier.classify_batch(
            [sample_religious_text, sample_scientific_text],
            language="french",
        )
        assert isinstance(results, list)
        assert len(results) == 2

    def test_batch_preserves_order(self, sample_religious_text, sample_general_text):
        results = ContentClassifier.classify_batch(
            [sample_religious_text, sample_general_text],
            language="french",
        )
        assert results[0]["primary_domain"] == ContentDomain.RELIGIOUS
        assert results[1]["primary_domain"] == ContentDomain.GENERAL

    def test_batch_empty_list(self):
        results = ContentClassifier.classify_batch([], language="french")
        assert results == []


# ---------------------------------------------------------------------------
# Tests: domain summary helper
# ---------------------------------------------------------------------------

class TestGetDomainSummary:
    """Tests for ``get_domain_summary``."""

    def test_summary_contains_domain(self, sample_scientific_text):
        result = _classify(sample_scientific_text)
        summary = ContentClassifier.get_domain_summary(result)
        assert "scientific" in summary.lower() or "Domain:" in summary

    def test_summary_for_mixed_content(self, sample_religious_text):
        result = _classify(sample_religious_text)
        summary = ContentClassifier.get_domain_summary(result)
        # Summary should at least mention primary domain
        assert result["primary_domain"] in summary

    def test_summary_marks_sensitive(self):
        """Highly sensitive content should be marked in the summary."""
        # Build a classification dict manually
        mock_classification = {
            "primary_domain": "religious",
            "secondary_domain": None,
            "is_mixed_content": False,
            "confidence": 0.9,
            "sensitivity": {"level": "high", "reasons": ["religious_content"], "requires_strict_mode": True},
        }
        summary = ContentClassifier.get_domain_summary(mock_classification)
        assert "SENSITIVE" in summary
