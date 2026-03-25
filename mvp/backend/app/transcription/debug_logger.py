"""
Debug Logger for Transcription - Development Mode
Provides detailed logging of all transcription steps
"""

import json
import structlog
from datetime import UTC, datetime
from typing import Any, Dict, Optional

logger = structlog.get_logger()


class TranscriptionDebugLogger:
    """
    Debug logger for transcription process.
    Logs every step with full data visibility.
    """
    
    def __init__(self, job_id: str, video_url: str, websocket_enabled: bool = False):
        self.job_id = job_id
        self.video_url = video_url
        self.start_time = datetime.now(UTC)
        self.steps = []
        self.websocket_enabled = websocket_enabled
        
        logger.info(
            "DEBUG_SESSION_START",
            separator="="*80,
            job_id=job_id,
            video_url=video_url,
            timestamp=self.start_time.isoformat()
        )
    
    def log_step(
        self,
        step_name: str,
        status: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Log a transcription step with full details"""
        
        step_time = datetime.now(UTC)
        duration = (step_time - self.start_time).total_seconds()
        
        step_info = {
            "step": step_name,
            "status": status,
            "timestamp": step_time.isoformat(),
            "duration_seconds": duration,
            "data": data or {},
            "error": error
        }
        
        self.steps.append(step_info)
        
        # Log with full details
        logger.info(
            f"TRANSCRIPTION_STEP_{len(self.steps)}_{step_name}",
            job_id=self.job_id,
            step_number=len(self.steps),
            step_name=step_name,
            status=status,
            duration_seconds=duration,
            data=json.dumps(data, indent=2) if data else None,
            error=error
        )
        
        # Print to console for immediate visibility
        print("\n" + "="*80)
        print(f"[DEBUG STEP {len(self.steps)}] {step_name}")
        print("="*80)
        print(f"Status: {status}")
        print(f"Duration: {duration:.2f}s")
        if data:
            print(f"Data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        if error:
            print(f"Error: {error}")
        print("="*80 + "\n")
        
        # Send via WebSocket if enabled
        if self.websocket_enabled:
            self._send_websocket_update(step_info)
    
    def _send_websocket_update(self, step_info: dict):
        """Send update via WebSocket (async)"""
        try:
            import asyncio
            import threading
            from app.modules.transcription.websocket import get_debug_manager
            
            manager = get_debug_manager()
            
            async def send_async():
                """Async wrapper to send message"""
                try:
                    await manager.send_debug_message(self.job_id, {
                        "type": "debug_step",
                        "step": step_info
                    })
                except Exception as e:
                    logger.error("websocket_send_error", error=str(e), job_id=self.job_id)
            
            # Run in a separate thread to avoid blocking
            def run_in_thread():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(send_async())
                    loop.close()
                except Exception as e:
                    logger.error("websocket_thread_error", error=str(e), job_id=self.job_id)
            
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
            
        except Exception as e:
            logger.warning("websocket_send_failed", error=str(e), job_id=self.job_id)
    
    def log_youtube_validation(self, is_valid: bool, video_id: Optional[str] = None):
        """Log YouTube URL validation"""
        self.log_step(
            "✅ STEP 1: YOUTUBE URL VALIDATION",
            "SUCCESS" if is_valid else "FAILED",
            data={
                "📥 INPUT": {
                    "original_url": self.video_url,
                },
                "📤 OUTPUT": {
                    "is_valid": is_valid,
                    "video_id": video_id,
                    "normalized_url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
                    "video_platform": "YouTube"
                }
            }
        )
    
    def log_youtube_download_start(self, temp_dir: str):
        """Log YouTube download start"""
        self.log_step(
            "📥 STEP 2: YOUTUBE AUDIO DOWNLOAD (START)",
            "IN_PROGRESS",
            data={
                "📥 INPUT": {
                    "video_url": self.video_url,
                    "download_format": "best audio (webm/m4a/opus)",
                    "temp_directory": temp_dir
                },
                "ℹ️ INFO": {
                    "tool": "yt-dlp",
                    "expected_duration": "5-15 seconds",
                    "status": "Downloading audio from YouTube..."
                }
            }
        )
    
    def log_youtube_download_complete(
        self,
        audio_file: str,
        file_size: int,
        metadata: Dict[str, Any],
        job_id: Optional[str] = None,
        detected_language: Optional[str] = None
    ):
        """Log YouTube download completion"""
        import os
        file_extension = os.path.splitext(audio_file)[1]
        
        output_data = {
            "audio_file_path": audio_file,
            "audio_file_name": os.path.basename(audio_file),
            "file_extension": file_extension,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / 1024 / 1024, 2),
            "file_size_human": f"{round(file_size / 1024 / 1024, 2)} MB"
        }
        
        # Add download link if job_id is provided
        if job_id:
            output_data["audio_download_url"] = f"/api/transcription/debug/{job_id}/audio"
            output_data["audio_available_for"] = "30 minutes"
        
        metadata_data = {
            "video_title": metadata.get('title', 'N/A'),
            "video_duration_seconds": metadata.get('duration', 'N/A'),
            "video_uploader": metadata.get('uploader', 'N/A'),
            "upload_date": metadata.get('upload_date', 'N/A')
        }
        
        # Add detected language if available
        if detected_language:
            from .language_detector import LanguageDetector
            metadata_data["detected_language"] = detected_language
            metadata_data["language_name"] = LanguageDetector.get_language_name(detected_language)
            metadata_data["assemblyai_supported"] = LanguageDetector.is_supported_by_assemblyai(detected_language)
        
        self.log_step(
            "📥 STEP 2: YOUTUBE AUDIO DOWNLOAD (COMPLETE)",
            "SUCCESS",
            data={
                "📤 OUTPUT": output_data,
                "📊 METADATA": metadata_data,
                "✅ STATUS": "Audio downloaded successfully",
                "🎧 LISTEN": f"You can download and listen to the audio at: /api/transcription/debug/{job_id}/audio" if job_id else "Audio file available"
            }
        )
    
    def log_assemblyai_upload_start(self, audio_file: str):
        """Log AssemblyAI upload start"""
        import os
        file_size = os.path.getsize(audio_file) if os.path.exists(audio_file) else 0
        
        self.log_step(
            "🚀 STEP 3: ASSEMBLYAI UPLOAD",
            "IN_PROGRESS",
            data={
                "📥 INPUT": {
                    "audio_file": audio_file,
                    "file_size_mb": round(file_size / 1024 / 1024, 2),
                    "api_service": "AssemblyAI"
                },
                "ℹ️ INFO": {
                    "status": "Uploading audio to AssemblyAI...",
                    "expected_duration": "5-10 seconds",
                    "next_step": "Transcription will start automatically after upload"
                }
            }
        )
    
    def log_assemblyai_upload_complete(self, transcript_id: str):
        """Log AssemblyAI upload completion"""
        self.log_step(
            "🚀 STEP 3: ASSEMBLYAI UPLOAD",
            "SUCCESS",
            data={
                "📤 OUTPUT": {
                    "transcript_id": transcript_id,
                    "upload_status": "Success",
                    "assemblyai_url": f"https://www.assemblyai.com/app/transcripts/{transcript_id}"
                },
                "✅ STATUS": "Audio uploaded successfully to AssemblyAI"
            }
        )
    
    def log_assemblyai_transcription_start(self, transcript_id: str):
        """Log AssemblyAI transcription start"""
        self.log_step(
            "⏳ STEP 4: AI TRANSCRIPTION",
            "IN_PROGRESS",
            data={
                "📥 INPUT": {
                    "transcript_id": transcript_id,
                    "assemblyai_url": f"https://www.assemblyai.com/app/transcripts/{transcript_id}"
                },
                "ℹ️ INFO": {
                    "status": "AI is transcribing audio...",
                    "expected_duration": "30-60 seconds (depends on audio length)",
                    "ai_model": "AssemblyAI Universal-1",
                    "process": "Speech-to-Text conversion in progress"
                }
            }
        )
    
    def log_assemblyai_transcription_complete(
        self,
        transcript_id: str,
        text: str,
        confidence: float,
        audio_duration: float,
        language_code: Optional[str] = None
    ):
        """Log AssemblyAI transcription completion"""
        words_count = len(text.split()) if text else 0
        chars_count = len(text)
        
        self.log_step(
            "⏳ STEP 4: AI TRANSCRIPTION",
            "SUCCESS",
            data={
                "📤 OUTPUT": {
                    "transcript_id": transcript_id,
                    "text_length_characters": chars_count,
                    "text_length_words": words_count,
                    "text_preview": text[:200] + "..." if len(text) > 200 else text,
                    "full_text": text,
                    "confidence_score": confidence,
                    "confidence_percentage": f"{round(confidence * 100, 1)}%",
                    "audio_duration_seconds": audio_duration,
                    "audio_duration_minutes": round(audio_duration / 60, 2),
                    "language_detected": language_code or "auto-detected"
                },
                "📊 STATISTICS": {
                    "total_characters": chars_count,
                    "total_words": words_count,
                    "average_word_length": round(chars_count / words_count, 2) if words_count > 0 else 0,
                    "transcription_quality": "High" if confidence > 0.8 else "Medium" if confidence > 0.6 else "Low"
                },
                "✅ STATUS": f"Transcription complete! {words_count} words transcribed with {round(confidence * 100, 1)}% confidence"
            }
        )
    
    def log_ai_router_start(self, raw_text_length: int, language: str):
        """Log AI Router content improvement start"""
        self.log_step(
            "🤖 STEP 5: AI ROUTER - CONTENT IMPROVEMENT",
            "IN_PROGRESS",
            data={
                "📥 INPUT": {
                    "raw_text_length": raw_text_length,
                    "language": language,
                    "task": "improve_quality",
                    "strategy": "COST_OPTIMIZED (prefer free models)"
                },
                "ℹ️ INFO": {
                    "status": "AI Router analyzing content...",
                    "phase_1": "Content Classification (domain, tone, sensitivity)",
                    "phase_2": "Model Selection (based on content type)",
                    "phase_3": "Content Improvement (structure, clarity, flow)",
                    "expected_duration": "10-30 seconds",
                    "cost": "FREE (using free AI models)"
                }
            }
        )
    
    def log_ai_router_complete(
        self,
        raw_length: int,
        improved_length: int,
        domain: str,
        sensitivity: str,
        model_used: str,
        strategy: str,
        confidence: float
    ):
        """Log AI Router content improvement completion"""
        growth_ratio = ((improved_length / raw_length - 1) * 100) if raw_length > 0 else 0
        
        self.log_step(
            "🤖 STEP 5: AI ROUTER - CONTENT IMPROVEMENT",
            "SUCCESS",
            data={
                "📤 OUTPUT": {
                    "improved_text_length": improved_length,
                    "growth_ratio_percentage": f"{growth_ratio:+.1f}%",
                    "growth_status": "✅ Within limits" if abs(growth_ratio) <= 50 else "⚠️ Exceeds +50%",
                    "ai_model_used": model_used,
                    "strategy_used": strategy,
                    "cost": "FREE 🆓"
                },
                "📊 CLASSIFICATION": {
                    "primary_domain": domain,
                    "sensitivity_level": sensitivity,
                    "classification_confidence": confidence,
                    "model_selection_reason": f"Selected {model_used} for {domain} content"
                },
                "📈 STATISTICS": {
                    "original_length": raw_length,
                    "improved_length": improved_length,
                    "difference": improved_length - raw_length,
                    "growth_ratio": f"{growth_ratio:+.1f}%"
                },
                "✅ STATUS": f"Content improved by {model_used}! Growth: {growth_ratio:+.1f}%"
            }
        )
    
    def log_ai_router_failed(self, error: str):
        """Log AI Router failure (fallback to raw text)"""
        self.log_step(
            "🤖 STEP 5: AI ROUTER - CONTENT IMPROVEMENT",
            "WARNING",
            data={
                "⚠️ WARNING": {
                    "status": "AI Router failed, using raw transcription",
                    "error": error,
                    "fallback": "Raw transcription text (no improvement)"
                },
                "ℹ️ INFO": {
                    "impact": "Transcription still available, but without AI enhancement",
                    "quality": "Raw AssemblyAI output (still good quality)"
                }
            },
            error=error
        )
    
    def log_cleanup(self, temp_dir: str, success: bool):
        """Log temporary file cleanup"""
        self.log_step(
            "🧹 STEP 6: CLEANUP TEMPORARY FILES",
            "SUCCESS" if success else "FAILED",
            data={
                "📥 INPUT": {
                    "temp_directory": temp_dir
                },
                "📤 OUTPUT": {
                    "cleanup_status": "Success" if success else "Failed",
                    "files_removed": "All temporary audio files deleted" if success else "Failed to delete temporary files"
                },
                "ℹ️ INFO": {
                    "reason": "Temporary audio files are no longer needed after transcription",
                    "disk_space_freed": "Audio file size (varies)"
                }
            }
        )
    
    def log_error(self, step_name: str, error: Exception):
        """Log an error"""
        self.log_step(
            step_name,
            "ERROR",
            error=f"{type(error).__name__}: {str(error)}"
        )
    
    def log_final_summary(self):
        """Log final summary of the transcription process"""
        end_time = datetime.now(UTC)
        total_duration = (end_time - self.start_time).total_seconds()
        
        summary = {
            "job_id": self.job_id,
            "video_url": self.video_url,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration_seconds": total_duration,
            "total_steps": len(self.steps),
            "steps_summary": [
                {
                    "step": s["step"],
                    "status": s["status"],
                    "duration": s["duration_seconds"]
                }
                for s in self.steps
            ]
        }
        
        logger.info(
            "DEBUG_SESSION_END",
            separator="="*80,
            **summary
        )
        
        print("\n" + "="*80)
        print("[DEBUG SESSION SUMMARY]")
        print("="*80)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        print("="*80 + "\n")


# Singleton instance for easy access
_current_debug_logger: Optional[TranscriptionDebugLogger] = None


def start_debug_session(job_id: str, video_url: str, websocket_enabled: bool = False) -> TranscriptionDebugLogger:
    """Start a new debug session"""
    global _current_debug_logger
    _current_debug_logger = TranscriptionDebugLogger(job_id, video_url, websocket_enabled)
    return _current_debug_logger


def get_debug_logger() -> Optional[TranscriptionDebugLogger]:
    """Get current debug logger"""
    return _current_debug_logger


def end_debug_session():
    """End current debug session"""
    global _current_debug_logger
    if _current_debug_logger:
        _current_debug_logger.log_final_summary()
        _current_debug_logger = None

