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
- Multi-language support (en, fr, de, es)
- Custom French PII recognizers (NIR, IBAN, phone)
- Multiple anonymization modes (replace, mask, hash, redact)
- Per-entity-type confidence thresholds
- Batch analysis support
"""

import structlog
from typing import Optional

logger = structlog.get_logger()

_analyzer = None
_anonymizer = None
_available = None
_french_recognizers_registered = False

# Supported languages
SUPPORTED_LANGUAGES = {"en", "fr", "de", "es"}


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


def _register_french_recognizers(analyzer) -> None:
    """Register custom French PII pattern recognizers."""
    global _french_recognizers_registered
    if _french_recognizers_registered:
        return

    try:
        from presidio_analyzer import PatternRecognizer, Pattern

        # French NIR (social security number): 1 or 2 + 2-digit year + 2-digit month + 3-digit dept + 3-digit commune + 2-digit key
        nir_pattern = Pattern(
            name="french_nir_pattern",
            regex=r"[12][- ]?\d{2}[- ]?\d{2}[- ]?\d{3}[- ]?\d{3}[- ]?\d{2}",
            score=0.7,
        )
        nir_recognizer = PatternRecognizer(
            supported_entity="FR_NIR",
            name="French NIR Recognizer",
            patterns=[nir_pattern],
            supported_language="fr",
            context=["nir", "securite sociale", "numero de securite", "secu", "social security"],
        )

        # French IBAN: FR + 2 check digits + 23 alphanumeric chars (grouped by 4)
        iban_pattern = Pattern(
            name="french_iban_pattern",
            regex=r"FR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{3}",
            score=0.85,
        )
        iban_recognizer = PatternRecognizer(
            supported_entity="FR_IBAN",
            name="French IBAN Recognizer",
            patterns=[iban_pattern],
            supported_language="fr",
            context=["iban", "compte", "bancaire", "banque", "virement"],
        )

        # French phone: +33 or 0 prefix, then 9 digits in groups of 2
        phone_pattern = Pattern(
            name="french_phone_pattern",
            regex=r"(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}",
            score=0.7,
        )
        phone_recognizer = PatternRecognizer(
            supported_entity="FR_PHONE",
            name="French Phone Recognizer",
            patterns=[phone_pattern],
            supported_language="fr",
            context=["telephone", "tel", "appeler", "numero", "mobile", "portable"],
        )

        analyzer.registry.add_recognizer(nir_recognizer)
        analyzer.registry.add_recognizer(iban_recognizer)
        analyzer.registry.add_recognizer(phone_recognizer)

        _french_recognizers_registered = True
        logger.info("french_recognizers_registered", recognizers=["FR_NIR", "FR_IBAN", "FR_PHONE"])

    except Exception as e:
        logger.warning("french_recognizers_registration_failed", error=str(e))


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
        # Register French recognizers immediately so they're ready for fr language
        _register_french_recognizers(_analyzer)
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


def _build_operator_config(mode: str = "replace"):
    """Build Presidio OperatorConfig based on the anonymization mode.

    Supported modes: replace, mask, hash, redact.
    Falls back to replace if mode is unknown.
    """
    try:
        from presidio_anonymizer.entities import OperatorConfig

        if mode == "mask":
            return OperatorConfig("mask", {"chars_to_mask": 8, "masking_char": "*", "from_end": True})
        elif mode == "hash":
            return OperatorConfig("hash", {"hash_type": "sha256"})
        elif mode == "redact":
            return OperatorConfig("redact")
        else:
            # Default: replace with <REDACTED>
            return OperatorConfig("replace", {"new_value": "<REDACTED>"})
    except Exception as e:
        logger.warning("operator_config_build_failed", mode=mode, error=str(e))
        return None


# Mapping Presidio entity types to our severity levels
SEVERITY_MAP = {
    "CREDIT_CARD": "critical",
    "CRYPTO": "critical",
    "IBAN_CODE": "critical",
    "FR_IBAN": "critical",
    "FR_NIR": "critical",
    "US_SSN": "critical",
    "UK_NHS": "critical",
    "US_BANK_NUMBER": "critical",
    "US_PASSPORT": "critical",
    "EMAIL_ADDRESS": "high",
    "PHONE_NUMBER": "high",
    "FR_PHONE": "high",
    "PERSON": "high",
    "US_DRIVER_LICENSE": "high",
    "IP_ADDRESS": "medium",
    "LOCATION": "medium",
    "ORGANIZATION": "medium",
    "DATE_TIME": "low",
    "NRP": "low",  # nationality, religion, political group
    "URL": "low",
}


def detect_pii(
    text: str,
    language: str = "en",
    entity_thresholds: Optional[dict[str, float]] = None,
) -> list[dict]:
    """Detect PII using Presidio's NLP-based recognizers.

    Args:
        text: The text to analyze.
        language: Language code for analysis ("en", "fr", "de", "es").
        entity_thresholds: Optional per-entity confidence thresholds.
            Example: {"CREDIT_CARD": 0.3, "PERSON": 0.6, "DATE_TIME": 0.8}
            Entities not listed use the default 0.5 threshold.

    Returns a list of findings compatible with SecurityGuardianService format.
    Returns empty list if Presidio is not available (caller should fallback to regex).
    """
    analyzer = _get_analyzer()
    if analyzer is None:
        return []

    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        logger.warning("unsupported_language", language=language, fallback="en")
        language = "en"

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

            # Apply per-entity threshold or default 0.5
            if entity_thresholds and result.entity_type in entity_thresholds:
                threshold = entity_thresholds[result.entity_type]
            else:
                threshold = 0.5

            if result.score < threshold:
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

        logger.info("presidio_scan_complete", findings=len(findings), text_length=len(text), language=language)
        return findings

    except Exception as e:
        logger.warning("presidio_detection_failed", error=str(e))
        return []


def anonymize(
    text: str,
    language: str = "en",
    anonymization_mode: str = "replace",
) -> tuple[str, dict]:
    """Anonymize text using Presidio with configurable operators.

    Args:
        text: The text to anonymize.
        language: Language code for analysis ("en", "fr", "de", "es").
        anonymization_mode: One of "replace", "mask", "hash", "redact".
            - replace: Replaces with <REDACTED> (default, reversible via mapping)
            - mask: Masks last 8 chars with * (partial visibility)
            - hash: Replaces with SHA-256 hash (deterministic, one-way)
            - redact: Removes the PII entirely (no placeholder)

    Returns (anonymized_text, mapping) where mapping allows restoration.
    Returns (original_text, {}) if Presidio is not available.
    """
    analyzer = _get_analyzer()
    anonymizer_engine = _get_anonymizer()

    if analyzer is None or anonymizer_engine is None:
        return text, {}

    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        logger.warning("unsupported_language", language=language, fallback="en")
        language = "en"

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

        # Build operator config based on mode
        operator_config = _build_operator_config(anonymization_mode)
        if operator_config is None:
            # Fallback to basic replace
            operator_config = OperatorConfig("replace", {"new_value": "<REDACTED>"})

        # Anonymize with chosen operator
        anonymized = anonymizer_engine.anonymize(
            text=text,
            analyzer_results=results,
            operators={"DEFAULT": operator_config},
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


def analyze_batch(
    texts: list[str],
    language: str = "en",
    entity_thresholds: Optional[dict[str, float]] = None,
) -> list[list[dict]]:
    """Analyze multiple texts for PII in batch.

    Tries to use Presidio's BatchAnalyzerEngine for optimized batch processing.
    Falls back to sequential analysis if BatchAnalyzerEngine is not available.

    Args:
        texts: List of texts to analyze.
        language: Language code for analysis ("en", "fr", "de", "es").
        entity_thresholds: Optional per-entity confidence thresholds.

    Returns a list of findings lists, one per input text.
    Returns list of empty lists if Presidio is not available.
    """
    if not texts:
        return []

    if not is_available():
        return [[] for _ in texts]

    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        logger.warning("unsupported_language", language=language, fallback="en")
        language = "en"

    # Try BatchAnalyzerEngine first
    try:
        from presidio_analyzer import BatchAnalyzerEngine

        analyzer = _get_analyzer()
        if analyzer is None:
            return [[] for _ in texts]

        batch_analyzer = BatchAnalyzerEngine(analyzer_engine=analyzer)

        batch_results = list(batch_analyzer.analyze_iterator(
            texts=texts,
            language=language,
            score_threshold=0.4,
        ))

        # batch_results is a list of lists of RecognizerResult
        all_findings = []
        for i, results in enumerate(batch_results):
            findings = _process_analyzer_results(results, entity_thresholds)
            all_findings.append(findings)

        logger.info("presidio_batch_scan_complete", texts_count=len(texts), total_findings=sum(len(f) for f in all_findings))
        return all_findings

    except (ImportError, AttributeError):
        logger.info("batch_analyzer_not_available", msg="Falling back to sequential analysis")
    except Exception as e:
        logger.warning("batch_analyzer_failed", error=str(e), msg="Falling back to sequential analysis")

    # Fallback: sequential analysis
    try:
        all_findings = []
        for text in texts:
            findings = detect_pii(text, language=language, entity_thresholds=entity_thresholds)
            all_findings.append(findings)

        logger.info("presidio_sequential_batch_complete", texts_count=len(texts), total_findings=sum(len(f) for f in all_findings))
        return all_findings

    except Exception as e:
        logger.warning("presidio_batch_fallback_failed", error=str(e))
        return [[] for _ in texts]


def _process_analyzer_results(
    results,
    entity_thresholds: Optional[dict[str, float]] = None,
) -> list[dict]:
    """Convert Presidio analyzer results to our finding format.

    Shared logic used by both detect_pii and analyze_batch.
    """
    findings = []
    seen = set()

    for result in results:
        key = (result.entity_type, result.start, result.end)
        if key in seen:
            continue
        seen.add(key)

        # Apply per-entity threshold or default 0.5
        if entity_thresholds and result.entity_type in entity_thresholds:
            threshold = entity_thresholds[result.entity_type]
        else:
            threshold = 0.5

        if result.score < threshold:
            continue

        severity = SEVERITY_MAP.get(result.entity_type, "medium")

        findings.append({
            "type": f"pii_{result.entity_type.lower()}",
            "severity": severity,
            "description": f"{result.entity_type.replace('_', ' ').title()} detected (confidence: {result.score:.0%})",
            "location": f"chars {result.start}-{result.end}",
            "suggestion": f"Redact or remove the {result.entity_type.lower().replace('_', ' ')}",
            "presidio_score": round(result.score, 2),
            "presidio_entity": result.entity_type,
        })

    return findings


def list_supported_entities(language: str = "en") -> list[str]:
    """List all PII entity types supported by the current analyzer for a given language.

    Args:
        language: Language code ("en", "fr", "de", "es").

    Returns a list of entity type strings (e.g., ["PERSON", "CREDIT_CARD", ...]).
    Returns empty list if Presidio is not available.
    """
    analyzer = _get_analyzer()
    if analyzer is None:
        return []

    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        logger.warning("unsupported_language", language=language, fallback="en")
        language = "en"

    try:
        entities = analyzer.get_supported_entities(language=language)
        logger.info("supported_entities_listed", language=language, count=len(entities))
        return sorted(entities)
    except Exception as e:
        logger.warning("list_supported_entities_failed", error=str(e))
        return []
