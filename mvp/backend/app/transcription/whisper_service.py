"""
Local transcription using faster-whisper.

Free, unlimited, runs locally without any API key.
Uses CTranslate2 backend for fast inference.
"""

import os
from typing import Optional

import structlog

logger = structlog.get_logger()

# Cache the model to avoid reloading
_model = None
_model_size = None


def _get_model(model_size: str = "base"):
    """Get or create the Whisper model (cached)."""
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
        logger.error("whisper_model_load_failed", error=str(e))
        return None


async def transcribe_with_whisper(
    file_path: str,
    language: str = "auto",
    model_size: str = "base",
) -> Optional[dict]:
    """
    Transcribe an audio file using faster-whisper (local, free).

    Models available: tiny, base, small, medium, large-v3
    - tiny: fastest, lowest quality (~32MB)
    - base: good balance (~74MB)
    - small: better quality (~244MB)
    - medium: high quality (~769MB)
    - large-v3: best quality (~1.5GB)
    """
    if not os.path.exists(file_path):
        return None

    model = _get_model(model_size)
    if model is None:
        return None

    try:
        import asyncio

        # Run in thread pool to not block async loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: _do_transcribe(model, file_path, language),
        )

        return result

    except Exception as e:
        logger.error("whisper_transcription_failed", file_path=file_path, error=str(e))
        return None


def _do_transcribe(model, file_path: str, language: str) -> dict:
    """Synchronous transcription (runs in thread pool)."""
    kwargs = {
        "beam_size": 5,
        "word_timestamps": True,
        "vad_filter": True,
    }

    if language != "auto":
        kwargs["language"] = language

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
    }
