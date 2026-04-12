"""Tests for the presidio_service module — London School TDD (mock-first).

Covers:
- is_available() detection (Presidio installed vs. not)
- detect_pii() with mocked AnalyzerEngine (email, phone)
- detect_pii() returns empty list when Presidio unavailable
- detect_pii() per-entity threshold filtering
- anonymize() with mocked engines — returns (anon_text, mapping) tuple
- anonymize() returns original text when Presidio unavailable
- SEVERITY_MAP sanity checks
- Language validation/fallback
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# is_available()
# ---------------------------------------------------------------------------

class TestIsAvailable:
    """is_available() should reflect whether Presidio is importable."""

    def test_returns_true_when_presidio_installed(self):
        """When presidio_analyzer is importable, is_available returns True."""
        import sys
        import app.modules.security_guardian.presidio_service as ps

        mock_analyzer_mod = MagicMock()
        mock_anonymizer_mod = MagicMock()

        with patch.dict(sys.modules, {
            "presidio_analyzer": mock_analyzer_mod,
            "presidio_anonymizer": mock_anonymizer_mod,
        }):
            ps._available = None
            result = ps.is_available()
            ps._available = None  # clean up for other tests

        assert result is True

    def test_returns_false_when_presidio_missing(self):
        """When Presidio is marked as unavailable, is_available returns False."""
        import app.modules.security_guardian.presidio_service as ps

        original = ps._available
        ps._available = False
        result = ps.is_available()
        ps._available = original  # restore

        assert result is False


# ---------------------------------------------------------------------------
# SEVERITY_MAP sanity
# ---------------------------------------------------------------------------

class TestSeverityMap:
    """SEVERITY_MAP should contain the critical financial PII types."""

    def test_credit_card_is_critical(self):
        from app.modules.security_guardian.presidio_service import SEVERITY_MAP
        assert SEVERITY_MAP.get("CREDIT_CARD") == "critical"

    def test_email_is_high(self):
        from app.modules.security_guardian.presidio_service import SEVERITY_MAP
        assert SEVERITY_MAP.get("EMAIL_ADDRESS") == "high"

    def test_iban_is_critical(self):
        from app.modules.security_guardian.presidio_service import SEVERITY_MAP
        assert SEVERITY_MAP.get("IBAN_CODE") == "critical"

    def test_fr_iban_is_critical(self):
        from app.modules.security_guardian.presidio_service import SEVERITY_MAP
        assert SEVERITY_MAP.get("FR_IBAN") == "critical"

    def test_ip_address_is_medium(self):
        from app.modules.security_guardian.presidio_service import SEVERITY_MAP
        assert SEVERITY_MAP.get("IP_ADDRESS") == "medium"

    def test_phone_number_is_high(self):
        from app.modules.security_guardian.presidio_service import SEVERITY_MAP
        assert SEVERITY_MAP.get("PHONE_NUMBER") == "high"


# ---------------------------------------------------------------------------
# detect_pii() — Presidio available (mocked)
# ---------------------------------------------------------------------------

class TestDetectPiiWithPresidio:
    """detect_pii() uses the mocked AnalyzerEngine to return findings."""

    def _make_result(self, entity_type, start, end, score=0.9):
        r = MagicMock()
        r.entity_type = entity_type
        r.start = start
        r.end = end
        r.score = score
        return r

    def test_detect_email_returns_finding(self):
        """A detected EMAIL_ADDRESS should produce a finding with 'high' severity."""
        import app.modules.security_guardian.presidio_service as ps

        text = "Contact alice@example.com for support."
        mock_result = self._make_result("EMAIL_ADDRESS", 8, 25, score=0.92)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = [mock_result]

        with patch.object(ps, "_get_analyzer", return_value=mock_analyzer):
            findings = ps.detect_pii(text, language="en")

        assert len(findings) == 1
        assert findings[0]["type"] == "pii_email_address"
        assert findings[0]["severity"] == "high"
        assert findings[0]["presidio_entity"] == "EMAIL_ADDRESS"
        assert round(findings[0]["presidio_score"], 2) == 0.92

    def test_detect_phone_returns_finding(self):
        """A detected PHONE_NUMBER should produce a finding with 'high' severity."""
        import app.modules.security_guardian.presidio_service as ps

        text = "Call me at +1-555-123-4567."
        mock_result = self._make_result("PHONE_NUMBER", 11, 26, score=0.85)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = [mock_result]

        with patch.object(ps, "_get_analyzer", return_value=mock_analyzer):
            findings = ps.detect_pii(text, language="en")

        assert len(findings) == 1
        assert findings[0]["type"] == "pii_phone_number"
        assert findings[0]["severity"] == "high"

    def test_detect_credit_card_returns_critical(self):
        """A detected CREDIT_CARD should have 'critical' severity."""
        import app.modules.security_guardian.presidio_service as ps

        text = "My card is 4111111111111111."
        mock_result = self._make_result("CREDIT_CARD", 11, 27, score=0.98)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = [mock_result]

        with patch.object(ps, "_get_analyzer", return_value=mock_analyzer):
            findings = ps.detect_pii(text, language="en")

        assert len(findings) == 1
        assert findings[0]["severity"] == "critical"

    def test_detect_multiple_entities_returns_all(self):
        """Multiple detected entities are all returned."""
        import app.modules.security_guardian.presidio_service as ps

        text = "Email alice@example.com or call 555-1234."
        mock_results = [
            self._make_result("EMAIL_ADDRESS", 6, 23, score=0.9),
            self._make_result("PHONE_NUMBER", 32, 40, score=0.8),
        ]

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = mock_results

        with patch.object(ps, "_get_analyzer", return_value=mock_analyzer):
            findings = ps.detect_pii(text)

        assert len(findings) == 2
        types = {f["presidio_entity"] for f in findings}
        assert types == {"EMAIL_ADDRESS", "PHONE_NUMBER"}

    def test_threshold_filters_low_confidence(self):
        """Results below the default threshold (0.5) are excluded."""
        import app.modules.security_guardian.presidio_service as ps

        text = "Maybe a name here."
        # score=0.45 < default threshold 0.5
        mock_result = self._make_result("PERSON", 0, 5, score=0.45)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = [mock_result]

        with patch.object(ps, "_get_analyzer", return_value=mock_analyzer):
            findings = ps.detect_pii(text, language="en")

        assert len(findings) == 0

    def test_custom_threshold_allows_low_confidence(self):
        """A lower custom threshold lets low-confidence results through."""
        import app.modules.security_guardian.presidio_service as ps

        text = "Maybe a name here."
        mock_result = self._make_result("PERSON", 0, 5, score=0.45)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = [mock_result]

        with patch.object(ps, "_get_analyzer", return_value=mock_analyzer):
            findings = ps.detect_pii(text, language="en", entity_thresholds={"PERSON": 0.3})

        assert len(findings) == 1

    def test_dedup_same_position(self):
        """Duplicate results at the same position are deduplicated."""
        import app.modules.security_guardian.presidio_service as ps

        text = "alice@example.com"
        mock_results = [
            self._make_result("EMAIL_ADDRESS", 0, 17, score=0.9),
            self._make_result("EMAIL_ADDRESS", 0, 17, score=0.9),  # exact duplicate
        ]

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = mock_results

        with patch.object(ps, "_get_analyzer", return_value=mock_analyzer):
            findings = ps.detect_pii(text)

        assert len(findings) == 1

    def test_unsupported_language_falls_back_to_en(self):
        """An unsupported language code falls back to 'en' silently."""
        import app.modules.security_guardian.presidio_service as ps

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = []

        with patch.object(ps, "_get_analyzer", return_value=mock_analyzer):
            findings = ps.detect_pii("Hello", language="xx")

        # Should not raise; analyzer was called with "en"
        mock_analyzer.analyze.assert_called_once()
        call_kwargs = mock_analyzer.analyze.call_args[1]
        assert call_kwargs.get("language") == "en"

    def test_presidio_exception_returns_empty_list(self):
        """If AnalyzerEngine.analyze raises, detect_pii returns [] without crashing."""
        import app.modules.security_guardian.presidio_service as ps

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.side_effect = RuntimeError("Presidio crash")

        with patch.object(ps, "_get_analyzer", return_value=mock_analyzer):
            findings = ps.detect_pii("Some text", language="en")

        assert findings == []


# ---------------------------------------------------------------------------
# detect_pii() — Presidio unavailable
# ---------------------------------------------------------------------------

class TestDetectPiiPresidioUnavailable:
    """detect_pii() returns [] when Presidio is not installed."""

    def test_returns_empty_when_analyzer_none(self):
        """_get_analyzer returning None causes detect_pii to return []."""
        import app.modules.security_guardian.presidio_service as ps

        with patch.object(ps, "_get_analyzer", return_value=None):
            findings = ps.detect_pii("alice@example.com phone: 555-1234")

        assert findings == []


# ---------------------------------------------------------------------------
# anonymize() — returns (anon_text, mapping) tuple
# ---------------------------------------------------------------------------

class TestAnonymizeWithPresidio:
    """anonymize() uses AnalyzerEngine + AnonymizerEngine and returns (str, dict)."""

    def test_anonymize_replaces_pii(self):
        """anonymize() with mocked engines should return redacted text."""
        import sys
        import app.modules.security_guardian.presidio_service as ps

        text = "Contact alice@example.com for help."

        mock_analyzer_result = MagicMock()
        mock_analyzer_result.entity_type = "EMAIL_ADDRESS"
        mock_analyzer_result.start = 8
        mock_analyzer_result.end = 25
        mock_analyzer_result.score = 0.9

        mock_anon_output = MagicMock()
        mock_anon_output.text = "Contact <REDACTED> for help."
        mock_anon_output.items = []

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = [mock_analyzer_result]

        mock_anonymizer_engine = MagicMock()
        mock_anonymizer_engine.anonymize.return_value = mock_anon_output

        # Mock the presidio_anonymizer.entities module so the import inside anonymize() succeeds
        mock_entities_mod = MagicMock()
        mock_entities_mod.OperatorConfig = MagicMock(return_value=MagicMock())

        with (
            patch.object(ps, "_get_analyzer", return_value=mock_analyzer),
            patch.object(ps, "_get_anonymizer", return_value=mock_anonymizer_engine),
            patch.object(ps, "_build_operator_config", return_value=MagicMock()),
            patch.dict(sys.modules, {"presidio_anonymizer.entities": mock_entities_mod}),
        ):
            anon_text, mapping = ps.anonymize(text, language="en", anonymization_mode="replace")

        assert anon_text == "Contact <REDACTED> for help."
        assert isinstance(mapping, dict)

    def test_anonymize_unavailable_returns_original(self):
        """When Presidio analyzer is None, anonymize returns original text with empty mapping."""
        import app.modules.security_guardian.presidio_service as ps

        text = "alice@example.com"

        with patch.object(ps, "_get_analyzer", return_value=None):
            anon_text, mapping = ps.anonymize(text)

        assert anon_text == text
        assert mapping == {}

    def test_anonymize_no_results_returns_original(self):
        """When analyzer finds nothing, original text is returned unchanged."""
        import app.modules.security_guardian.presidio_service as ps

        text = "Clean text with no PII."

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = []  # nothing detected

        mock_anonymizer_engine = MagicMock()

        with (
            patch.object(ps, "_get_analyzer", return_value=mock_analyzer),
            patch.object(ps, "_get_anonymizer", return_value=mock_anonymizer_engine),
        ):
            anon_text, mapping = ps.anonymize(text)

        assert anon_text == text
        assert mapping == {}

    def test_anonymize_exception_returns_original(self):
        """If anonymization raises, the original text is returned safely."""
        import app.modules.security_guardian.presidio_service as ps

        text = "Call +1-555-000-1234 now."

        mock_analyzer_result = MagicMock()
        mock_analyzer_result.entity_type = "PHONE_NUMBER"
        mock_analyzer_result.start = 5
        mock_analyzer_result.end = 19
        mock_analyzer_result.score = 0.9

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = [mock_analyzer_result]

        mock_anonymizer_engine = MagicMock()
        mock_anonymizer_engine.anonymize.side_effect = RuntimeError("Anonymizer crashed")

        mock_operator_config = MagicMock()

        with (
            patch.object(ps, "_get_analyzer", return_value=mock_analyzer),
            patch.object(ps, "_get_anonymizer", return_value=mock_anonymizer_engine),
            patch.object(ps, "_build_operator_config", return_value=mock_operator_config),
        ):
            anon_text, mapping = ps.anonymize(text)

        # Falls back to original
        assert anon_text == text
        assert mapping == {}
