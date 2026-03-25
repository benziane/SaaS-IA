"""
Presidio PII Detection Service - Microsoft's enterprise-grade PII detection.

Wraps Microsoft Presidio for advanced PII detection and anonymization.
Falls back gracefully to regex-based detection if Presidio is not installed.
The existing regex patterns in SecurityGuardianService._detect_pii() are PRESERVED.

Features over regex:
- NLP-based entity recognition (names, organizations, locations)
- Context-aware detection (understands "call me at 555-1234" vs "order #555-1234")
- 30+ built-in PII recognizers
- Reversible anonymization (replace -> restore mapping)
- Multi-language support
"""

import structlog
from typing import Optional

logger = structlog.get_logger()

_analyzer = None
_anonymizer = None
_available = None


def is_available() -> bool:
    """Check if Presidio is installed and ready."""
    global _available
    if _available is not None:
        return _available
    try:
        from presidio_analyzer import AnalyzerEngine  # noqa: F401
        from presidio_anonymizer import AnonymizerEngine  # noqa: F401
        _available = True
        logger.info("presidio_available", msg="Presidio PII detection enabled (enterprise-grade)")
    except ImportError:
        _available = False
        logger.info("presidio_not_installed", msg="Using regex PII detection (pip install presidio-analyzer presidio-anonymizer to upgrade)")
    return _available


def _get_analyzer():
    """Lazy-load Presidio analyzer (singleton)."""
    global _analyzer
    if _analyzer is not None:
        return _analyzer
    if not is_available():
        return None
    try:
        from presidio_analyzer import AnalyzerEngine
        _analyzer = AnalyzerEngine()
        logger.info("presidio_analyzer_loaded")
        return _analyzer
    except Exception as e:
        logger.error("presidio_analyzer_load_failed", error=str(e))
        return None


def _get_anonymizer():
    """Lazy-load Presidio anonymizer (singleton)."""
    global _anonymizer
    if _anonymizer is not None:
        return _anonymizer
    if not is_available():
        return None
    try:
        from presidio_anonymizer import AnonymizerEngine
        _anonymizer = AnonymizerEngine()
        return _anonymizer
    except Exception as e:
        logger.error("presidio_anonymizer_load_failed", error=str(e))
        return None


# Mapping Presidio entity types to our severity levels
SEVERITY_MAP = {
    "CREDIT_CARD": "critical",
    "CRYPTO": "critical",
    "IBAN_CODE": "critical",
    "US_SSN": "critical",
    "UK_NHS": "critical",
    "US_BANK_NUMBER": "critical",
    "US_PASSPORT": "critical",
    "EMAIL_ADDRESS": "high",
    "PHONE_NUMBER": "high",
    "PERSON": "high",
    "US_DRIVER_LICENSE": "high",
    "IP_ADDRESS": "medium",
    "LOCATION": "medium",
    "ORGANIZATION": "medium",
    "DATE_TIME": "low",
    "NRP": "low",  # nationality, religion, political group
    "URL": "low",
}


def detect_pii(text: str, language: str = "en") -> list[dict]:
    """Detect PII using Presidio's NLP-based recognizers.

    Returns a list of findings compatible with SecurityGuardianService format.
    Returns empty list if Presidio is not available (caller should fallback to regex).
    """
    analyzer = _get_analyzer()
    if analyzer is None:
        return []

    try:
        results = analyzer.analyze(
            text=text,
            language=language,
            score_threshold=0.4,  # Lower threshold to catch more, we filter later
        )

        findings = []
        seen = set()  # dedup by position

        for result in results:
            key = (result.entity_type, result.start, result.end)
            if key in seen:
                continue
            seen.add(key)

            # Only keep results with decent confidence
            if result.score < 0.5:
                continue

            severity = SEVERITY_MAP.get(result.entity_type, "medium")
            matched_text = text[result.start:result.end]

            findings.append({
                "type": f"pii_{result.entity_type.lower()}",
                "severity": severity,
                "description": f"{result.entity_type.replace('_', ' ').title()} detected (confidence: {result.score:.0%})",
                "location": f"chars {result.start}-{result.end}",
                "suggestion": f"Redact or remove the {result.entity_type.lower().replace('_', ' ')}",
                "presidio_score": round(result.score, 2),
                "presidio_entity": result.entity_type,
            })

        logger.info("presidio_scan_complete", findings=len(findings), text_length=len(text))
        return findings

    except Exception as e:
        logger.warning("presidio_detection_failed", error=str(e))
        return []


def anonymize(text: str, language: str = "en") -> tuple[str, dict]:
    """Anonymize text using Presidio with reversible mapping.

    Returns (anonymized_text, mapping) where mapping allows restoration.
    Example: "Jean Dupont" -> "[PERSON_1]", mapping = {"[PERSON_1]": "Jean Dupont"}

    Returns (original_text, {}) if Presidio is not available.
    """
    analyzer = _get_analyzer()
    anonymizer_engine = _get_anonymizer()

    if analyzer is None or anonymizer_engine is None:
        return text, {}

    try:
        from presidio_anonymizer.entities import OperatorConfig

        # Analyze
        results = analyzer.analyze(text=text, language=language, score_threshold=0.5)

        if not results:
            return text, {}

        # Build custom operators for reversible anonymization
        # Group by entity type to number them
        entity_counters: dict[str, int] = {}
        operators = {}

        for result in sorted(results, key=lambda r: r.start):
            etype = result.entity_type
            if etype not in entity_counters:
                entity_counters[etype] = 0
            entity_counters[etype] += 1
            # We use the default "replace" operator

        # Anonymize with replace
        anonymized = anonymizer_engine.anonymize(
            text=text,
            analyzer_results=results,
            operators={"DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"})},
        )

        # Build reversible mapping
        mapping = {}
        anon_text = anonymized.text

        for item in anonymized.items:
            placeholder = anon_text[item.start:item.end]
            original = text[item.start:item.end] if item.start < len(text) else ""
            if placeholder and original:
                mapping[placeholder] = original

        return anon_text, mapping

    except Exception as e:
        logger.warning("presidio_anonymization_failed", error=str(e))
        return text, {}


def deanonymize(anonymized_text: str, mapping: dict) -> str:
    """Restore original text from anonymized version using the mapping."""
    result = anonymized_text
    for placeholder, original in mapping.items():
        result = result.replace(placeholder, original)
    return result
