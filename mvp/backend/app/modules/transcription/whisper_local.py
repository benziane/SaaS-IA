"""
Local Whisper Transcription Service - faster-whisper + pyannote diarization.

Provides free, local transcription using:
- faster-whisper (CTranslate2): 4x faster than OpenAI Whisper, GPU/CPU
- BatchedInferencePipeline: up to 8x throughput for multi-file batch transcription
- pyannote.audio: speaker diarization (who spoke when)
- distil-whisper / turbo variants: faster models for first-pass or low-latency use

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


def is_available() -> bool:
    """Check if faster-whisper is installed."""
    try:
        from faster_whisper import WhisperModel  # noqa: F401
        return True
    except ImportError:
        return False


def _has_batched_pipeline() -> bool:
    """Check if BatchedInferencePipeline is available (faster-whisper >= 1.0)."""
    try:
        from faster_whisper import BatchedInferencePipeline  # noqa: F401
        return True
    except ImportError:
        return False


def _get_model(model_size: str = "base"):
    """Lazy-load faster-whisper model (singleton).

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

        # Auto-detect GPU
        device = "cpu"
        compute_type = "int8"
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
                compute_type = "float16"
        except ImportError:
            pass

        _model = WhisperModel(model_size, device=device, compute_type=compute_type)
        _model_size = model_size
        logger.info("whisper_model_loaded", model=model_size, device=device, compute_type=compute_type)
        return _model
    except Exception as e:
        logger.error("whisper_model_load_failed", error=str(e), model=model_size)
        return None


async def transcribe(
    audio_path: str,
    language: Optional[str] = None,
    model_size: str = "base",
    with_diarization: bool = False,
    task: str = "transcribe",
    initial_prompt: Optional[str] = None,
    hotwords: Optional[str] = None,
    hallucination_silence_threshold: Optional[float] = None,
    repetition_penalty: float = 1.0,
    log_progress: bool = False,
    clip_timestamps: Optional[list[float]] = None,
) -> Optional[dict]:
    """Transcribe audio using faster-whisper locally.

    Args:
        audio_path: Path to audio file
        language: Language code (None for auto-detect)
        model_size: Whisper model size (tiny, base, small, medium, large-v3,
            large-v3-turbo, distil-large-v3, distil-medium.en)
        with_diarization: Enable speaker diarization via pyannote
        task: "transcribe" (default) or "translate" (auto-translates to English)
        initial_prompt: Optional text to condition the model (improves domain accuracy)
        hotwords: Optional comma-separated hotwords to boost recognition
        hallucination_silence_threshold: Skip silent segments longer than this (seconds)
        repetition_penalty: Penalty for repeated tokens (1.0 = no penalty)
        log_progress: Log transcription progress to console
        clip_timestamps: List of timestamps (seconds) to transcribe specific ranges

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
            _transcribe_sync,
            model,
            audio_path,
            language,
            task=task,
            initial_prompt=initial_prompt,
            hotwords=hotwords,
            hallucination_silence_threshold=hallucination_silence_threshold,
            repetition_penalty=repetition_penalty,
            log_progress=log_progress,
            clip_timestamps=clip_timestamps,
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


def _transcribe_sync(
    model,
    audio_path: str,
    language: Optional[str],
    *,
    task: str = "transcribe",
    initial_prompt: Optional[str] = None,
    hotwords: Optional[str] = None,
    hallucination_silence_threshold: Optional[float] = None,
    repetition_penalty: float = 1.0,
    log_progress: bool = False,
    clip_timestamps: Optional[list[float]] = None,
) -> dict:
    """Synchronous transcription (runs in thread)."""
    lang = language if language and language != "auto" else None

    kwargs = {
        "language": lang,
        "beam_size": 5,
        "vad_filter": True,
        "vad_parameters": dict(min_silence_duration_ms=500),
        "task": task,
        "repetition_penalty": repetition_penalty,
        "log_progress": log_progress,
    }

    if initial_prompt is not None:
        kwargs["initial_prompt"] = initial_prompt
    if hotwords is not None:
        kwargs["hotwords"] = hotwords
    if hallucination_silence_threshold is not None:
        kwargs["hallucination_silence_threshold"] = hallucination_silence_threshold
    if clip_timestamps is not None:
        kwargs["clip_timestamps"] = clip_timestamps

    segments, info = model.transcribe(audio_path, **kwargs)

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
        "task": task,
    }


async def detect_language(
    audio_path: str,
    model_size: str = "base",
) -> Optional[dict]:
    """Detect the language of an audio file without full transcription.

    Args:
        audio_path: Path to audio file
        model_size: Whisper model size to use for detection

    Returns:
        dict with language code and probability, or None if unavailable.
        Example: {"language": "fr", "probability": 0.95}
    """
    if not is_available():
        return None

    model = _get_model(model_size)
    if model is None:
        return None

    try:
        def _detect_sync():
            language_info = model.detect_language(audio_path)
            # detect_language returns list of (language, probability) tuples
            # sorted by probability descending
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
        logger.error("whisper_language_detection_failed", error=str(e), audio_path=audio_path)
        return None


async def transcribe_batch(
    audio_paths: list[str],
    language: Optional[str] = None,
    model_size: str = "base",
    task: str = "transcribe",
    initial_prompt: Optional[str] = None,
    hotwords: Optional[str] = None,
    batch_size: int = 8,
) -> list[Optional[dict]]:
    """Batch transcription using BatchedInferencePipeline for up to 8x throughput.

    If BatchedInferencePipeline is not available (older faster-whisper), falls back
    to sequential transcription automatically.

    Args:
        audio_paths: List of paths to audio files
        language: Language code (None for auto-detect)
        model_size: Whisper model size
        task: "transcribe" or "translate"
        initial_prompt: Optional conditioning text
        hotwords: Optional comma-separated hotwords
        batch_size: Max files to process in parallel (default 8)

    Returns:
        List of result dicts (same order as audio_paths), None for failed items
    """
    if not audio_paths:
        return []

    if not is_available():
        logger.warning("whisper_batch_unavailable", reason="faster-whisper not installed")
        return [None] * len(audio_paths)

    model = _get_model(model_size)
    if model is None:
        return [None] * len(audio_paths)

    # Try BatchedInferencePipeline for optimized throughput
    if _has_batched_pipeline():
        try:
            result = await asyncio.to_thread(
                _transcribe_batch_sync,
                model,
                audio_paths,
                language,
                task=task,
                initial_prompt=initial_prompt,
                hotwords=hotwords,
                batch_size=batch_size,
            )
            return result
        except Exception as e:
            logger.warning(
                "whisper_batch_pipeline_failed",
                error=str(e),
                msg="falling back to sequential transcription",
            )

    # Fallback: sequential transcription
    logger.info("whisper_batch_sequential_fallback", file_count=len(audio_paths))
    results = []
    for path in audio_paths:
        result = await transcribe(
            audio_path=path,
            language=language,
            model_size=model_size,
            task=task,
            initial_prompt=initial_prompt,
            hotwords=hotwords,
        )
        results.append(result)
    return results


def _transcribe_batch_sync(
    model,
    audio_paths: list[str],
    language: Optional[str],
    *,
    task: str = "transcribe",
    initial_prompt: Optional[str] = None,
    hotwords: Optional[str] = None,
    batch_size: int = 8,
) -> list[Optional[dict]]:
    """Synchronous batch transcription using BatchedInferencePipeline (runs in thread)."""
    from faster_whisper import BatchedInferencePipeline

    batched_model = BatchedInferencePipeline(model=model)
    lang = language if language and language != "auto" else None

    results = []
    for audio_path in audio_paths:
        try:
            kwargs = {
                "language": lang,
                "beam_size": 5,
                "vad_filter": True,
                "vad_parameters": dict(min_silence_duration_ms=500),
                "task": task,
                "batch_size": batch_size,
            }

            if initial_prompt is not None:
                kwargs["initial_prompt"] = initial_prompt
            if hotwords is not None:
                kwargs["hotwords"] = hotwords

            segments, info = batched_model.transcribe(audio_path, **kwargs)

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

            avg_confidence = 0.0
            if all_segments:
                probs = [s["avg_logprob"] for s in all_segments if s["avg_logprob"] is not None]
                if probs:
                    import math
                    avg_confidence = round(math.exp(sum(probs) / len(probs)), 3)

            results.append({
                "text": full_text,
                "language": info.language,
                "language_probability": round(info.language_probability, 3),
                "duration_seconds": round(total_duration),
                "confidence": avg_confidence,
                "segments": all_segments,
                "provider": "faster-whisper-batched",
                "segment_count": len(all_segments),
                "task": task,
            })

            logger.info(
                "whisper_batch_file_done",
                audio_path=audio_path,
                segments=len(all_segments),
            )

        except Exception as e:
            logger.error("whisper_batch_file_failed", audio_path=audio_path, error=str(e))
            results.append(None)

    logger.info(
        "whisper_batch_complete",
        total=len(audio_paths),
        success=sum(1 for r in results if r is not None),
    )
    return results


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
