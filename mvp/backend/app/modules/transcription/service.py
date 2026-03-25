"""
Transcription service - Business logic for transcription jobs
"""

import asyncio
from datetime import datetime
from typing import Optional, List
from uuid import UUID

import structlog
from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.metrics import transcription_jobs_total
from app.models.transcription import Transcription, TranscriptionStatus
from app.database import get_session_context

# Initialize logger
logger = structlog.get_logger()


class TranscriptionService:
    """Service for managing transcription jobs"""
    
    def __init__(self):
        """Initialize transcription service"""
        api_key = settings.ASSEMBLYAI_API_KEY
        
        # Check if we're in MOCK mode
        if api_key == "MOCK" or api_key.startswith("your-") or api_key.startswith("change-"):
            self.mock_mode = True
            logger.info("⚠️  Mode MOCK activé pour Assembly AI - Transcriptions simulées")
        else:
            self.mock_mode = False
            try:
                import assemblyai as aai
                aai.settings.api_key = api_key
                self.aai = aai
                logger.info("✅ Assembly AI configuré avec clé API réelle")
            except ImportError:
                logger.warning("⚠️  assemblyai package non installé, passage en mode MOCK")
                self.mock_mode = True
    
    async def create_job(
        self,
        video_url: str,
        user_id: UUID,
        language: Optional[str],
        session: AsyncSession,
        source_type: str = "youtube",
        original_filename: Optional[str] = None
    ) -> Transcription:
        """Create a new transcription job"""

        job = Transcription(
            video_url=video_url,
            user_id=user_id,
            language=language or "auto",
            status=TranscriptionStatus.PENDING,
            source_type=source_type,
            original_filename=original_filename
        )
        
        session.add(job)
        await session.commit()
        await session.refresh(job)
        
        transcription_jobs_total.labels(status="pending").inc()

        logger.info(
            "transcription_job_created",
            job_id=str(job.id),
            user_id=str(user_id),
            video_url=video_url,
            mock_mode=self.mock_mode
        )
        
        return job
    
    async def process_transcription(self, job_id: UUID):
        """
        Process a transcription job (runs in background)
        
        This method runs asynchronously in the background using FastAPI BackgroundTasks
        """
        
        async with get_session_context() as session:
            # Get job
            job = await session.get(Transcription, job_id)
            
            if not job:
                logger.error("transcription_job_not_found", job_id=str(job_id))
                return
            
            try:
                # Update status to processing
                job.status = TranscriptionStatus.PROCESSING
                job.updated_at = datetime.utcnow()
                await session.commit()
                
                logger.info(
                    "transcription_processing_started",
                    job_id=str(job.id),
                    video_url=job.video_url,
                    mock_mode=self.mock_mode
                )
                
                if self.mock_mode:
                    # MOCK MODE: Simulate transcription
                    result = await self._mock_transcribe(job.video_url)
                else:
                    # REAL MODE: Use Assembly AI
                    result = await self._real_transcribe(job.video_url)
                
                # Update job with results
                job.status = TranscriptionStatus.COMPLETED
                job.text = result["text"]
                job.confidence = result.get("confidence", 0.95)
                job.duration_seconds = result.get("duration_seconds", 180)
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                
                await session.commit()
                
                transcription_jobs_total.labels(status="completed").inc()

                # Auto-index completed transcription into Knowledge Base
                try:
                    from app.modules.knowledge.service import KnowledgeService
                    if job.text and len(job.text.strip()) > 50:
                        filename = f"transcription_{job.source_type}_{str(job.id)[:8]}.md"
                        if job.original_filename:
                            filename = f"transcription_{job.original_filename}"
                        await KnowledgeService.index_text_content(
                            user_id=job.user_id,
                            filename=filename,
                            content=job.text,
                            content_type="text/plain",
                            session=session,
                        )
                except Exception as e:
                    logger.warning("auto_index_transcription_failed", error=str(e))

                # Auto-analyze sentiment
                try:
                    from app.modules.sentiment.service import SentimentService
                    if job.text and len(job.text.strip()) > 100:
                        sentiment_result = await SentimentService.analyze_text(job.text[:5000])
                        import json
                        job.sentiment_json = json.dumps(sentiment_result, ensure_ascii=False)
                        job.sentiment_score = sentiment_result.get("overall_score", 0.0)
                        session.add(job)
                        await session.commit()
                except Exception as e:
                    logger.warning("auto_sentiment_failed", error=str(e))

                logger.info(
                    "transcription_completed",
                    job_id=str(job.id),
                    text_length=len(result["text"]),
                    confidence=result.get("confidence"),
                    mock_mode=self.mock_mode
                )

            except Exception as e:
                # Handle errors
                job.status = TranscriptionStatus.FAILED
                job.error = str(e)[:1000]  # Limit error message length
                job.retry_count += 1
                job.updated_at = datetime.utcnow()
                
                await session.commit()
                
                transcription_jobs_total.labels(status="failed").inc()

                logger.error(
                    "transcription_failed",
                    job_id=str(job.id),
                    error=str(e),
                    retry_count=job.retry_count
                )
    
    async def process_upload_transcription(self, job_id: UUID, file_path: str, language: Optional[str] = None):
        """
        Process a file upload transcription job (runs in background).

        Sends a local audio file to AssemblyAI (or mock), updates
        the job record, and cleans up the temporary file afterwards.
        """
        import os

        async with get_session_context() as session:
            job = await session.get(Transcription, job_id)

            if not job:
                logger.error("upload_transcription_job_not_found", job_id=str(job_id))
                return

            try:
                job.status = TranscriptionStatus.PROCESSING
                job.updated_at = datetime.utcnow()
                await session.commit()

                logger.info(
                    "upload_transcription_processing_started",
                    job_id=str(job.id),
                    file_path=file_path,
                    mock_mode=self.mock_mode
                )

                if self.mock_mode:
                    result = await self._mock_transcribe(file_path)
                else:
                    result = await self._real_transcribe_file(file_path, language)

                job.status = TranscriptionStatus.COMPLETED
                job.text = result["text"]
                job.confidence = result.get("confidence", 0.95)
                job.duration_seconds = result.get("duration_seconds", 0)
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()

                await session.commit()

                transcription_jobs_total.labels(status="completed").inc()

                # Auto-index completed transcription into Knowledge Base
                try:
                    from app.modules.knowledge.service import KnowledgeService
                    if job.text and len(job.text.strip()) > 50:
                        filename = f"transcription_{job.source_type}_{str(job.id)[:8]}.md"
                        if job.original_filename:
                            filename = f"transcription_{job.original_filename}"
                        await KnowledgeService.index_text_content(
                            user_id=job.user_id,
                            filename=filename,
                            content=job.text,
                            content_type="text/plain",
                            session=session,
                        )
                except Exception as e:
                    logger.warning("auto_index_transcription_failed", error=str(e))

                # Auto-analyze sentiment
                try:
                    from app.modules.sentiment.service import SentimentService
                    if job.text and len(job.text.strip()) > 100:
                        sentiment_result = await SentimentService.analyze_text(job.text[:5000])
                        import json
                        job.sentiment_json = json.dumps(sentiment_result, ensure_ascii=False)
                        job.sentiment_score = sentiment_result.get("overall_score", 0.0)
                        session.add(job)
                        await session.commit()
                except Exception as e:
                    logger.warning("auto_sentiment_failed", error=str(e))

                logger.info(
                    "upload_transcription_completed",
                    job_id=str(job.id),
                    text_length=len(result["text"]),
                    confidence=result.get("confidence"),
                    mock_mode=self.mock_mode
                )

            except Exception as e:
                job.status = TranscriptionStatus.FAILED
                job.error = str(e)[:1000]
                job.retry_count += 1
                job.updated_at = datetime.utcnow()

                await session.commit()

                transcription_jobs_total.labels(status="failed").inc()

                logger.error(
                    "upload_transcription_failed",
                    job_id=str(job.id),
                    error=str(e),
                    retry_count=job.retry_count
                )
            finally:
                # Clean up the temporary uploaded file
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info("upload_temp_file_cleaned", file_path=file_path)
                except Exception as e:
                    logger.warning("upload_temp_file_cleanup_failed", file_path=file_path, error=str(e))

    async def _real_transcribe_file(self, file_path: str, language: Optional[str] = None) -> dict:
        """
        Transcribe a local audio file using AssemblyAI.

        Unlike _real_transcribe which downloads from YouTube first, this method
        sends a local file directly to AssemblyAI for transcription.
        """
        from app.transcription import AssemblyAIService

        logger.info("real_file_transcription_started", file_path=file_path, language=language)

        # AssemblyAI accepts local file paths directly
        result = await asyncio.to_thread(
            AssemblyAIService.transcribe_audio,
            file_path,
            language if language and language != "auto" else None
        )

        return {
            "text": result["text"],
            "confidence": result.get("confidence"),
            "duration_seconds": result.get("audio_duration"),
        }

    async def _mock_transcribe(self, video_url: str) -> dict:
        """
        MOCK transcription for testing without API key
        
        Simulates a 2-second processing time and returns fake transcription
        """
        
        logger.info("mock_transcription_started", video_url=video_url)
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Return mock transcription
        mock_text = f"""
        Ceci est une transcription SIMULÉE pour le test.
        
        URL de la vidéo : {video_url}
        
        Cette transcription est générée en mode MOCK car aucune clé API Assembly AI réelle n'est configurée.
        
        Pour utiliser Assembly AI réellement :
        1. Obtenez une clé API sur https://www.assemblyai.com/
        2. Modifiez .env : ASSEMBLYAI_API_KEY=votre-clé-réelle
        3. Redémarrez le backend
        
        En mode MOCK, vous pouvez tester toutes les fonctionnalités de l'API sans consommer de crédits Assembly AI.
        
        Timestamp : {datetime.utcnow().isoformat()}
        """.strip()
        
        return {
            "text": mock_text,
            "confidence": 0.95,
            "duration_seconds": 180
        }
    
    async def _real_transcribe(self, video_url: str) -> dict:
        """
        Real transcription using Assembly AI + AI Router
        
        This method is called when a real API key is configured.
        Uses AI Router for intelligent model selection and content restructuring.
        """
        from app.transcription import YouTubeService, AssemblyAIService
        from app.transcription.debug_logger import start_debug_session, end_debug_session
        from app.transcription.audio_cache import get_audio_cache
        from app.transcription.language_detector import LanguageDetector
        from app.ai_assistant.service import AIAssistantService
        from app.ai_assistant.classification.model_selector import SelectionStrategy
        from app.database import get_session_context
        import shutil
        import uuid
        
        # Start debug session (with WebSocket enabled)
        job_id = str(uuid.uuid4())
        debug = start_debug_session(job_id, video_url, websocket_enabled=True)
        audio_cache = get_audio_cache()
        
        logger.info("real_transcription_started", video_url=video_url, job_id=job_id)
        
        try:
            # Validate YouTube URL
            video_id = YouTubeService.extract_video_id(video_url)
            is_valid = video_id is not None
            debug.log_youtube_validation(is_valid, video_id)
            
            if not is_valid:
                raise ValueError(f"Invalid YouTube URL: {video_url}")
            
            # Download audio from YouTube
            audio_file, metadata = await asyncio.to_thread(
                YouTubeService.download_audio,
                video_url
            )
            
            # Log download complete with job_id for audio download link
            import os
            file_size = os.path.getsize(audio_file)
            debug.log_youtube_download_complete(audio_file, file_size, metadata, job_id)
            
            try:
                # Cache audio file for debug (30 minutes TTL)
                cached_audio_path = audio_cache.store_audio(
                    job_id,
                    audio_file,
                    metadata,
                    ttl_minutes=30
                )
                logger.info("audio_cached_for_debug", job_id=job_id, cached_path=cached_audio_path)
                
                # Detect language from metadata
                detected_language = LanguageDetector.detect_language_from_metadata(metadata)
                
                # Transcribe using AssemblyAI (blocking call in thread)
                result = await asyncio.to_thread(
                    AssemblyAIService.transcribe_audio,
                    audio_file,
                    detected_language
                )
                
                # Extract raw transcription
                raw_text = result["text"]
                confidence = result.get("confidence")
                
                # 🆕 USE AI ROUTER for intelligent content improvement
                try:
                    # Log AI Router start
                    debug.log_ai_router_start(len(raw_text), detected_language)
                    
                    async with get_session_context() as db_session:
                        logger.info(
                            "ai_router_start",
                            job_id=job_id,
                            text_length=len(raw_text),
                            language=detected_language
                        )
                        
                        # Use AI Router with COST_OPTIMIZED strategy
                        improved_result = await AIAssistantService.process_text_smart(
                            db=db_session,
                            text=raw_text,
                            task="improve_quality",
                            language=detected_language,
                            metadata={
                                "source": "youtube_transcription",
                                "job_id": job_id,
                                "confidence": confidence,
                                "video_title": metadata.get("title")
                            },
                            strategy=SelectionStrategy.COST_OPTIMIZED
                        )
                        
                        improved_text = improved_result["processed_text"]
                        classification = improved_result.get("classification", {})
                        model_selection = improved_result.get("model_selection", {})
                        
                        # Log AI Router success
                        debug.log_ai_router_complete(
                            raw_length=len(raw_text),
                            improved_length=len(improved_text),
                            domain=classification.get("primary_domain", "unknown"),
                            sensitivity=classification.get("sensitivity", {}).get("level", "low"),
                            model_used=model_selection.get("model", "unknown"),
                            strategy=model_selection.get("strategy_used", "unknown"),
                            confidence=classification.get("confidence", 0.0)
                        )
                        
                        logger.info(
                            "ai_router_success",
                            job_id=job_id,
                            raw_length=len(raw_text),
                            improved_length=len(improved_text),
                            domain=classification.get("primary_domain"),
                            sensitivity=classification.get("sensitivity", {}).get("level"),
                            model_used=model_selection.get("model"),
                            strategy=model_selection.get("strategy_used")
                        )
                except Exception as e:
                    # Log AI Router failure
                    debug.log_ai_router_failed(str(e))
                    
                    logger.warning(
                        "ai_router_failed",
                        job_id=job_id,
                        error=str(e),
                        fallback="using_raw_text"
                    )
                    improved_text = raw_text  # Fallback
                
                # Extract results
                final_result = {
                    "text": improved_text,  # Use AI-improved text
                    "raw_text": raw_text,  # Keep original for comparison
                    "confidence": confidence,
                    "duration_seconds": result.get("audio_duration"),
                    "job_id": job_id,
                    "audio_available": True,
                    "ai_improved": improved_text != raw_text
                }
                
                # End debug session
                end_debug_session()
                
                return final_result
                
            finally:
                # Cleanup: Delete temporary audio file (original download, not cache)
                try:
                    import os
                    temp_dir = os.path.dirname(audio_file)
                    shutil.rmtree(temp_dir)
                    logger.info("temp_audio_cleanup", temp_dir=temp_dir)
                    debug.log_cleanup(temp_dir, True)
                except Exception as e:
                    logger.warning("temp_audio_cleanup_failed", error=str(e))
                    debug.log_cleanup(temp_dir, False)
                    
        except Exception as e:
            debug.log_error("TRANSCRIPTION_ERROR", e)
            end_debug_session()
            raise
    
    async def get_job(self, job_id: UUID, session: AsyncSession) -> Optional[Transcription]:
        """Get a transcription job by ID"""
        return await session.get(Transcription, job_id)
    
    async def list_user_jobs(
        self,
        user_id: UUID,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TranscriptionStatus] = None
    ) -> tuple[List[Transcription], int]:
        """
        List transcription jobs for a user with pagination and optional status filter.

        Returns a tuple of (items, total_count).
        """
        # Build base filter conditions
        conditions = [Transcription.user_id == user_id]
        if status is not None:
            conditions.append(Transcription.status == status)

        # Count query
        count_statement = select(func.count()).select_from(Transcription).where(*conditions)
        count_result = await session.execute(count_statement)
        total = count_result.scalar_one()

        # Data query
        statement = (
            select(Transcription)
            .where(*conditions)
            .order_by(Transcription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await session.execute(statement)
        items = result.scalars().all()

        return items, total
    
    async def get_user_stats(self, user_id: UUID, session: AsyncSession) -> dict:
        """Get transcription statistics for a user"""

        # Counts by status
        status_result = await session.execute(
            select(
                Transcription.status,
                func.count().label("cnt"),
            )
            .where(Transcription.user_id == user_id)
            .group_by(Transcription.status)
        )
        status_counts: dict[str, int] = {}
        for row in status_result.all():
            status_counts[row.status] = row.cnt

        completed = status_counts.get(TranscriptionStatus.COMPLETED, 0)
        failed = status_counts.get(TranscriptionStatus.FAILED, 0)
        pending = status_counts.get(TranscriptionStatus.PENDING, 0)
        processing = status_counts.get(TranscriptionStatus.PROCESSING, 0)
        total = completed + failed + pending + processing

        # Total duration (sum of completed transcription durations)
        duration_result = await session.execute(
            select(func.coalesce(func.sum(Transcription.duration_seconds), 0))
            .where(Transcription.user_id == user_id)
            .where(Transcription.status == TranscriptionStatus.COMPLETED)
        )
        total_duration_seconds = duration_result.scalar() or 0

        # Average confidence
        confidence_result = await session.execute(
            select(func.avg(Transcription.confidence))
            .where(Transcription.user_id == user_id)
            .where(Transcription.status == TranscriptionStatus.COMPLETED)
            .where(Transcription.confidence.isnot(None))
        )
        avg_confidence = confidence_result.scalar()
        if avg_confidence is not None:
            avg_confidence = round(float(avg_confidence), 4)

        # Recent transcriptions (last 5)
        recent_result = await session.execute(
            select(Transcription)
            .where(Transcription.user_id == user_id)
            .order_by(Transcription.created_at.desc())
            .limit(5)
        )
        recent_jobs = recent_result.scalars().all()
        recent_transcriptions = [
            {
                "id": str(job.id),
                "video_url": job.video_url,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
            }
            for job in recent_jobs
        ]

        return {
            "total_transcriptions": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "processing": processing,
            "total_duration_seconds": int(total_duration_seconds),
            "avg_confidence": avg_confidence,
            "recent_transcriptions": recent_transcriptions,
        }

    @staticmethod
    async def smart_transcribe(
        video_url: str,
        language: str = "auto",
        prefer_provider: str = "auto",
    ) -> dict:
        """
        Smart transcription routing:
        1. youtube-transcript-api (instant, free) for YouTube with subtitles
        2. faster-whisper (local, free) as fallback
        3. AssemblyAI (paid, premium) for diarization or premium quality
        """
        from app.transcription.youtube_transcript import (
            extract_video_id,
            get_youtube_transcript,
        )

        # Strategy 1: Try YouTube subtitles first (instant, free)
        if prefer_provider in ("auto", "youtube_subtitles"):
            video_id = extract_video_id(video_url)
            if video_id:
                transcript = await get_youtube_transcript(video_url, language)
                if transcript:
                    return transcript

        # Strategy 2: faster-whisper local (free, fast, with confidence retry)
        if prefer_provider in ("auto", "whisper", "faster_whisper"):
            try:
                from app.modules.transcription.whisper_local import is_available as fw_available, transcribe_with_confidence_retry
                if fw_available():
                    from app.transcription import YouTubeService

                    audio_file, metadata = await asyncio.to_thread(
                        YouTubeService.download_audio, video_url
                    )
                    if audio_file:
                        result = await transcribe_with_confidence_retry(
                            audio_file, language, confidence_threshold=0.6,
                        )
                        if result and result.get("text"):
                            logger.info("faster_whisper_success", confidence=result.get("confidence"))
                            return result
            except Exception as e:
                logger.debug("faster_whisper_fallback", error=str(e))

        # Strategy 2b: Legacy whisper_service fallback
        if prefer_provider in ("auto", "whisper"):
            try:
                from app.transcription.whisper_service import transcribe_with_whisper
                from app.transcription.youtube_service import YouTubeService

                audio_path = await YouTubeService.download_audio(video_url)
                if audio_path:
                    result = await transcribe_with_whisper(audio_path, language)
                    if result:
                        return result
            except Exception:
                pass

        # Strategy 3: Fall back to AssemblyAI (paid, high quality)
        try:
            from app.transcription.assemblyai_service import AssemblyAIService

            result = await AssemblyAIService.transcribe(video_url, language)
            if result:
                result["provider"] = "assemblyai"
                return result
        except Exception:
            pass

        return {"text": "", "error": "All transcription providers failed", "provider": "none"}

    @staticmethod
    async def transcribe_playlist(
        playlist_url: str,
        language: str = "auto",
        max_videos: int = 20,
        user_id=None,
        session=None,
    ) -> dict:
        """
        Transcribe all videos in a YouTube playlist.
        Returns list of transcription results.
        """
        from app.transcription.youtube_transcript import get_playlist_videos, get_youtube_metadata

        videos = await get_playlist_videos(playlist_url, max_videos)
        if not videos:
            return {"success": False, "error": "No videos found in playlist", "results": []}

        results = []
        for video in videos:
            try:
                # Get metadata
                metadata = await get_youtube_metadata(video["url"])

                # Smart transcribe
                transcript = await TranscriptionService.smart_transcribe(
                    video["url"], language
                )

                results.append({
                    "video_id": video["video_id"],
                    "title": video.get("title", "") or (metadata.get("title", "") if metadata else ""),
                    "url": video["url"],
                    "transcript": transcript.get("text", ""),
                    "provider": transcript.get("provider", "unknown"),
                    "duration": transcript.get("duration_seconds", 0),
                    "language": transcript.get("language", ""),
                    "success": bool(transcript.get("text")),
                    "metadata": metadata,
                })

            except Exception as e:
                results.append({
                    "video_id": video["video_id"],
                    "title": video.get("title", ""),
                    "url": video["url"],
                    "success": False,
                    "error": str(e)[:500],
                })

        return {
            "success": True,
            "total": len(videos),
            "transcribed": sum(1 for r in results if r.get("success")),
            "results": results,
        }

    async def delete_job(self, job_id: UUID, session: AsyncSession) -> bool:
        """Delete a transcription job"""
        
        job = await session.get(Transcription, job_id)
        
        if not job:
            return False
        
        await session.delete(job)
        await session.commit()
        
        logger.info("transcription_job_deleted", job_id=str(job_id))
        
        return True

