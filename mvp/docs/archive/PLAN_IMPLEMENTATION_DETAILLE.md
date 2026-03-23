# 📋 PLAN D'IMPLÉMENTATION - MODULE TRANSCRIPTION YOUTUBE

**Date** : 2025-11-14  
**Durée Estimée** : 5-7 jours  
**Niveau** : Intermédiaire à Avancé  
**Prérequis** : Base de code existante (backend FastAPI + frontend Next.js)

---

## 🎯 OBJECTIF

Implémenter de A à Z le module de transcription automatique de vidéos YouTube en suivant un plan structuré et progressif permettant de tester à chaque étape.

---

## 📅 PLANNING GLOBAL

| Jour | Phase | Durée | Livrables |
|------|-------|-------|-----------|
| **J1** | Setup & Infrastructure | 4-6h | Base de données, Celery, Tests |
| **J2** | Services Core | 6-8h | YouTube, AI, Correction |
| **J3** | API Backend | 4-6h | Routes, Validation, Rate limiting |
| **J4** | Tasks Asynchrones | 4-6h | Celery tasks, Retry, Error handling |
| **J5** | Frontend Interface | 6-8h | Page, Form, Progress bar |
| **J6** | Tests & Debug | 4-6h | Tests E2E, Correction bugs |
| **J7** | Polish & Doc | 2-4h | Documentation, Optimisations |

**Total** : 30-44 heures de développement

---

## 📋 JOUR 1 : SETUP & INFRASTRUCTURE (4-6h)

### Étape 1.1 : Modèles de Données (1h)

#### Créer le modèle Transcription

```bash
# Créer le fichier
touch backend/app/models/transcription.py
```

```python
# backend/app/models/transcription.py

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid
from datetime import datetime
import enum

class TranscriptionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Transcription(Base):
    __tablename__ = "transcriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Vidéo info
    youtube_url = Column(String(500), nullable=False)
    video_title = Column(String(500))
    video_duration = Column(Integer)
    
    # Config
    language = Column(String(10), nullable=False, default="auto")
    
    # État
    status = Column(Enum(TranscriptionStatus), nullable=False, default=TranscriptionStatus.PENDING)
    current_step = Column(String(50))
    progress = Column(Integer, default=0)
    
    # Résultats
    raw_transcript = Column(Text)
    transcript_text = Column(Text)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    
    # Relation
    user = relationship("User", back_populates="transcriptions")
    
    __table_args__ = (
        Index("idx_transcriptions_user_id", "user_id"),
        Index("idx_transcriptions_status", "status"),
        Index("idx_transcriptions_created_at", "created_at"),
    )
```

#### Ajouter relation dans User model

```python
# backend/app/models/user.py

# Dans la classe User, ajouter:
transcriptions = relationship("Transcription", back_populates="user")
```

#### Créer migration Alembic

```bash
cd backend
alembic revision --autogenerate -m "add transcriptions table"
```

**Vérifier le fichier de migration généré** :
```bash
# backend/alembic/versions/xxx_add_transcriptions_table.py
# S'assurer que la migration contient bien:
# - CREATE TYPE transcriptionstatus
# - CREATE TABLE transcriptions
# - CREATE INDEX ...
```

#### Appliquer la migration

```bash
alembic upgrade head
```

#### ✅ Test Étape 1.1

```bash
# Vérifier que la table existe
psql -h localhost -U saas_ia_user -d saas_ia -p 5435
\dt transcriptions
\d transcriptions
\q
```

---

### Étape 1.2 : Schemas Pydantic (30min)

```bash
mkdir -p backend/app/modules/transcription
touch backend/app/modules/transcription/schemas.py
```

```python
# backend/app/modules/transcription/schemas.py

from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
from app.models.transcription import TranscriptionStatus

class TranscriptionCreateRequest(BaseModel):
    """Requête de création de transcription"""
    youtube_url: str = Field(..., min_length=10, max_length=500)
    language: str = Field(default="auto", pattern="^(auto|fr|en|ar)$")
    
    @validator('youtube_url')
    def validate_youtube_url(cls, v):
        if not ('youtube.com/' in v or 'youtu.be/' in v):
            raise ValueError("URL YouTube invalide")
        return v

class TranscriptionResponse(BaseModel):
    """Réponse création transcription"""
    id: str
    status: TranscriptionStatus
    youtube_url: str
    video_title: Optional[str]
    message: str
    
    class Config:
        from_attributes = True

class TranscriptionStatusResponse(BaseModel):
    """Réponse statut transcription"""
    id: str
    status: TranscriptionStatus
    progress: int
    current_step: Optional[str]
    youtube_url: str
    video_title: Optional[str]
    transcript_text: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True
```

#### ✅ Test Étape 1.2

```python
# Test rapide dans Python REPL
python
>>> from app.modules.transcription.schemas import TranscriptionCreateRequest
>>> req = TranscriptionCreateRequest(youtube_url="https://youtube.com/watch?v=test", language="fr")
>>> print(req)
>>> exit()
```

---

### Étape 1.3 : Setup Celery (1h30)

#### Créer configuration Celery

```bash
touch backend/app/celery_app.py
```

```python
# backend/app/celery_app.py

from celery import Celery
from app.config import settings

celery_app = Celery(
    "saas_ia",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.modules.transcription.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 heure max
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)
```

#### Créer fichier tasks (vide pour l'instant)

```bash
touch backend/app/modules/transcription/tasks.py
```

```python
# backend/app/modules/transcription/tasks.py

from app.celery_app import celery_app

# Tasks will be added in Day 4
```

#### Ajouter dépendances

```bash
cd backend
poetry add celery redis
```

#### Créer script de démarrage Celery

```bash
# backend/start-celery.sh (Linux/Mac)
#!/bin/bash
celery -A app.celery_app worker --loglevel=info

# backend/start-celery.bat (Windows)
celery -A app.celery_app worker --loglevel=info
```

```bash
chmod +x backend/start-celery.sh
```

#### ✅ Test Étape 1.3

```bash
# Terminal 1: Démarrer Redis
docker-compose up -d redis

# Terminal 2: Démarrer Celery worker
cd backend
./start-celery.sh  # ou start-celery.bat sur Windows

# Vérifier logs: devrait afficher "celery@hostname ready"
```

---

### Étape 1.4 : Setup Tests (1h)

```bash
cd backend
poetry add --group dev pytest pytest-asyncio pytest-cov httpx
mkdir -p tests/unit tests/integration
touch tests/conftest.py
```

```python
# tests/conftest.py

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.auth import get_password_hash
import uuid

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://saas_ia_user:saas_ia_dev_password@localhost:5435/saas_ia_test"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    # Créer tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Nettoyer
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def session(engine):
    SessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with SessionLocal() as session:
        yield session

@pytest.fixture
async def test_user(session):
    user = User(
        id=uuid.uuid4(),
        email="test@test.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
```

#### Créer test de base

```python
# tests/unit/test_schemas.py

from app.modules.transcription.schemas import TranscriptionCreateRequest
import pytest

def test_valid_youtube_url():
    req = TranscriptionCreateRequest(
        youtube_url="https://www.youtube.com/watch?v=test123",
        language="fr"
    )
    assert req.youtube_url == "https://www.youtube.com/watch?v=test123"

def test_invalid_youtube_url():
    with pytest.raises(ValueError, match="URL YouTube invalide"):
        TranscriptionCreateRequest(
            youtube_url="https://not-youtube.com/video",
            language="fr"
        )
```

#### ✅ Test Étape 1.4

```bash
cd backend
pytest tests/unit/test_schemas.py -v
# Devrait passer avec succès
```

---

### 📊 Checkpoint Jour 1

✅ **Livrables** :
- [x] Modèle Transcription créé
- [x] Migration Alembic appliquée
- [x] Schemas Pydantic définis
- [x] Celery configuré et fonctionnel
- [x] Tests unitaires de base

**Commandes de vérification** :
```bash
# DB
psql -h localhost -U saas_ia_user -d saas_ia -p 5435 -c "\dt transcriptions"

# Celery
celery -A app.celery_app inspect active

# Tests
pytest tests/ -v
```

---

## 📋 JOUR 2 : SERVICES CORE (6-8h)

### Étape 2.1 : YouTube Service (2h)

#### Installer dépendances

```bash
cd backend
poetry add yt-dlp
```

#### Créer le service

```bash
touch backend/app/modules/transcription/youtube_service.py
```

```python
# backend/app/modules/transcription/youtube_service.py

import yt_dlp
import os
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        self.download_dir = Path("/tmp/youtube_downloads")
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def download_audio(self, youtube_url: str) -> str:
        """Télécharge et extrait l'audio d'une vidéo YouTube"""
        
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
                
                logger.info(f"Audio downloaded: {audio_path}")
                return str(audio_path)
                
        except Exception as e:
            logger.error(f"Failed to download audio: {str(e)}")
            raise
    
    def get_video_info(self, youtube_url: str) -> Optional[Dict]:
        """Récupère les informations de la vidéo"""
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                return {
                    "title": info.get("title"),
                    "duration": info.get("duration"),
                    "channel": info.get("channel"),
                    "thumbnail": info.get("thumbnail"),
                }
        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            return None
    
    def cleanup(self, audio_path: str):
        """Supprime le fichier audio"""
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info(f"Cleaned up: {audio_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {audio_path}: {str(e)}")
```

#### ✅ Test Étape 2.1

```python
# tests/unit/test_youtube_service.py

import pytest
from unittest.mock import Mock, patch
from app.modules.transcription.youtube_service import YouTubeService

def test_get_video_info_mock():
    service = YouTubeService()
    
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        # Mock extract_info
        mock_instance = Mock()
        mock_instance.extract_info.return_value = {
            'title': 'Test Video',
            'duration': 120,
            'channel': 'Test Channel'
        }
        mock_ydl.return_value.__enter__.return_value = mock_instance
        
        info = service.get_video_info("https://youtube.com/watch?v=test")
        
        assert info['title'] == 'Test Video'
        assert info['duration'] == 120

# Test manuel (optionnel, avec vraie vidéo)
@pytest.mark.skip(reason="Requires real YouTube video")
def test_download_audio_real():
    service = YouTubeService()
    # Utiliser une courte vidéo de test
    audio_path = service.download_audio("https://youtube.com/watch?v=jNQXAC9IVRw")  # "Me at the zoo"
    assert os.path.exists(audio_path)
    service.cleanup(audio_path)
```

---

### Étape 2.2 : AI Transcription Service (2h)

#### Installer Assembly AI

```bash
poetry add assemblyai
```

#### Créer le service

```bash
touch backend/app/modules/transcription/ai_service.py
```

```python
# backend/app/modules/transcription/ai_service.py

import assemblyai as aai
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class TranscriptionAIService:
    def __init__(self):
        aai.settings.api_key = settings.ASSEMBLYAI_API_KEY
        self.transcriber = aai.Transcriber()
    
    def transcribe(self, audio_path: str, language: str = "auto") -> str:
        """Transcrit un fichier audio"""
        
        try:
            logger.info(f"Starting transcription: {audio_path}")
            
            config = aai.TranscriptionConfig(
                language_code=self._map_language(language),
                punctuate=True,
                format_text=True,
            )
            
            transcript = self.transcriber.transcribe(audio_path, config=config)
            
            if transcript.status == aai.TranscriptStatus.error:
                raise Exception(f"Transcription failed: {transcript.error}")
            
            logger.info(f"Transcription completed: {len(transcript.text)} chars")
            return transcript.text
            
        except Exception as e:
            logger.error(f"Transcription error: {str(e)}")
            raise
    
    def _map_language(self, language: str) -> str:
        mapping = {
            "fr": "fr",
            "en": "en",
            "ar": "ar",
            "auto": "en",
        }
        return mapping.get(language.lower(), "en")
```

#### Ajouter config

```python
# backend/app/config.py

class Settings(BaseSettings):
    # ... existing settings ...
    
    ASSEMBLYAI_API_KEY: str = "MOCK"  # Remplacer par vraie clé
```

#### ✅ Test Étape 2.2

```python
# tests/unit/test_ai_service.py

import pytest
from unittest.mock import Mock, patch
from app.modules.transcription.ai_service import TranscriptionAIService

def test_transcribe_mock():
    service = TranscriptionAIService()
    
    with patch.object(service.transcriber, 'transcribe') as mock_transcribe:
        # Mock transcript
        mock_transcript = Mock()
        mock_transcript.status = "completed"
        mock_transcript.text = "This is a test transcription"
        mock_transcribe.return_value = mock_transcript
        
        result = service.transcribe("/tmp/test.mp3", "en")
        
        assert result == "This is a test transcription"
```

---

### Étape 2.3 : Correction Service (2h)

```bash
touch backend/app/modules/transcription/correction_service.py
```

```python
# backend/app/modules/transcription/correction_service.py

import re
import logging

logger = logging.getLogger(__name__)

class CorrectionService:
    def correct_and_format(self, text: str, language: str) -> str:
        """Corrige et formate le texte"""
        
        logger.info(f"Starting text correction ({len(text)} chars)")
        
        text = self._normalize_spaces(text)
        text = self._remove_fillers(text, language)
        text = self._capitalize_sentences(text)
        text = self._format_punctuation(text)
        text = self._segment_paragraphs(text)
        
        logger.info(f"Text correction completed ({len(text)} chars)")
        return text
    
    def _normalize_spaces(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _remove_fillers(self, text: str, language: str) -> str:
        fillers = {
            "fr": [r'\beuh\b', r'\bhmm\b', r'\bhein\b'],
            "en": [r'\buh\b', r'\bum\b', r'\blike\b'],
            "ar": [r'\bيعني\b']
        }
        
        patterns = fillers.get(language, fillers["en"])
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return self._normalize_spaces(text)
    
    def _capitalize_sentences(self, text: str) -> str:
        sentences = re.split(r'([.!?]+\s+)', text)
        result = []
        
        for i, part in enumerate(sentences):
            if i % 2 == 0 and part:
                part = part[0].upper() + part[1:] if len(part) > 1 else part.upper()
            result.append(part)
        
        return ''.join(result)
    
    def _format_punctuation(self, text: str) -> str:
        text = re.sub(r'\s*([;:!?])', r' \1', text)
        text = re.sub(r"'\s+", "'", text)
        text = re.sub(r'([,.;:!?])([^\s\d])', r'\1 \2', text)
        return text
    
    def _segment_paragraphs(self, text: str, max_sentences: int = 5) -> str:
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
        
        if current_paragraph:
            paragraphs.append(''.join(current_paragraph).strip())
        
        return '\n\n'.join(paragraphs)
```

#### ✅ Test Étape 2.3

```python
# tests/unit/test_correction_service.py

from app.modules.transcription.correction_service import CorrectionService

def test_normalize_spaces():
    service = CorrectionService()
    text = "hello    world   !"
    result = service._normalize_spaces(text)
    assert result == "hello world !"

def test_capitalize_sentences():
    service = CorrectionService()
    text = "hello. world! how are you?"
    result = service._capitalize_sentences(text)
    assert result == "Hello. World! How are you?"

def test_full_correction():
    service = CorrectionService()
    text = "euh hello   world ! this is  a test . it works well ."
    result = service.correct_and_format(text, "en")
    
    assert "euh" not in result.lower()
    assert result.startswith("Hello")
    assert "\n\n" in result  # Paragraphs
```

---

### 📊 Checkpoint Jour 2

✅ **Livrables** :
- [x] YouTubeService implémenté et testé
- [x] TranscriptionAIService implémenté et testé
- [x] CorrectionService implémenté et testé
- [x] Tests unitaires pour tous les services

**Commandes de vérification** :
```bash
pytest tests/unit/ -v --cov=app/modules/transcription
```

---

## 📋 JOUR 3 : API BACKEND (4-6h)

### Étape 3.1 : Service Layer (2h)

```bash
touch backend/app/modules/transcription/service.py
```

```python
# backend/app/modules/transcription/service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.modules.transcription.models import Transcription, TranscriptionStatus
from app.modules.transcription.youtube_service import YouTubeService
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TranscriptionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.youtube_service = YouTubeService()
    
    async def create_transcription(
        self,
        youtube_url: str,
        language: str,
        user_id: uuid.UUID
    ) -> dict:
        """Crée une nouvelle transcription"""
        
        # Valider et récupérer infos vidéo
        video_info = self.youtube_service.get_video_info(youtube_url)
        if not video_info:
            raise ValueError("Impossible de récupérer les informations de la vidéo")
        
        # Créer transcription
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
        
        # TODO: Enqueue Celery task (Jour 4)
        logger.info(f"Transcription created: {transcription.id}")
        
        return {
            "id": str(transcription.id),
            "status": transcription.status,
            "youtube_url": youtube_url,
            "video_title": video_info.get("title"),
            "message": "Transcription démarrée avec succès"
        }
    
    async def get_transcription_status(
        self,
        transcription_id: str,
        user_id: uuid.UUID
    ) -> dict:
        """Récupère le statut d'une transcription"""
        
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
```

---

### Étape 3.2 : API Routes (2h)

```bash
touch backend/app/modules/transcription/routes.py
touch backend/app/modules/transcription/__init__.py
```

```python
# backend/app/modules/transcription/routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth import get_current_user
from app.models.user import User
from app.database import get_session
from app.modules.transcription.service import TranscriptionService
from app.modules.transcription.schemas import (
    TranscriptionCreateRequest,
    TranscriptionResponse,
    TranscriptionStatusResponse
)
from typing import List

router = APIRouter(prefix="/transcriptions", tags=["transcription"])

def get_transcription_service(
    session: AsyncSession = Depends(get_session)
) -> TranscriptionService:
    return TranscriptionService(session)

@router.post("/", response_model=TranscriptionResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_transcription(
    request: TranscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    service: TranscriptionService = Depends(get_transcription_service)
):
    """Démarre une nouvelle transcription YouTube"""
    
    try:
        result = await service.create_transcription(
            youtube_url=request.youtube_url,
            language=request.language,
            user_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/{transcription_id}", response_model=TranscriptionStatusResponse)
async def get_transcription_status(
    transcription_id: str,
    current_user: User = Depends(get_current_user),
    service: TranscriptionService = Depends(get_transcription_service)
):
    """Récupère le statut d'une transcription"""
    
    try:
        result = await service.get_transcription_status(
            transcription_id=transcription_id,
            user_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/", response_model=List[TranscriptionResponse])
async def list_transcriptions(
    current_user: User = Depends(get_current_user),
    service: TranscriptionService = Depends(get_transcription_service),
    skip: int = 0,
    limit: int = 20
):
    """Liste toutes les transcriptions de l'utilisateur"""
    
    result = await service.list_transcriptions(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return result
```

#### Enregistrer router dans main.py

```python
# backend/app/main.py

from app.modules.transcription.routes import router as transcription_router

# Ajouter après les autres routers
app.include_router(transcription_router, prefix="/api")
```

#### ✅ Test Étape 3.2

```bash
# Démarrer backend
cd backend
uvicorn app.main:app --reload --port 8004

# Ouvrir Swagger UI
# http://localhost:8004/docs

# Tester POST /api/transcriptions/ (nécessite JWT token)
```

---

### Étape 3.3 : Rate Limiting (1h)

```python
# backend/app/modules/transcription/routes.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/", response_model=TranscriptionResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/hour")  # Max 10 transcriptions/heure
async def create_transcription(...):
    ...
```

---

### 📊 Checkpoint Jour 3

✅ **Livrables** :
- [x] TranscriptionService implémenté
- [x] Routes API créées et documentées
- [x] Rate limiting activé
- [x] Tests d'intégration

---

## 📋 JOUR 4 : TASKS ASYNCHRONES (4-6h)

*[Suite du document avec Jour 4, 5, 6, et 7]*

---

## ✅ CHECKLIST COMPLÈTE

### Backend Core
- [ ] Modèles SQLAlchemy
- [ ] Migration Alembic
- [ ] Schemas Pydantic
- [ ] YouTubeService
- [ ] TranscriptionAIService
- [ ] CorrectionService
- [ ] TranscriptionService
- [ ] API Routes
- [ ] Celery Tasks

### Frontend
- [ ] Page transcription
- [ ] Form validation
- [ ] Progress tracking
- [ ] Result display
- [ ] Error handling

### Tests
- [ ] Tests unitaires (≥85% coverage)
- [ ] Tests d'intégration
- [ ] Tests E2E

### Infrastructure
- [ ] Docker Compose
- [ ] Celery workers
- [ ] Redis
- [ ] Variables d'environnement

### Documentation
- [ ] README module
- [ ] API documentation
- [ ] User guide

---

**Document créé par** : Assistant IA  
**Date** : 2025-11-14  
**Version** : 1.0.0 (Jours 1-3 détaillés)

*Note: Les jours 4-7 seront détaillés dans la prochaine version du document pour éviter qu'il soit trop long.*
