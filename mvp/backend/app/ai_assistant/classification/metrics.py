"""
Prometheus Metrics for AI Classification System - Grade S++

Provides comprehensive metrics for monitoring and observability.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import structlog

logger = structlog.get_logger()


# ============================================================================
# CLASSIFICATION METRICS
# ============================================================================

# Total classifications performed
classification_total = Counter(
    'ai_router_classification_total',
    'Total number of content classifications performed',
    ['domain', 'language', 'sensitivity_level']
)

# Classification duration
classification_duration = Histogram(
    'ai_router_classification_duration_seconds',
    'Time spent classifying content',
    buckets=[0.001, 0.005, 0.010, 0.025, 0.050, 0.100, 0.250, 0.500, 1.0]
)

# Classification confidence distribution
classification_confidence = Histogram(
    'ai_router_classification_confidence',
    'Confidence score distribution',
    ['domain'],
    buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
)

# Mixed content detection
mixed_content_total = Counter(
    'ai_router_mixed_content_total',
    'Total number of mixed content detected',
    ['primary_domain', 'secondary_domain']
)

# Tone detection
tone_detection_total = Counter(
    'ai_router_tone_detection_total',
    'Total number of tone detections',
    ['tone', 'domain']
)


# ============================================================================
# MODEL SELECTION METRICS
# ============================================================================

# Model selections
model_selection_total = Counter(
    'ai_router_model_selection_total',
    'Total number of model selections',
    ['model', 'strategy', 'domain']
)

# Strategy adjustments
strategy_adjustment_total = Counter(
    'ai_router_strategy_adjustment_total',
    'Total number of strategy adjustments',
    ['from_strategy', 'to_strategy', 'reason']
)

# Fallback usage
fallback_usage_total = Counter(
    'ai_router_fallback_usage_total',
    'Total number of fallback model usage',
    ['model', 'domain']
)

# Model selection duration
model_selection_duration = Histogram(
    'ai_router_model_selection_duration_seconds',
    'Time spent selecting model',
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.010]
)


# ============================================================================
# PROMPT SELECTION METRICS
# ============================================================================

# Prompt profile usage
prompt_profile_total = Counter(
    'ai_router_prompt_profile_total',
    'Total number of prompt profile selections',
    ['profile', 'domain', 'model']
)

# Strict mode activation
strict_mode_total = Counter(
    'ai_router_strict_mode_total',
    'Total number of strict mode activations',
    ['domain', 'reason']
)

# Prompt selection duration
prompt_selection_duration = Histogram(
    'ai_router_prompt_selection_duration_seconds',
    'Time spent selecting prompt',
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.010]
)


# ============================================================================
# PERFORMANCE METRICS
# ============================================================================

# Total router processing time
router_total_duration = Histogram(
    'ai_router_total_duration_seconds',
    'Total time spent in router (classification + selection)',
    buckets=[0.001, 0.005, 0.010, 0.025, 0.050, 0.100, 0.250, 0.500, 1.0]
)

# Text length distribution
text_length_distribution = Histogram(
    'ai_router_text_length_chars',
    'Distribution of text lengths processed',
    buckets=[100, 500, 1000, 5000, 10000, 50000]
)

# Keywords matched
keywords_matched_total = Counter(
    'ai_router_keywords_matched_total',
    'Total number of keywords matched',
    ['domain', 'language']
)


# ============================================================================
# CONFIGURATION METRICS
# ============================================================================

# Config info (static)
config_info = Info(
    'ai_router_config',
    'AI Router configuration information'
)

# Config reloads
config_reload_total = Counter(
    'ai_router_config_reload_total',
    'Total number of config reloads'
)

# Active domains
active_domains = Gauge(
    'ai_router_active_domains',
    'Number of active domains in configuration'
)

# Active models
active_models = Gauge(
    'ai_router_active_models',
    'Number of active models in configuration'
)


# ============================================================================
# ERROR METRICS
# ============================================================================

# Classification errors
classification_errors_total = Counter(
    'ai_router_classification_errors_total',
    'Total number of classification errors',
    ['error_type']
)

# Model selection errors
model_selection_errors_total = Counter(
    'ai_router_model_selection_errors_total',
    'Total number of model selection errors',
    ['error_type']
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def record_classification(
    domain: str,
    language: str,
    sensitivity_level: str,
    confidence: float,
    duration_seconds: float,
    tone: str,
    is_mixed: bool,
    secondary_domain: str = None,
    keywords_count: int = 0
):
    """
    Record classification metrics.
    
    Args:
        domain: Primary domain detected
        language: Language of the text
        sensitivity_level: Sensitivity level (LOW, MEDIUM, HIGH, CRITICAL)
        confidence: Confidence score (0.0-1.0)
        duration_seconds: Time spent classifying
        tone: Detected tone
        is_mixed: Whether content is mixed
        secondary_domain: Secondary domain if mixed
        keywords_count: Number of keywords matched
    """
    try:
        # Total classifications
        classification_total.labels(
            domain=domain,
            language=language,
            sensitivity_level=sensitivity_level
        ).inc()
        
        # Duration
        classification_duration.observe(duration_seconds)
        
        # Confidence
        classification_confidence.labels(domain=domain).observe(confidence)
        
        # Tone
        tone_detection_total.labels(tone=tone, domain=domain).inc()
        
        # Mixed content
        if is_mixed and secondary_domain:
            mixed_content_total.labels(
                primary_domain=domain,
                secondary_domain=secondary_domain
            ).inc()
        
        # Keywords
        if keywords_count > 0:
            keywords_matched_total.labels(
                domain=domain,
                language=language
            ).inc(keywords_count)
        
    except Exception as e:
        logger.error(
            "metrics_recording_error",
            metric_type="classification",
            error=str(e)
        )


def record_model_selection(
    model: str,
    strategy: str,
    domain: str,
    duration_seconds: float,
    strategy_adjusted: bool = False,
    from_strategy: str = None,
    to_strategy: str = None,
    adjustment_reason: str = None,
    fallback_used: bool = False
):
    """
    Record model selection metrics.
    
    Args:
        model: Selected model
        strategy: Strategy used
        domain: Content domain
        duration_seconds: Time spent selecting
        strategy_adjusted: Whether strategy was adjusted
        from_strategy: Original strategy if adjusted
        to_strategy: New strategy if adjusted
        adjustment_reason: Reason for adjustment
        fallback_used: Whether fallback was used
    """
    try:
        # Total selections
        model_selection_total.labels(
            model=model,
            strategy=strategy,
            domain=domain
        ).inc()
        
        # Duration
        model_selection_duration.observe(duration_seconds)
        
        # Strategy adjustment
        if strategy_adjusted and from_strategy and to_strategy:
            strategy_adjustment_total.labels(
                from_strategy=from_strategy,
                to_strategy=to_strategy,
                reason=adjustment_reason or "unknown"
            ).inc()
        
        # Fallback
        if fallback_used:
            fallback_usage_total.labels(
                model=model,
                domain=domain
            ).inc()
        
    except Exception as e:
        logger.error(
            "metrics_recording_error",
            metric_type="model_selection",
            error=str(e)
        )


def record_prompt_selection(
    profile: str,
    domain: str,
    model: str,
    duration_seconds: float,
    strict_mode: bool = False,
    strict_mode_reason: str = None
):
    """
    Record prompt selection metrics.
    
    Args:
        profile: Prompt profile selected
        domain: Content domain
        model: Model being used
        duration_seconds: Time spent selecting
        strict_mode: Whether strict mode is enabled
        strict_mode_reason: Reason for strict mode
    """
    try:
        # Total selections
        prompt_profile_total.labels(
            profile=profile,
            domain=domain,
            model=model
        ).inc()
        
        # Duration
        prompt_selection_duration.observe(duration_seconds)
        
        # Strict mode
        if strict_mode:
            strict_mode_total.labels(
                domain=domain,
                reason=strict_mode_reason or "domain_policy"
            ).inc()
        
    except Exception as e:
        logger.error(
            "metrics_recording_error",
            metric_type="prompt_selection",
            error=str(e)
        )


def record_router_performance(
    total_duration_seconds: float,
    text_length: int
):
    """
    Record overall router performance metrics.
    
    Args:
        total_duration_seconds: Total time in router
        text_length: Length of text processed
    """
    try:
        router_total_duration.observe(total_duration_seconds)
        text_length_distribution.observe(text_length)
    except Exception as e:
        logger.error(
            "metrics_recording_error",
            metric_type="performance",
            error=str(e)
        )


def record_error(error_type: str, component: str):
    """
    Record error metrics.
    
    Args:
        error_type: Type of error
        component: Component where error occurred (classification, model_selection)
    """
    try:
        if component == "classification":
            classification_errors_total.labels(error_type=error_type).inc()
        elif component == "model_selection":
            model_selection_errors_total.labels(error_type=error_type).inc()
    except Exception as e:
        logger.error(
            "metrics_recording_error",
            metric_type="error",
            error=str(e)
        )


def update_config_metrics(domains_count: int, models_count: int, version: str):
    """
    Update configuration metrics.
    
    Args:
        domains_count: Number of active domains
        models_count: Number of active models
        version: Config version
    """
    try:
        active_domains.set(domains_count)
        active_models.set(models_count)
        config_info.info({
            'version': version,
            'domains_count': str(domains_count),
            'models_count': str(models_count)
        })
    except Exception as e:
        logger.error(
            "metrics_recording_error",
            metric_type="config",
            error=str(e)
        )


def record_config_reload():
    """Record config reload event."""
    try:
        config_reload_total.inc()
    except Exception as e:
        logger.error(
            "metrics_recording_error",
            metric_type="config_reload",
            error=str(e)
        )

