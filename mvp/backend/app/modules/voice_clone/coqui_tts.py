"""
Coqui TTS Service - Open-source text-to-speech and voice cloning.

Provides free, local TTS and voice cloning using the Coqui TTS toolkit (30K+ stars).
Supports 1100+ languages, multi-speaker models, and voice cloning from short samples.

Falls back gracefully if TTS is not installed.
The existing OpenAI TTS / ElevenLabs / mock providers are PRESERVED.
"""

import asyncio
import os
import tempfile
from typing import Optional

import structlog

logger = structlog.get_logger()

_tts = None
_model_name = None


def is_available() -> bool:
    """Check if Coqui TTS is installed."""
    try:
        from TTS.api import TTS  # noqa: F401
        return True
    except ImportError:
        return False


def _get_tts(model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"):
    """Lazy-load Coqui TTS model (singleton)."""
    global _tts, _model_name
    if _tts is not None and _model_name == model_name:
        return _tts
    try:
        from TTS.api import TTS
        _tts = TTS(model_name=model_name)
        _model_name = model_name
        logger.info("coqui_tts_loaded", model=model_name)
        return _tts
    except Exception as e:
        logger.error("coqui_tts_load_failed", error=str(e))
        return None


# Multi-language model mapping
LANGUAGE_MODELS = {
    "en": "tts_models/en/ljspeech/tacotron2-DDC",
    "fr": "tts_models/fr/mai/tacotron2-DDC",
    "de": "tts_models/de/thorsten/tacotron2-DDC",
    "es": "tts_models/es/mai/tacotron2-DDC",
    "multi": "tts_models/multilingual/multi-dataset/xtts_v2",  # Best quality, multi-lang
}


async def synthesize(
    text: str,
    language: str = "en",
    output_format: str = "wav",
    speed: float = 1.0,
    speaker_wav: Optional[str] = None,
) -> Optional[str]:
    """Synthesize text to speech using Coqui TTS.

    Args:
        text: Text to speak
        language: Language code (en, fr, de, es, or auto for multilingual)
        output_format: Output format (wav is native, mp3 requires conversion)
        speed: Speech speed multiplier
        speaker_wav: Path to reference audio for voice cloning (XTTS v2)

    Returns:
        Path to generated audio file, or None if unavailable.
    """
    if not is_available():
        return None

    # Select model based on language
    if speaker_wav:
        model_name = LANGUAGE_MODELS.get("multi", LANGUAGE_MODELS["en"])
    else:
        model_name = LANGUAGE_MODELS.get(language, LANGUAGE_MODELS["en"])

    tts = _get_tts(model_name)
    if tts is None:
        return None

    try:
        # Generate output file path
        fd, output_path = tempfile.mkstemp(suffix=f".{output_format}", prefix="coqui_tts_")
        os.close(fd)

        # Run TTS in thread (CPU-bound)
        if speaker_wav and "xtts" in model_name.lower():
            # Voice cloning with XTTS v2
            await asyncio.to_thread(
                tts.tts_to_file,
                text=text[:5000],
                file_path=output_path,
                speaker_wav=speaker_wav,
                language=language if language != "auto" else "en",
            )
        else:
            # Standard TTS
            await asyncio.to_thread(
                tts.tts_to_file,
                text=text[:5000],
                file_path=output_path,
            )

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(
                "coqui_tts_success",
                model=model_name,
                language=language,
                text_length=len(text),
                output_size=os.path.getsize(output_path),
                voice_cloning=speaker_wav is not None,
            )
            return output_path

        return None

    except Exception as e:
        logger.error("coqui_tts_failed", error=str(e), language=language)
        return None


async def clone_voice(
    sample_audio_path: str,
    text: str,
    language: str = "en",
) -> Optional[str]:
    """Clone a voice from a short audio sample and speak the given text.

    Uses XTTS v2 model which supports zero-shot voice cloning.
    Requires only 3-10 seconds of reference audio.

    Returns path to generated audio file, or None.
    """
    return await synthesize(
        text=text,
        language=language,
        speaker_wav=sample_audio_path,
    )


def list_available_models() -> list[dict]:
    """List available Coqui TTS models."""
    if not is_available():
        return []
    try:
        from TTS.api import TTS
        manager = TTS()
        models = []
        for model_name in manager.list_models():
            models.append({
                "id": model_name,
                "provider": "coqui",
                "type": "tts" if "tts_models" in model_name else "vocoder",
            })
        return models[:30]  # Limit to avoid huge list
    except Exception:
        return []


def get_supported_languages() -> list[dict]:
    """Get languages supported by Coqui TTS."""
    return [
        {"code": "en", "name": "English", "model": LANGUAGE_MODELS["en"]},
        {"code": "fr", "name": "French", "model": LANGUAGE_MODELS["fr"]},
        {"code": "de", "name": "German", "model": LANGUAGE_MODELS["de"]},
        {"code": "es", "name": "Spanish", "model": LANGUAGE_MODELS["es"]},
        {"code": "multi", "name": "Multilingual (XTTS v2)", "model": LANGUAGE_MODELS["multi"]},
    ]
