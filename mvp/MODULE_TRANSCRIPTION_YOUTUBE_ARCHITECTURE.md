# 🎥 MODULE TRANSCRIPTION YOUTUBE - ARCHITECTURE & IMPLÉMENTATION

**Date** : 2025-11-14  
**Version** : 1.0.0  
**Priorité** : 🔴 CRITIQUE (Fonctionnalité MVP)  
**Statut** : 📋 CONCEPTION COMPLÈTE

---

## 📋 RÉSUMÉ EXÉCUTIF

Ce document détaille l'architecture complète du module de transcription automatique de vidéos YouTube, la première fonctionnalité de la plateforme SaaS-IA. Le module permet de:

1. **Extraire** l'audio d'une vidéo YouTube
2. **Transcrire** automatiquement en multilingue
3. **Corriger** les erreurs linguistiques
4. **Formater** le texte de manière propre et lisible

---

## 🎯 OBJECTIFS ET EXIGENCES

### Objectifs Fonctionnels

| Objectif | Description | Priorité |
|----------|-------------|----------|
| **Extraction Audio** | Télécharger et extraire l'audio d'une vidéo YouTube | 🔴 Critique |
| **Transcription Multilingue** | Supporter FR, EN, AR et auto-détection | 🔴 Critique |
| **Correction Linguistique** | Corriger ponctuation, casse, erreurs grammaticales | 🟡 Important |
| **Formatage Propre** | Produire un texte lisible, bien structuré | 🟡 Important |
| **Traitement Asynchrone** | Jobs background avec suivi en temps réel | 🔴 Critique |
| **Gestion d'Erreurs** | Gérer échecs gracieusement avec retry | 🟡 Important |

### Exigences Non-Fonctionnelles

| Exigence | Cible | Mesure |
|----------|-------|--------|
| **Performance** | Transcription < 2x durée vidéo | p95 < 2x |
| **Disponibilité** | 99.5% uptime | Mensuel |
| **Scalabilité** | 100 transcriptions simultanées | Horizontal scaling |
| **Sécurité** | Authentification JWT obligatoire | 100% |
| **Coût** | Free tier Assembly AI (5h/mois) | Phase MVP |
| **Qualité** | 95%+ accuracy transcription | Multilingue |

---

## 🏗️ ARCHITECTURE TECHNIQUE

### Vue d'Ensemble du Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Page: /transcription                                 │  │
│  │  - Form: URL YouTube + Langue                        │  │
│  │  - Progress Bar: Real-time updates                   │  │
│  │  - Result Display: Formatted text + Download         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP POST /api/transcriptions
                         │ JWT Bearer Token
┌────────────────────────▼────────────────────────────────────┐
│                  BACKEND (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Layer: /modules/transcription/routes.py         │  │
│  │  - POST /transcribe → Create job                     │  │
│  │  - GET /status/{id} → Get progress                   │  │
│  │  - GET /result/{id} → Get final text                 │  │
│  └────────────┬─────────────────────────────────────────┘  │
│               │                                              │
│  ┌────────────▼─────────────────────────────────────────┐  │
│  │  Service Layer: service.py                           │  │
│  │  1. Validate YouTube URL                             │  │
│  │  2. Create Transcription record (DB)                 │  │
│  │  3. Enqueue Celery task                              │  │
│  │  4. Return job_id immediately                        │  │
│  └────────────┬─────────────────────────────────────────┘  │
└───────────────┼──────────────────────────────────────────────┘
                │
┌───────────────▼──────────────────────────────────────────────┐
│            CELERY WORKER (Async Tasks)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Task: process_transcription(job_id)                 │  │
│  │                                                       │  │
│  │  Step 1: Extract Audio (yt-dlp)                      │  │
│  │    - Download video                                  │  │
│  │    - Extract audio track (MP3/WAV)                   │  │
│  │    - Save to /tmp                                    │  │
│  │                                                       │  │
│  │  Step 2: Transcribe (Assembly AI / Whisper)          │  │
│  │    - Upload audio to API                             │  │
│  │    - Wait for processing                             │  │
│  │    - Poll status every 5s                            │  │
│  │    - Get raw transcript                              │  │
│  │                                                       │  │
│  │  Step 3: Correct & Format                            │  │
│  │    - Fix punctuation                                 │  │
│  │    - Normalize casing                                │  │
│  │    - Remove filler words                             │  │
│  │    - Segment paragraphs                              │  │
│  │                                                       │  │
│  │  Step 4: Save & Notify                               │  │
│  │    - Update DB with final text                       │  │
│  │    - Mark status as "completed"                      │  │
│  │    - Emit WebSocket event                            │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                             │
│  ┌────────────┐  ┌──────────┐  ┌────────────────────────┐  │
│  │ PostgreSQL │  │  Redis   │  │  S3/Local Storage      │  │
│  │            │  │          │  │  - Audio files (.mp3)  │  │
│  │ - Users    │  │ - Cache  │  │  - Temp downloads      │  │
│  │ - Trans... │  │ - Queue  │  │                        │  │
│  └────────────┘  └──────────┘  └────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Composants Clés

#### 1. Backend API Layer (`routes.py`)

```python
# app/modules/transcription/routes.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.auth import get_current_user
from app.models.user import User
from app.modules.transcription.service import TranscriptionService
from app.modules.transcription.schemas import (
    TranscriptionCreateRequest,
    TranscriptionResponse,
    TranscriptionStatusResponse
)

router = APIRouter(prefix="/transcriptions", tags=["transcription"])

@router.post("/", response_model=TranscriptionResponse, status_code=202)
async def create_transcription(
    request: TranscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    service: TranscriptionService = Depends()
):
    """
    Démarre une nouvelle transcription YouTube.
    
    - Valide l'URL YouTube
    - Crée un job de transcription
    - Lance le traitement asynchrone
    - Retourne immédiatement avec job_id
    """
    return await service.create_transcription(
        youtube_url=request.youtube_url,
        language=request.language,
        user_id=current_user.id
    )

@router.get("/{transcription_id}", response_model=TranscriptionStatusResponse)
async def get_transcription_status(
    transcription_id: str,
    current_user: User = Depends(get_current_user),
    service: TranscriptionService = Depends()
):
    """
    Récupère le statut d'une transcription.
    
    Statuts possibles:
    - pending: En attente
    - processing: En cours (downloading, transcribing, correcting)
    - completed: Terminé avec succès
    - failed: Échec avec message d'erreur
    """
    return await service.get_transcription_status(
        transcription_id=transcription_id,
        user_id=current_user.id
    )

@router.get("/", response_model=list[TranscriptionResponse])
async def list_transcriptions(
    current_user: User = Depends(get_current_user),
    service: TranscriptionService = Depends(),
    skip: int = 0,
    limit: int = 20
):
    """Liste toutes les transcriptions de l'utilisateur"""
    return await service.list_transcriptions(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

@router.delete("/{transcription_id}", status_code=204)
async def delete_transcription(
    transcription_id: str,
    current_user: User = Depends(get_current_user),
    service: TranscriptionService = Depends()
):
    """Supprime une transcription"""
    await service.delete_transcription(
        transcription_id=transcription_id,
        user_id=current_user.id
    )
    return None
```

#### 2. Service Layer (`service.py`)

```python
# app/modules/transcription/service.py

from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.transcription.models import Transcription, TranscriptionStatus
from app.modules.transcription.tasks import process_transcription_task
from app.modules.transcription.validators import validate_youtube_url
import uuid
from datetime import datetime

class TranscriptionService:
    """Service métier pour la gestion des transcriptions"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_transcription(
        self,
        youtube_url: str,
        language: str,
        user_id: uuid.UUID
    ) -> dict:
        """
        Crée une nouvelle transcription et lance le traitement asynchrone.
        
        Flow:
        1. Valider l'URL YouTube
        2. Créer l'enregistrement en DB (status: pending)
        3. Enqueue la tâche Celery
        4. Retourner immédiatement avec job_id
        """
        
        # 1. Validation
        video_info = await validate_youtube_url(youtube_url)
        if not video_info:
            raise ValueError("URL YouTube invalide")
        
        # 2. Création DB
        transcription = Transcription(
            id=uuid.uuid4(),
            user_id=user_id,
            youtube_url=youtube_url,
            video_title=video_info.get("title"),
            video_duration=video_info.get("duration"),
            language=language,
            status=TranscriptionStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        self.session.add(transcription)
        await self.session.commit()
        await self.session.refresh(transcription)
        
        # 3. Enqueue tâche Celery
        process_transcription_task.delay(str(transcription.id))
        
        # 4. Retour immédiat
        return {
            "id": str(transcription.id),
            "status": transcription.status,
            "youtube_url": youtube_url,
            "video_title": video_info.get("title"),
            "estimated_duration": f"{video_info.get('duration')} seconds",
            "message": "Transcription démarrée avec succès"
        }
    
    async def get_transcription_status(
        self,
        transcription_id: str,
        user_id: uuid.UUID
    ) -> dict:
        """Récupère le statut actuel d'une transcription"""
        
        transcription = await self.session.get(
            Transcription,
            uuid.UUID(transcription_id)
        )
        
        if not transcription:
            raise ValueError("Transcription non trouvée")
        
        if transcription.user_id != user_id:
            raise PermissionError("Accès refusé")
        
        return {
            "id": str(transcription.id),
            "status": transcription.status,
            "progress": transcription.progress,
            "current_step": transcription.current_step,
            "youtube_url": transcription.youtube_url,
            "video_title": transcription.video_title,
            "transcript_text": transcription.transcript_text,
            "error_message": transcription.error_message,
            "created_at": transcription.created_at.isoformat(),
            "completed_at": transcription.completed_at.isoformat() if transcription.completed_at else None
        }
    
    async def list_transcriptions(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20
    ) -> list[dict]:
        """Liste les transcriptions de l'utilisateur"""
        
        from sqlalchemy import select
        
        stmt = (
            select(Transcription)
            .where(Transcription.user_id == user_id)
            .order_by(Transcription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        transcriptions = result.scalars().all()
        
        return [
            {
                "id": str(t.id),
                "status": t.status,
                "youtube_url": t.youtube_url,
                "video_title": t.video_title,
                "created_at": t.created_at.isoformat()
            }
            for t in transcriptions
        ]
    
    async def delete_transcription(
        self,
        transcription_id: str,
        user_id: uuid.UUID
    ):
        """Supprime une transcription"""
        
        transcription = await self.session.get(
            Transcription,
            uuid.UUID(transcription_id)
        )
        
        if not transcription:
            raise ValueError("Transcription non trouvée")
        
        if transcription.user_id != user_id:
            raise PermissionError("Accès refusé")
        
        await self.session.delete(transcription)
        await self.session.commit()
```

#### 3. Celery Tasks (`tasks.py`)

```python
# app/modules/transcription/tasks.py

from celery import Task
from app.celery_app import celery_app
from app.database import get_session
from app.modules.transcription.models import Transcription, TranscriptionStatus
from app.modules.transcription.youtube_service import YouTubeService
from app.modules.transcription.ai_service import TranscriptionAIService
from app.modules.transcription.correction_service import CorrectionService
import uuid
import logging

logger = logging.getLogger(__name__)

class TranscriptionTask(Task):
    """Tâche Celery avec retry automatique"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True

@celery_app.task(base=TranscriptionTask, bind=True)
def process_transcription_task(self, transcription_id: str):
    """
    Tâche principale de traitement de transcription.
    
    Steps:
    1. Extract audio from YouTube
    2. Transcribe audio
    3. Correct & format text
    4. Save final result
    """
    
    logger.info(f"Starting transcription job {transcription_id}")
    
    # Services
    youtube_service = YouTubeService()
    ai_service = TranscriptionAIService()
    correction_service = CorrectionService()
    
    try:
        # Get transcription from DB
        async with get_session() as session:
            transcription = await session.get(
                Transcription,
                uuid.UUID(transcription_id)
            )
            
            if not transcription:
                raise ValueError(f"Transcription {transcription_id} not found")
            
            # Update status: processing
            transcription.status = TranscriptionStatus.PROCESSING
            transcription.current_step = "downloading"
            transcription.progress = 10
            await session.commit()
            
            # STEP 1: Extract audio
            logger.info(f"[{transcription_id}] Step 1: Extracting audio")
            audio_path = youtube_service.download_audio(
                transcription.youtube_url
            )
            
            transcription.current_step = "transcribing"
            transcription.progress = 30
            await session.commit()
            
            # STEP 2: Transcribe
            logger.info(f"[{transcription_id}] Step 2: Transcribing audio")
            raw_transcript = ai_service.transcribe(
                audio_path=audio_path,
                language=transcription.language
            )
            
            transcription.current_step = "correcting"
            transcription.progress = 70
            transcription.raw_transcript = raw_transcript
            await session.commit()
            
            # STEP 3: Correct & format
            logger.info(f"[{transcription_id}] Step 3: Correcting text")
            final_text = correction_service.correct_and_format(
                text=raw_transcript,
                language=transcription.language
            )
            
            # STEP 4: Save result
            transcription.status = TranscriptionStatus.COMPLETED
            transcription.current_step = "completed"
            transcription.progress = 100
            transcription.transcript_text = final_text
            transcription.completed_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"[{transcription_id}] Completed successfully")
            
            # Cleanup
            youtube_service.cleanup(audio_path)
            
    except Exception as e:
        logger.error(f"[{transcription_id}] Failed: {str(e)}")
        
        # Update status: failed
        async with get_session() as session:
            transcription = await session.get(
                Transcription,
                uuid.UUID(transcription_id)
            )
            
            transcription.status = TranscriptionStatus.FAILED
            transcription.error_message = str(e)
            await session.commit()
        
        # Re-raise for Celery retry
        raise
```

#### 4. YouTube Service (`youtube_service.py`)

```python
# app/modules/transcription/youtube_service.py

import yt_dlp
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class YouTubeService:
    """Service pour l'extraction audio de YouTube"""
    
    def __init__(self):
        self.download_dir = Path("/tmp/youtube_downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def download_audio(self, youtube_url: str) -> str:
        """
        Télécharge et extrait l'audio d'une vidéo YouTube.
        
        Returns:
            str: Chemin du fichier audio (.mp3)
        """
        
        # Options yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                video_id = info['id']
                audio_path = self.download_dir / f"{video_id}.mp3"
                
                logger.info(f"Audio extracted: {audio_path}")
                return str(audio_path)
                
        except Exception as e:
            logger.error(f"Failed to download audio: {str(e)}")
            raise
    
    def get_video_info(self, youtube_url: str) -> dict:
        """Récupère les informations de la vidéo sans télécharger"""
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                return {
                    "title": info.get("title"),
                    "duration": info.get("duration"),  # en secondes
                    "channel": info.get("channel"),
                    "thumbnail": info.get("thumbnail"),
                }
        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            raise
    
    def cleanup(self, audio_path: str):
        """Supprime le fichier audio temporaire"""
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info(f"Cleaned up: {audio_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {audio_path}: {str(e)}")
```

#### 5. AI Service - Assembly AI (`ai_service.py`)

```python
# app/modules/transcription/ai_service.py

import assemblyai as aai
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class TranscriptionAIService:
    """Service de transcription utilisant Assembly AI"""
    
    def __init__(self):
        # Configuration Assembly AI
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
        self.transcriber = aai.Transcriber()
    
    def transcribe(self, audio_path: str, language: str = "auto") -> str:
        """
        Transcrit un fichier audio.
        
        Args:
            audio_path: Chemin vers le fichier audio
            language: Code langue (fr, en, ar, auto)
        
        Returns:
            str: Texte transcrit brut
        """
        
        try:
            logger.info(f"Starting transcription: {audio_path}")
            
            # Configuration Assembly AI
            config = aai.TranscriptionConfig(
                language_code=self._map_language(language),
                punctuate=True,  # Ponctuation automatique
                format_text=True,  # Formatage automatique
                speaker_labels=False,  # Pas de diarisation (MVP)
            )
            
            # Transcription
            transcript = self.transcriber.transcribe(
                audio_path,
                config=config
            )
            
            # Vérification du statut
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Transcription failed: {transcript.error}")
            
            logger.info(f"Transcription completed: {len(transcript.text)} chars")
            
            return transcript.text
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise
    
    def _map_language(self, language: str) -> str:
        """Mappe les codes de langue vers Assembly AI"""
        mapping = {
            "fr": "fr",
            "en": "en",
            "ar": "ar",
            "auto": "en",  # Défaut si auto-détection
        }
        return mapping.get(language.lower(), "en")
```

**Alternative: Whisper (OpenAI)**

```python
# Alternative avec Whisper API (si besoin)
import openai
from app.config import settings

class WhisperTranscriptionService:
    """Service de transcription utilisant OpenAI Whisper"""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
    
    def transcribe(self, audio_path: str, language: str = "auto") -> str:
        """Transcrit avec Whisper API"""
        
        with open(audio_path, "rb") as audio_file:
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language=language if language != "auto" else None
            )
        
        return transcript["text"]
```

#### 6. Correction Service (`correction_service.py`)

```python
# app/modules/transcription/correction_service.py

import re
import logging

logger = logging.getLogger(__name__)

class CorrectionService:
    """Service de correction et formatage de transcriptions"""
    
    def correct_and_format(self, text: str, language: str) -> str:
        """
        Corrige et formate le texte transcrit.
        
        Corrections appliquées:
        1. Normalisation des espaces
        2. Capitalisation des débuts de phrases
        3. Formatage de la ponctuation
        4. Suppression des mots de remplissage (euh, hmm)
        5. Segmentation en paragraphes
        """
        
        logger.info(f"Starting text correction ({len(text)} chars)")
        
        # 1. Normalisation des espaces
        text = self._normalize_spaces(text)
        
        # 2. Suppression des fillers
        text = self._remove_fillers(text, language)
        
        # 3. Capitalisation
        text = self._capitalize_sentences(text)
        
        # 4. Formatage ponctuation
        text = self._format_punctuation(text)
        
        # 5. Segmentation paragraphes
        text = self._segment_paragraphs(text)
        
        logger.info(f"Text correction completed ({len(text)} chars)")
        
        return text
    
    def _normalize_spaces(self, text: str) -> str:
        """Normalise les espaces multiples"""
        # Remplace espaces multiples par un seul
        text = re.sub(r'\s+', ' ', text)
        # Trim
        text = text.strip()
        return text
    
    def _remove_fillers(self, text: str, language: str) -> str:
        """Supprime les mots de remplissage"""
        
        fillers = {
            "fr": [r'\beuh\b', r'\bhmm\b', r'\bhein\b', r'\bben\b', r'\bquoi\b'],
            "en": [r'\buh\b', r'\bum\b', r'\blike\b', r'\byou know\b'],
            "ar": [r'\bيعني\b', r'\bفهمت\b']
        }
        
        patterns = fillers.get(language, fillers["en"])
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return self._normalize_spaces(text)
    
    def _capitalize_sentences(self, text: str) -> str:
        """Capitalise le début de chaque phrase"""
        
        # Sépare sur . ! ?
        sentences = re.split(r'([.!?]+\s+)', text)
        
        result = []
        for i, part in enumerate(sentences):
            if i % 2 == 0:  # Texte (pas ponctuation)
                if part:
                    part = part[0].upper() + part[1:] if len(part) > 1 else part.upper()
            result.append(part)
        
        return ''.join(result)
    
    def _format_punctuation(self, text: str) -> str:
        """Formate correctement la ponctuation"""
        
        # Espace avant : ; ! ?
        text = re.sub(r'\s*([;:!?])', r' \1', text)
        
        # Pas d'espace après apostrophe
        text = re.sub(r"'\s+", "'", text)
        
        # Espace après , . ; : ! ?
        text = re.sub(r'([,.;:!?])([^\s\d])', r'\1 \2', text)
        
        return text
    
    def _segment_paragraphs(self, text: str, max_sentences: int = 5) -> str:
        """Segmente le texte en paragraphes logiques"""
        
        # Sépare sur les phrases
        sentences = re.split(r'([.!?]+)', text)
        
        paragraphs = []
        current_paragraph = []
        sentence_count = 0
        
        for i in range(0, len(sentences), 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
                current_paragraph.append(sentence)
                sentence_count += 1
                
                if sentence_count >= max_sentences:
                    paragraphs.append(''.join(current_paragraph).strip())
                    current_paragraph = []
                    sentence_count = 0
        
        # Dernier paragraphe
        if current_paragraph:
            paragraphs.append(''.join(current_paragraph).strip())
        
        return '\n\n'.join(paragraphs)
```

---

## 📊 MODÈLES DE DONNÉES

### Model SQLAlchemy

```python
# app/models/transcription.py

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from datetime import datetime
import enum

class TranscriptionStatus(str, enum.Enum):
    """États possibles d'une transcription"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Transcription(Base):
    """Modèle de transcription YouTube"""
    
    __tablename__ = "transcriptions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relations
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="transcriptions")
    
    # Metadata vidéo
    youtube_url = Column(String(500), nullable=False)
    video_title = Column(String(500))
    video_duration = Column(Integer)  # en secondes
    
    # Configuration
    language = Column(String(10), nullable=False, default="auto")
    
    # État du job
    status = Column(Enum(TranscriptionStatus), nullable=False, default=TranscriptionStatus.PENDING)
    current_step = Column(String(50))  # downloading, transcribing, correcting, completed
    progress = Column(Integer, default=0)  # 0-100
    
    # Résultats
    raw_transcript = Column(Text)  # Transcription brute
    transcript_text = Column(Text)  # Transcription finale corrigée
    
    # Erreurs
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index("idx_transcriptions_user_id", "user_id"),
        Index("idx_transcriptions_status", "status"),
        Index("idx_transcriptions_created_at", "created_at"),
    )
```

### Migration Alembic

```python
# alembic/versions/xxx_create_transcriptions_table.py

"""create transcriptions table

Revision ID: xxx
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

def upgrade():
    # Create enum type
    op.execute("CREATE TYPE transcriptionstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    
    # Create table
    op.create_table(
        'transcriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('youtube_url', sa.String(500), nullable=False),
        sa.Column('video_title', sa.String(500)),
        sa.Column('video_duration', sa.Integer()),
        sa.Column('language', sa.String(10), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='transcriptionstatus'), nullable=False),
        sa.Column('current_step', sa.String(50)),
        sa.Column('progress', sa.Integer(), default=0),
        sa.Column('raw_transcript', sa.Text()),
        sa.Column('transcript_text', sa.Text()),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime()),
    )
    
    # Create indexes
    op.create_index('idx_transcriptions_user_id', 'transcriptions', ['user_id'])
    op.create_index('idx_transcriptions_status', 'transcriptions', ['status'])
    op.create_index('idx_transcriptions_created_at', 'transcriptions', ['created_at'])

def downgrade():
    op.drop_index('idx_transcriptions_created_at')
    op.drop_index('idx_transcriptions_status')
    op.drop_index('idx_transcriptions_user_id')
    op.drop_table('transcriptions')
    op.execute('DROP TYPE transcriptionstatus')
```

---

## 🎨 FRONTEND (Next.js + Sneat MUI)

### Page Transcription

```typescript
// src/app/(dashboard)/transcription/page.tsx

'use client';

import { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  LinearProgress,
  Alert,
  Card,
  CardContent,
} from '@mui/material';
import { PlayArrow, Download } from '@mui/icons-material';
import { useTranscription } from '@/features/transcription/hooks/useTranscription';
import { TranscriptionResult } from '@/features/transcription/components/TranscriptionResult';

export default function TranscriptionPage() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [language, setLanguage] = useState('auto');
  
  const {
    createTranscription,
    transcriptionStatus,
    isCreating,
    isPolling,
    error,
  } = useTranscription();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createTranscription({ youtube_url: youtubeUrl, language });
  };
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Transcription YouTube
      </Typography>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="URL de la vidéo YouTube"
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            required
            sx={{ mb: 2 }}
          />
          
          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel>Langue</InputLabel>
            <Select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              label="Langue"
            >
              <MenuItem value="auto">Auto-détection</MenuItem>
              <MenuItem value="fr">Français</MenuItem>
              <MenuItem value="en">English</MenuItem>
              <MenuItem value="ar">العربية</MenuItem>
            </Select>
          </FormControl>
          
          <Button
            type="submit"
            variant="contained"
            size="large"
            startIcon={<PlayArrow />}
            disabled={isCreating || isPolling}
            fullWidth
          >
            {isCreating ? 'Démarrage...' : 'Démarrer la transcription'}
          </Button>
        </form>
      </Paper>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {transcriptionStatus && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {transcriptionStatus.video_title}
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Statut: {transcriptionStatus.status} - {transcriptionStatus.current_step}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={transcriptionStatus.progress}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {transcriptionStatus.progress}%
              </Typography>
            </Box>
            
            {transcriptionStatus.status === 'completed' && transcriptionStatus.transcript_text && (
              <TranscriptionResult text={transcriptionStatus.transcript_text} />
            )}
          </CardContent>
        </Card>
      )}
    </Container>
  );
}
```

### Hook React Query

```typescript
// src/features/transcription/hooks/useTranscription.ts

import { useMutation, useQuery } from '@tanstack/react-query';
import { transcriptionApi } from '../api';
import { useState, useEffect } from 'react';

export function useTranscription() {
  const [transcriptionId, setTranscriptionId] = useState<string | null>(null);
  
  // Création de transcription
  const createMutation = useMutation({
    mutationFn: transcriptionApi.createTranscription,
    onSuccess: (data) => {
      setTranscriptionId(data.id);
    },
  });
  
  // Polling du statut
  const { data: transcriptionStatus, error: statusError } = useQuery({
    queryKey: ['transcription-status', transcriptionId],
    queryFn: () => transcriptionApi.getStatus(transcriptionId!),
    enabled: !!transcriptionId,
    refetchInterval: (data) => {
      // Stop polling si terminé ou échoué
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      // Polling toutes les 3 secondes
      return 3000;
    },
  });
  
  return {
    createTranscription: createMutation.mutate,
    transcriptionStatus,
    isCreating: createMutation.isPending,
    isPolling: !!transcriptionId && transcriptionStatus?.status === 'processing',
    error: createMutation.error || statusError,
  };
}
```

### Composant Résultat

```typescript
// src/features/transcription/components/TranscriptionResult.tsx

import { Box, Button, Paper, Typography } from '@mui/material';
import { Download, ContentCopy } from '@mui/icons-material';
import { useState } from 'react';

interface Props {
  text: string;
}

export function TranscriptionResult({ text }: Props) {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const handleDownload = () => {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcription-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  return (
    <Box>
      <Box sx={{ mb: 2, display: 'flex', gap: 1 }}>
        <Button
          startIcon={<ContentCopy />}
          onClick={handleCopy}
          variant="outlined"
          size="small"
        >
          {copied ? 'Copié !' : 'Copier'}
        </Button>
        <Button
          startIcon={<Download />}
          onClick={handleDownload}
          variant="outlined"
          size="small"
        >
          Télécharger
        </Button>
      </Box>
      
      <Paper
        sx={{
          p: 3,
          maxHeight: '600px',
          overflow: 'auto',
          bgcolor: 'grey.50',
        }}
      >
        <Typography
          variant="body1"
          component="div"
          sx={{
            whiteSpace: 'pre-wrap',
            lineHeight: 1.8,
          }}
        >
          {text}
        </Typography>
      </Paper>
    </Box>
  );
}
```

---

## 🔒 SÉCURITÉ

### Rate Limiting

```python
# app/modules/transcription/routes.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/")
@limiter.limit("10/hour")  # Max 10 transcriptions par heure
async def create_transcription(...):
    ...
```

### Validation des URLs

```python
# app/modules/transcription/validators.py

import re
from urllib.parse import urlparse

YOUTUBE_REGEX = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'

async def validate_youtube_url(url: str) -> dict | None:
    """Valide qu'une URL est bien une URL YouTube valide"""
    
    if not re.match(YOUTUBE_REGEX, url):
        raise ValueError("URL YouTube invalide")
    
    parsed = urlparse(url)
    if parsed.scheme not in ['http', 'https']:
        raise ValueError("Protocole non sécurisé")
    
    return await YouTubeService().get_video_info(url)
```

### Sanitization

```python
# Limiter la taille des vidéos
MAX_VIDEO_DURATION = 7200  # 2 heures max

if video_info['duration'] > MAX_VIDEO_DURATION:
    raise ValueError("Vidéo trop longue (max 2h)")
```

---

## ⚡ OPTIMISATIONS

### Cache Redis

```python
# Cache des métadonnées vidéo
@cache.memoize(timeout=3600)  # 1 heure
async def get_video_info(youtube_url: str):
    ...
```

### Compression des Transcriptions

```python
# Compression gzip pour les longues transcriptions
import gzip

if len(text) > 10000:
    compressed = gzip.compress(text.encode())
    # Stocker compressed au lieu de text
```

### Pool de Connexions

```python
# Celery avec pool de workers
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_PREFETCH_MULTIPLIER = 2
```

---

## 📊 MONITORING

### Métriques Clés

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram

transcription_counter = Counter(
    'transcriptions_total',
    'Total number of transcriptions',
    ['status', 'language']
)

transcription_duration = Histogram(
    'transcription_duration_seconds',
    'Transcription processing duration'
)
```

### Logging

```python
# Structured logging
logger.info(
    "Transcription completed",
    extra={
        "transcription_id": transcription_id,
        "user_id": user_id,
        "duration": duration,
        "text_length": len(text),
    }
)
```

---

## 🧪 TESTS

### Tests Unitaires

```python
# tests/test_transcription_service.py

import pytest
from app.modules.transcription.service import TranscriptionService

@pytest.mark.asyncio
async def test_create_transcription(db_session, test_user):
    service = TranscriptionService(db_session)
    
    result = await service.create_transcription(
        youtube_url="https://youtube.com/watch?v=test",
        language="fr",
        user_id=test_user.id
    )
    
    assert result["status"] == "pending"
    assert "id" in result

@pytest.mark.asyncio
async def test_invalid_url(db_session, test_user):
    service = TranscriptionService(db_session)
    
    with pytest.raises(ValueError, match="URL YouTube invalide"):
        await service.create_transcription(
            youtube_url="https://not-youtube.com/video",
            language="fr",
            user_id=test_user.id
        )
```

### Tests d'Intégration

```python
# tests/integration/test_transcription_flow.py

@pytest.mark.asyncio
async def test_full_transcription_flow(client, test_user, monkeypatch):
    """Test du flow complet de transcription"""
    
    # Mock yt-dlp
    def mock_download(*args, **kwargs):
        return "/tmp/test.mp3"
    monkeypatch.setattr("yt_dlp.YoutubeDL.extract_info", mock_download)
    
    # Mock Assembly AI
    def mock_transcribe(*args, **kwargs):
        return "This is a test transcription"
    monkeypatch.setattr("assemblyai.Transcriber.transcribe", mock_transcribe)
    
    # 1. Créer transcription
    response = client.post(
        "/api/transcriptions/",
        json={
            "youtube_url": "https://youtube.com/watch?v=test",
            "language": "en"
        },
        headers={"Authorization": f"Bearer {test_user.token}"}
    )
    assert response.status_code == 202
    transcription_id = response.json()["id"]
    
    # 2. Attendre completion (avec timeout)
    max_wait = 30
    for _ in range(max_wait):
        response = client.get(
            f"/api/transcriptions/{transcription_id}",
            headers={"Authorization": f"Bearer {test_user.token}"}
        )
        status = response.json()["status"]
        if status == "completed":
            break
        await asyncio.sleep(1)
    
    # 3. Vérifier résultat
    assert status == "completed"
    assert response.json()["transcript_text"]
```

---

## 📦 DÉPLOIEMENT

### Docker Compose

```yaml
# docker-compose.yml

version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8004:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/saas_ia
      - REDIS_URL=redis://redis:6379
      - ASSEMBLYAI_API_KEY=${ASSEMBLYAI_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - /tmp/youtube_downloads:/tmp/youtube_downloads
  
  celery-worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/saas_ia
      - REDIS_URL=redis://redis:6379
      - ASSEMBLYAI_API_KEY=${ASSEMBLYAI_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - /tmp/youtube_downloads:/tmp/youtube_downloads
  
  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=saas_ia_user
      - POSTGRES_PASSWORD=saas_ia_dev_password
      - POSTGRES_DB=saas_ia
    ports:
      - "5435:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6382:6379"

volumes:
  postgres_data:
```

### Variables d'Environnement

```bash
# .env

# Assembly AI
ASSEMBLYAI_API_KEY=your_assembly_ai_key_here

# Database
DATABASE_URL=postgresql://saas_ia_user:saas_ia_dev_password@localhost:5435/saas_ia

# Redis
REDIS_URL=redis://localhost:6382

# JWT
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=http://localhost:3002

# Logging
LOG_LEVEL=INFO
```

---

## 📈 ROADMAP

### Phase 1: MVP (Semaine 1-2) ✅

- [x] Architecture backend
- [x] Extraction audio YouTube
- [x] Transcription Assembly AI
- [x] Correction basique
- [x] API REST
- [x] Interface utilisateur
- [x] Tests unitaires

### Phase 2: Améliorations (Semaine 3-4)

- [ ] WebSocket pour updates temps réel
- [ ] Diarisation (détection locuteurs)
- [ ] Export formats multiples (PDF, DOCX, SRT)
- [ ] Dashboard statistiques
- [ ] Historique des transcriptions
- [ ] Recherche full-text

### Phase 3: Scalabilité (Semaine 5-6)

- [ ] Queue prioritaire (Celery)
- [ ] Cache Redis avancé
- [ ] CDN pour fichiers audio
- [ ] Monitoring Grafana
- [ ] Alertes erreurs
- [ ] Auto-scaling workers

### Phase 4: Fonctionnalités Avancées (Semaine 7+)

- [ ] Résumé automatique (GPT-4)
- [ ] Traduction simultanée
- [ ] Chapitrage automatique
- [ ] Sous-titres SRT
- [ ] Intégration Google Drive
- [ ] API publique

---

## 🎓 RESSOURCES

### Documentation API

- **Assembly AI**: https://www.assemblyai.com/docs
- **yt-dlp**: https://github.com/yt-dlp/yt-dlp
- **Celery**: https://docs.celeryq.dev/
- **FastAPI**: https://fastapi.tiangolo.com/

### Templates de Code

Tous les templates complets sont disponibles dans:
- `TEMPLATES-CODE-MODULES.md`
- `GUIDE-IMPLEMENTATION-MODULAIRE.md`

---

## ✅ CHECKLIST DE MISE EN ŒUVRE

### Backend

- [ ] Créer models SQLAlchemy
- [ ] Créer migration Alembic
- [ ] Implémenter YouTubeService
- [ ] Implémenter TranscriptionAIService
- [ ] Implémenter CorrectionService
- [ ] Créer routes API
- [ ] Créer tasks Celery
- [ ] Ajouter tests unitaires
- [ ] Ajouter tests d'intégration
- [ ] Documenter API (OpenAPI)

### Frontend

- [ ] Créer page transcription
- [ ] Créer hooks React Query
- [ ] Implémenter formulaire
- [ ] Implémenter progress bar
- [ ] Créer composant résultat
- [ ] Ajouter boutons export
- [ ] Gérer états d'erreur
- [ ] Tests E2E Playwright

### Infrastructure

- [ ] Configurer Docker Compose
- [ ] Setup Celery workers
- [ ] Configurer Redis
- [ ] Configurer variables env
- [ ] Setup monitoring basique
- [ ] Configurer logs structurés

### Documentation

- [ ] README module
- [ ] Guide utilisateur
- [ ] Guide développeur
- [ ] Exemples d'utilisation
- [ ] Troubleshooting guide

---

## 🚀 QUICK START

### 1. Installation

```bash
# Backend
cd backend
poetry install
alembic upgrade head

# Frontend
cd frontend
npm install

# Docker
docker-compose up -d
```

### 2. Configuration

```bash
# Obtenir clé Assembly AI gratuite
# https://www.assemblyai.com/dashboard/signup

# Configurer .env
ASSEMBLYAI_API_KEY=your_key_here
```

### 3. Lancement

```bash
# Services
docker-compose up -d

# Backend
cd backend
uvicorn app.main:app --reload --port 8004

# Celery worker
celery -A app.celery_app worker --loglevel=info

# Frontend
cd frontend
npm run dev
```

### 4. Test

```bash
# Ouvrir http://localhost:3002/transcription
# Coller URL YouTube
# Sélectionner langue
# Cliquer "Démarrer"
# Attendre résultat (progress bar en temps réel)
```

---

**Document créé par** : Assistant IA  
**Date** : 2025-11-14  
**Version** : 1.0.0  
**Status** : ✅ COMPLET ET PRÊT POUR IMPLÉMENTATION

---

## 📞 SUPPORT

Pour toute question ou problème:
- GitHub Issues
- Documentation complète dans `/docs`
- Stack Overflow (tag: saas-ia)
