"""
AssemblyAI Service - Grade S++
Handles transcription using AssemblyAI API
"""

import assemblyai as aai
import structlog
from typing import Optional

from app.config import settings

logger = structlog.get_logger()

# ========================================================================
# ASSEMBLYAI CLIENT INITIALIZATION
# ========================================================================

# Configure AssemblyAI with API key from settings
aai.settings.api_key = settings.ASSEMBLYAI_API_KEY


# ========================================================================
# ASSEMBLYAI SERVICE
# ========================================================================

class AssemblyAIService:
    """Service for transcribing audio using AssemblyAI"""
    
    @staticmethod
    def transcribe_audio(
        audio_url: str,
        language_code: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio from URL using AssemblyAI
        
        Args:
            audio_url: URL of the audio file to transcribe
            language_code: Optional language code (e.g., 'en', 'fr')
        
        Returns:
            dict: Transcription result with text and metadata
        
        Raises:
            RuntimeError: If transcription fails
        """
        from .debug_logger import get_debug_logger
        debug = get_debug_logger()
        
        try:
            # Log language info
            language_info = {
                "audio_url": audio_url,
                "language_code": language_code,
                "language_detection": "explicit" if language_code else "auto"
            }
            
            logger.info(
                "assemblyai_transcribe_start",
                **language_info
            )
            
            if debug:
                debug.log_assemblyai_upload_start(audio_url)
            
            # Configure transcription with language
            config = aai.TranscriptionConfig(
                language_code=language_code
            )
            
            logger.info(
                "assemblyai_config",
                language_code=language_code,
                config_type="explicit_language" if language_code else "auto_detect"
            )
            
            # Create transcriber and transcribe
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(audio_url)
            
            if debug:
                # Log upload complete
                debug.log_assemblyai_upload_complete(transcript.id)
                # Log transcription start
                debug.log_assemblyai_transcription_start(transcript.id)
            
            # Check for errors
            if transcript.status == aai.TranscriptStatus.error:
                error_msg = f"AssemblyAI transcription failed: {transcript.error}"
                logger.error(
                    "assemblyai_transcribe_error",
                    error=transcript.error,
                    audio_url=audio_url
                )
                raise RuntimeError(error_msg)
            
            result = {
                "transcript_id": transcript.id,
                "text": transcript.text,
                "status": transcript.status.value,
                "audio_duration": transcript.audio_duration,
                "confidence": transcript.confidence if hasattr(transcript, 'confidence') else None,
                "language_code": transcript.language_code if hasattr(transcript, 'language_code') else language_code,
            }
            
            logger.info(
                "assemblyai_transcribe_success",
                transcript_id=transcript.id,
                audio_duration=transcript.audio_duration,
                word_count=len(transcript.text.split()) if transcript.text else 0
            )
            
            if debug:
                debug.log_assemblyai_transcription_complete(
                    transcript.id,
                    transcript.text or "",
                    result["confidence"] or 0.0,
                    transcript.audio_duration or 0.0,
                    result["language_code"]
                )
            
            # Return structured result
            return result
            
        except Exception as e:
            logger.error(
                "assemblyai_transcribe_exception",
                error=str(e),
                audio_url=audio_url
            )
            raise RuntimeError(f"AssemblyAI transcription failed: {str(e)}")
    
    @staticmethod
    def transcribe_with_polling(
        audio_url: str,
        language_code: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio using polling method (for async processing)
        
        This method submits the transcription and returns immediately.
        The caller can poll the status using get_transcript_status().
        
        Args:
            audio_url: URL of the audio file to transcribe
            language_code: Optional language code
        
        Returns:
            dict: Initial transcription info with transcript_id
        """
        try:
            logger.info(
                "assemblyai_submit_start",
                audio_url=audio_url,
                language_code=language_code
            )
            
            # Configure transcription
            config = aai.TranscriptionConfig(
                language_code=language_code
            )
            
            # Submit transcription (non-blocking)
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.submit(audio_url)
            
            logger.info(
                "assemblyai_submit_success",
                transcript_id=transcript.id,
                status=transcript.status.value
            )
            
            return {
                "transcript_id": transcript.id,
                "status": transcript.status.value,
                "audio_url": audio_url,
            }
            
        except Exception as e:
            logger.error(
                "assemblyai_submit_exception",
                error=str(e),
                audio_url=audio_url
            )
            raise RuntimeError(f"AssemblyAI submission failed: {str(e)}")
    
    @staticmethod
    def get_transcript_status(transcript_id: str) -> dict:
        """
        Get the status of a transcription job
        
        Args:
            transcript_id: AssemblyAI transcript ID
        
        Returns:
            dict: Transcript status and result (if completed)
        """
        try:
            transcript = aai.Transcript.get_by_id(transcript_id)
            
            result = {
                "transcript_id": transcript.id,
                "status": transcript.status.value,
            }
            
            # Add text if completed
            if transcript.status == aai.TranscriptStatus.completed:
                result.update({
                    "text": transcript.text,
                    "audio_duration": transcript.audio_duration,
                    "confidence": transcript.confidence if hasattr(transcript, 'confidence') else None,
                    "language_code": transcript.language_code if hasattr(transcript, 'language_code') else None,
                })
            
            # Add error if failed
            elif transcript.status == aai.TranscriptStatus.error:
                result["error"] = transcript.error
            
            return result
            
        except Exception as e:
            logger.error(
                "assemblyai_get_status_exception",
                error=str(e),
                transcript_id=transcript_id
            )
            raise RuntimeError(f"Failed to get transcript status: {str(e)}")


# ========================================================================
# EXPORTS
# ========================================================================

__all__ = ["AssemblyAIService"]

