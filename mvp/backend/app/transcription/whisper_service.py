"""
Local transcription using faster-whisper.

Free, unlimited, runs locally without any API key.
Uses CTranslate2 backend for fast inference.
Supports standard, turbo, and distil-whisper model variants.
"""

import os
from typing import Optional

import structlog

logger = structlog.get_logger()

# Cache the model to avoid reloading
_model = None
_model_size = None

# Supported model variants (standard + distil + turbo)
SUPPORTED_MODELS = [
    "tiny", "tiny.en",
    "base", "base.en",
    "small", "small.en",
    "medium", "medium.en",
    "large-v1", "large-v2", "large-v3",
    "large-v3-turbo",
    "distil-large-v3",
    "distil-medium.en",
    "distil-small.en",
]


def _get_model(model_size: str = "base"):
    """Get or create the Whisper model (cached).

    Args:
        model_size: Model identifier. Supports standard sizes (tiny, base, small,
            medium, large-v3), turbo variants (large-v3-turbo), and distil models
            (distil-large-v3, distil-medium.en, distil-small.en).
    """
    global _model, _model_size

    if _model is not None and _model_size == model_size:
        return _model

    try:
        from faster_whisper import WhisperModel

        # Use CPU by default, GPU if available
        device = "cpu"
        compute_type = "int8"

        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
                compute_type = "float16"
        except ImportError:
            pass

        logger.info("whisper_loading_model", model_size=model_size, device=device)
        _model = WhisperModel(model_size, device=device, compute_type=compute_type)
        _model_size = model_size
        logger.info("whisper_model_loaded", model_size=model_size, device=device)

        return _model

    except ImportError:
        logger.warning("faster_whisper_not_installed")
        return None
    except Exception as e:
        logger.error("whisper_model_load_failed", error=str(e), model_size=model_size)
        return None


async def transcribe_with_whisper(
    file_path: str,
    language: str = "auto",
    model_size: str = "base",
    task: str = "transcribe",
    initial_prompt: Optional[str] = None,
    hotwords: Optional[str] = None,
    hallucination_silence_threshold: Optional[float] = None,
    repetition_penalty: float = 1.0,
    log_progress: bool = False,
    clip_timestamps: Optional[list[float]] = None,
) -> Optional[dict]:
    """
    Transcribe an audio file using faster-whisper (local, free).

    Models available: tiny, base, small, medium, large-v3, large-v3-turbo,
    distil-large-v3, distil-medium.en
    - tiny: fastest, lowest quality (~32MB)
    - base: good balance (~74MB)
    - small: better quality (~244MB)
    - medium: high quality (~769MB)
    - large-v3: best quality (~1.5GB)
    - large-v3-turbo: near large-v3 quality, much faster
    - distil-large-v3: distilled, ~6x faster than large-v3

    Args:
        file_path: Path to audio file
        language: Language code ("auto" for auto-detect)
        model_size: Whisper model variant
        task: "transcribe" (default) or "translate" (auto-translates to English)
        initial_prompt: Optional text to condition the model (improves domain accuracy)
        hotwords: Optional comma-separated hotwords to boost recognition
        hallucination_silence_threshold: Skip silent segments longer than this (seconds)
        repetition_penalty: Penalty for repeated tokens (1.0 = no penalty)
        log_progress: Log transcription progress to console
        clip_timestamps: List of timestamps (seconds) to transcribe specific ranges
    """
    if not os.path.exists(file_path):
        return None

    model = _get_model(model_size)
    if model is None:
        return None

    try:
        import asyncio

        # Run in thread pool to not block async loop
        result = await asyncio.to_thread(
            _do_transcribe,
            model,
            file_path,
            language,
            task=task,
            initial_prompt=initial_prompt,
            hotwords=hotwords,
            hallucination_silence_threshold=hallucination_silence_threshold,
            repetition_penalty=repetition_penalty,
            log_progress=log_progress,
            clip_timestamps=clip_timestamps,
        )

        return result

    except Exception as e:
        logger.error("whisper_transcription_failed", file_path=file_path, error=str(e))
        return None


def _do_transcribe(
    model,
    file_path: str,
    language: str,
    *,
    task: str = "transcribe",
    initial_prompt: Optional[str] = None,
    hotwords: Optional[str] = None,
    hallucination_silence_threshold: Optional[float] = None,
    repetition_penalty: float = 1.0,
    log_progress: bool = False,
    clip_timestamps: Optional[list[float]] = None,
) -> dict:
    """Synchronous transcription (runs in thread pool)."""
    kwargs = {
        "beam_size": 5,
        "word_timestamps": True,
        "vad_filter": True,
        "task": task,
        "repetition_penalty": repetition_penalty,
        "log_progress": log_progress,
    }

    if language != "auto":
        kwargs["language"] = language

    if initial_prompt is not None:
        kwargs["initial_prompt"] = initial_prompt
    if hotwords is not None:
        kwargs["hotwords"] = hotwords
    if hallucination_silence_threshold is not None:
        kwargs["hallucination_silence_threshold"] = hallucination_silence_threshold
    if clip_timestamps is not None:
        kwargs["clip_timestamps"] = clip_timestamps

    segments_gen, info = model.transcribe(file_path, **kwargs)

    segments = []
    full_text_parts = []

    for segment in segments_gen:
        segments.append({
            "text": segment.text.strip(),
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "confidence": round(segment.avg_log_prob, 3) if hasattr(segment, 'avg_log_prob') else None,
        })
        full_text_parts.append(segment.text.strip())

    full_text = " ".join(full_text_parts)
    duration = round(info.duration, 0) if info.duration else 0

    return {
        "text": full_text,
        "segments": segments,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration_seconds": int(duration),
        "confidence": round(info.language_probability, 3),
        "provider": "whisper",
        "model_size": model.model_size_or_path if hasattr(model, 'model_size_or_path') else "base",
        "task": task,
    }


async def detect_language_with_whisper(
    file_path: str,
    model_size: str = "base",
) -> Optional[dict]:
    """Detect the language of an audio file without full transcription.

    Args:
        file_path: Path to audio file
        model_size: Whisper model size to use for detection

    Returns:
        dict with language code and probability, or None if unavailable.
    """
    if not os.path.exists(file_path):
        return None

    model = _get_model(model_size)
    if model is None:
        return None

    try:
        import asyncio

        def _detect_sync():
            language_info = model.detect_language(file_path)
            if isinstance(language_info, list) and len(language_info) > 0:
                best_lang, best_prob = language_info[0]
                return {
                    "language": best_lang,
                    "probability": round(best_prob, 4),
                    "all_languages": [
                        {"language": lang, "probability": round(prob, 4)}
                        for lang, prob in language_info[:10]
                    ],
                }
            return None

        result = await asyncio.to_thread(_detect_sync)
        if result:
            logger.info(
                "whisper_language_detected",
                language=result["language"],
                probability=result["probability"],
            )
        return result

    except Exception as e:
        logger.error("whisper_language_detection_failed", error=str(e), file_path=file_path)
        return None
