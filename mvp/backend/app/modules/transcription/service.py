"""
Transcription service - Business logic for transcription jobs
"""

import asyncio
from datetime import datetime
from typing import Optional, List
from uuid import UUID

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
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
        session: AsyncSession
    ) -> Transcription:
        """Create a new transcription job"""
        
        job = Transcription(
            video_url=video_url,
            user_id=user_id,
            language=language or "auto",
            status=TranscriptionStatus.PENDING
        )
        
        session.add(job)
        await session.commit()
        await session.refresh(job)
        
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
                
                logger.error(
                    "transcription_failed",
                    job_id=str(job.id),
                    error=str(e),
                    retry_count=job.retry_count
                )
    
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
        Real transcription using Assembly AI
        
        This method is called when a real API key is configured
        """
        
        logger.info("real_transcription_started", video_url=video_url)
        
        # Use Assembly AI transcriber
        transcriber = self.aai.Transcriber()
        
        # Transcribe (this is blocking, but we're in a background task)
        transcript = await asyncio.to_thread(transcriber.transcribe, video_url)
        
        # Extract results
        return {
            "text": transcript.text,
            "confidence": transcript.confidence if hasattr(transcript, 'confidence') else None,
            "duration_seconds": transcript.audio_duration if hasattr(transcript, 'audio_duration') else None
        }
    
    async def get_job(self, job_id: UUID, session: AsyncSession) -> Optional[Transcription]:
        """Get a transcription job by ID"""
        return await session.get(Transcription, job_id)
    
    async def list_user_jobs(
        self,
        user_id: UUID,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transcription]:
        """List all transcription jobs for a user"""
        
        statement = (
            select(Transcription)
            .where(Transcription.user_id == user_id)
            .order_by(Transcription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await session.execute(statement)
        return result.scalars().all()
    
    async def delete_job(self, job_id: UUID, session: AsyncSession) -> bool:
        """Delete a transcription job"""
        
        job = await session.get(Transcription, job_id)
        
        if not job:
            return False
        
        await session.delete(job)
        await session.commit()
        
        logger.info("transcription_job_deleted", job_id=str(job_id))
        
        return True

