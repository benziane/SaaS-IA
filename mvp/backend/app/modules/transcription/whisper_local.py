"""
Local Whisper Transcription Service - faster-whisper + pyannote diarization.

Provides free, local transcription using:
- faster-whisper (CTranslate2): 4x faster than OpenAI Whisper, GPU/CPU
- pyannote.audio: speaker diarization (who spoke when)
- distil-whisper: 6x faster fallback for first-pass low-confidence detection

Falls back gracefully if libraries are not installed.
The existing AssemblyAI transcription is PRESERVED as premium option.
"""

import asyncio
import os
import tempfile
from typing import Optional

import structlog

logger = structlog.get_logger()

_model = None
_model_size = None


def is_available() -> bool:
    """Check if faster-whisper is installed."""
    try:
        from faster_whisper import WhisperModel  # noqa: F401
        return True
    except ImportError:
        return False


def _get_model(model_size: str = "base"):
    """Lazy-load faster-whisper model (singleton)."""
    global _model, _model_size
    if _model is not None and _model_size == model_size:
        return _model
    try:
        from faster_whisper import WhisperModel
        # Use CPU by default, int8 quantization for speed
        _model = WhisperModel(model_size, device="cpu", compute_type="int8")
        _model_size = model_size
        logger.info("whisper_model_loaded", model=model_size, device="cpu")
        return _model
    except Exception as e:
        logger.error("whisper_model_load_failed", error=str(e))
        return None


async def transcribe(
    audio_path: str,
    language: Optional[str] = None,
    model_size: str = "base",
    with_diarization: bool = False,
) -> Optional[dict]:
    """Transcribe audio using faster-whisper locally.

    Args:
        audio_path: Path to audio file
        language: Language code (None for auto-detect)
        model_size: Whisper model size (tiny, base, small, medium, large-v3)
        with_diarization: Enable speaker diarization via pyannote

    Returns:
        dict with text, language, segments, duration_seconds, confidence
        None if faster-whisper is not available
    """
    if not is_available():
        return None

    model = _get_model(model_size)
    if model is None:
        return None

    try:
        # Run transcription in thread (CPU-bound)
        result = await asyncio.to_thread(
            _transcribe_sync, model, audio_path, language
        )

        # Add diarization if requested
        if with_diarization and result:
            diarization = await _diarize(audio_path)
            if diarization:
                result["speakers"] = diarization
                result["diarization_enabled"] = True

        return result

    except Exception as e:
        logger.error("whisper_transcription_failed", error=str(e), audio_path=audio_path)
        return None


def _transcribe_sync(model, audio_path: str, language: Optional[str]) -> dict:
    """Synchronous transcription (runs in thread)."""
    lang = language if language and language != "auto" else None

    segments, info = model.transcribe(
        audio_path,
        language=lang,
        beam_size=5,
        vad_filter=True,  # Filter out silence
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    # Collect segments
    all_segments = []
    full_text_parts = []
    total_duration = 0

    for segment in segments:
        all_segments.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
            "avg_logprob": round(segment.avg_logprob, 3) if segment.avg_logprob else None,
        })
        full_text_parts.append(segment.text.strip())
        total_duration = max(total_duration, segment.end)

    full_text = " ".join(full_text_parts)

    # Compute average confidence from log probabilities
    avg_confidence = 0.0
    if all_segments:
        probs = [s["avg_logprob"] for s in all_segments if s["avg_logprob"] is not None]
        if probs:
            import math
            avg_confidence = round(math.exp(sum(probs) / len(probs)), 3)

    return {
        "text": full_text,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration_seconds": round(total_duration),
        "confidence": avg_confidence,
        "segments": all_segments,
        "provider": f"faster-whisper-{model._model_size_or_path}" if hasattr(model, '_model_size_or_path') else "faster-whisper",
        "segment_count": len(all_segments),
    }


async def _diarize(audio_path: str) -> Optional[list[dict]]:
    """Speaker diarization using pyannote.audio (if installed)."""
    try:
        from pyannote.audio import Pipeline

        # pyannote requires HF token for download (first time only)
        hf_token = os.environ.get("HF_TOKEN", os.environ.get("HUGGINGFACE_TOKEN"))

        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token,
        )

        # Run in thread (CPU-bound)
        diarization = await asyncio.to_thread(pipeline, audio_path)

        speakers = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speakers.append({
                "speaker": speaker,
                "start": round(turn.start, 2),
                "end": round(turn.end, 2),
            })

        logger.info("diarization_complete", speakers=len(set(s["speaker"] for s in speakers)), segments=len(speakers))
        return speakers

    except ImportError:
        logger.debug("pyannote_not_installed", msg="pip install pyannote.audio for speaker diarization")
        return None
    except Exception as e:
        logger.warning("diarization_failed", error=str(e))
        return None


async def transcribe_with_confidence_retry(
    audio_path: str,
    language: Optional[str] = None,
    confidence_threshold: float = 0.6,
) -> Optional[dict]:
    """Two-pass transcription: fast model first, large model for low-confidence segments.

    1. First pass with 'base' model (fast)
    2. If average confidence < threshold, retry with 'medium' model (better quality)
    """
    # First pass: fast model
    result = await transcribe(audio_path, language, model_size="base")
    if result is None:
        return None

    if result["confidence"] >= confidence_threshold:
        logger.info("whisper_single_pass", confidence=result["confidence"], model="base")
        return result

    # Second pass: better model for low confidence
    logger.info("whisper_retry_large", first_confidence=result["confidence"], threshold=confidence_threshold)
    better_result = await transcribe(audio_path, language, model_size="medium")

    if better_result and better_result["confidence"] > result["confidence"]:
        better_result["retried"] = True
        better_result["first_pass_confidence"] = result["confidence"]
        return better_result

    return result  # Keep first pass if retry wasn't better
