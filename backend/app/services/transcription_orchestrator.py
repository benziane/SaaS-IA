"""
Orchestrator service that coordinates the entire transcription pipeline
"""
import asyncio
from typing import Dict, Optional, Callable
from datetime import datetime

from app.services.youtube_extractor import YouTubeExtractor
from app.services.transcription_service import TranscriptionService
from app.services.post_processor import TranscriptPostProcessor
from app.models.transcription import TranscriptionStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.transcription import Transcription


class TranscriptionOrchestrator:
    """Orchestrates the complete transcription pipeline"""

    def __init__(self):
        """Initialize orchestrator with all required services"""
        self.youtube_extractor = YouTubeExtractor()
        self.transcription_service = TranscriptionService()
        self.post_processor = TranscriptPostProcessor()

    async def process_transcription(
        self,
        transcription_id: int,
        db: AsyncSession,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Complete transcription pipeline

        Args:
            transcription_id: Database ID of transcription
            db: Database session
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with processing results
        """
        try:
            # Get transcription record
            result = await db.execute(
                select(Transcription).where(Transcription.id == transcription_id)
            )
            transcription = result.scalar_one_or_none()

            if not transcription:
                raise ValueError(f"Transcription {transcription_id} not found")

            # Helper to update status
            async def update_status(status: TranscriptionStatus, progress: int, **kwargs):
                await db.execute(
                    update(Transcription)
                    .where(Transcription.id == transcription_id)
                    .values(status=status, progress=progress, **kwargs)
                )
                await db.commit()

                if progress_callback:
                    progress_callback(status, progress)

            # Step 1: Download audio (0-30%)
            await update_status(TranscriptionStatus.DOWNLOADING, 0)

            def download_progress(percent):
                asyncio.create_task(
                    update_status(TranscriptionStatus.DOWNLOADING, int(percent * 0.3))
                )

            audio_path, video_info = await self.youtube_extractor.download_audio(
                transcription.youtube_url,
                transcription.video_id,
                progress_callback=download_progress
            )

            # Update with video info
            await update_status(
                TranscriptionStatus.EXTRACTING,
                30,
                video_title=video_info.get("title"),
                video_duration=video_info.get("duration"),
                channel_name=video_info.get("channel"),
                audio_file_path=audio_path
            )

            # Step 2: Transcribe audio (30-70%)
            await update_status(TranscriptionStatus.TRANSCRIBING, 40)

            language = transcription.language if transcription.language != "auto" else None

            transcription_result = await self.transcription_service.transcribe(
                audio_path,
                language=language
            )

            await update_status(
                TranscriptionStatus.TRANSCRIBING,
                70,
                raw_transcript=transcription_result["text"],
                detected_language=transcription_result["language"],
                transcription_service=transcription_result["service"],
                model_used=transcription_result["model"],
                processing_time=transcription_result["processing_time"],
                confidence_score=transcription_result["confidence"],
                metadata={"segments": transcription_result["segments"]}
            )

            # Step 3: Post-process (70-100%)
            await update_status(TranscriptionStatus.POST_PROCESSING, 80)

            detected_lang = transcription_result["language"]
            post_process_result = await self.post_processor.process(
                transcription_result["text"],
                language=detected_lang
            )

            await update_status(
                TranscriptionStatus.POST_PROCESSING,
                95
            )

            # Step 4: Final update
            await update_status(
                TranscriptionStatus.COMPLETED,
                100,
                corrected_transcript=post_process_result["processed_text"],
                word_count=post_process_result["word_count"],
                completed_at=datetime.utcnow()
            )

            # Optional: Cleanup audio file
            # await self.youtube_extractor.cleanup_audio(audio_path)

            return {
                "success": True,
                "transcription_id": transcription_id,
                "video_info": video_info,
                "transcription": transcription_result,
                "post_processing": post_process_result,
            }

        except Exception as e:
            # Update with error
            await db.execute(
                update(Transcription)
                .where(Transcription.id == transcription_id)
                .values(
                    status=TranscriptionStatus.FAILED,
                    error_message=str(e)
                )
            )
            await db.commit()

            return {
                "success": False,
                "transcription_id": transcription_id,
                "error": str(e)
            }

    async def get_video_preview(self, youtube_url: str) -> Dict:
        """
        Get video information without processing

        Args:
            youtube_url: YouTube video URL

        Returns:
            Dictionary with video information
        """
        return await self.youtube_extractor.get_video_info(youtube_url)
