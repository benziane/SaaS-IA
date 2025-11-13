"""
Service for transcribing audio using various AI models
"""
import os
import time
import asyncio
from typing import Dict, Optional, Tuple
from pathlib import Path
import whisper
import torch

from app.core.config import settings


class TranscriptionService:
    """Service for transcribing audio using AI models"""

    def __init__(self, service: str = None, model_name: str = None):
        """
        Initialize transcription service

        Args:
            service: Transcription service to use (whisper, assemblyai, deepgram)
            model_name: Model name/size to use
        """
        self.service = service or settings.TRANSCRIPTION_SERVICE
        self.model_name = model_name or settings.WHISPER_MODEL
        self._model = None
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

    def _load_whisper_model(self):
        """Load Whisper model (lazy loading)"""
        if self._model is None:
            print(f"Loading Whisper model: {self.model_name} on {self._device}")
            self._model = whisper.load_model(self.model_name, device=self._device)
        return self._model

    async def transcribe_with_whisper(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio using OpenAI Whisper

        Args:
            audio_path: Path to audio file
            language: Target language code (None for auto-detect)

        Returns:
            Dictionary with transcription results
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        start_time = time.time()

        try:
            # Load model
            model = self._load_whisper_model()

            # Prepare options
            options = {
                "language": language if language != "auto" else None,
                "task": "transcribe",
                "verbose": False,
            }

            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: model.transcribe(audio_path, **options)
            )

            processing_time = time.time() - start_time

            # Extract segments with timestamps
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "confidence": segment.get("no_speech_prob", 0.0),
                })

            # Calculate average confidence
            avg_confidence = 1.0 - (
                sum(s.get("confidence", 0) for s in segments) / len(segments)
                if segments else 0.5
            )

            return {
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "segments": segments,
                "confidence": avg_confidence,
                "processing_time": processing_time,
                "model": self.model_name,
                "service": "whisper",
            }

        except Exception as e:
            raise Exception(f"Whisper transcription failed: {str(e)}")

    async def transcribe_with_assemblyai(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio using AssemblyAI API

        Args:
            audio_path: Path to audio file
            language: Target language code

        Returns:
            Dictionary with transcription results
        """
        if not settings.ASSEMBLYAI_API_KEY:
            raise ValueError("AssemblyAI API key not configured")

        # TODO: Implement AssemblyAI integration
        raise NotImplementedError("AssemblyAI integration coming soon")

    async def transcribe_with_deepgram(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio using Deepgram API

        Args:
            audio_path: Path to audio file
            language: Target language code

        Returns:
            Dictionary with transcription results
        """
        if not settings.DEEPGRAM_API_KEY:
            raise ValueError("Deepgram API key not configured")

        # TODO: Implement Deepgram integration
        raise NotImplementedError("Deepgram integration coming soon")

    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        service: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio using configured service

        Args:
            audio_path: Path to audio file
            language: Target language code (None for auto-detect)
            service: Override default service

        Returns:
            Dictionary with transcription results

        Raises:
            Exception: If transcription fails
        """
        service = service or self.service

        if service == "whisper":
            return await self.transcribe_with_whisper(audio_path, language)
        elif service == "assemblyai":
            return await self.transcribe_with_assemblyai(audio_path, language)
        elif service == "deepgram":
            return await self.transcribe_with_deepgram(audio_path, language)
        else:
            raise ValueError(f"Unsupported transcription service: {service}")

    def get_supported_languages(self) -> list:
        """
        Get list of supported languages

        Returns:
            List of language codes
        """
        if self.service == "whisper":
            return [
                "en", "fr", "ar", "es", "de", "it", "pt", "ru", "zh", "ja",
                "ko", "nl", "tr", "pl", "sv", "id", "hi", "th", "vi", "uk",
                # Whisper supports 99+ languages
            ]
        return []

    def estimate_processing_time(self, duration: float) -> float:
        """
        Estimate processing time based on audio duration

        Args:
            duration: Audio duration in seconds

        Returns:
            Estimated processing time in seconds
        """
        # Whisper processes roughly real-time on GPU, 5x slower on CPU
        if self.service == "whisper":
            multiplier = 1.5 if self._device == "cuda" else 7.0
            return duration * multiplier

        return duration * 0.5  # APIs are usually faster
