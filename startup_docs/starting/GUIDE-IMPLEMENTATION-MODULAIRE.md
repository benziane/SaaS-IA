# 🚀 Guide d'Implémentation - Architecture Modulaire SaaS IA

## 📋 Vue d'Ensemble

Ce guide vous accompagne pas-à-pas dans l'implémentation de l'architecture modulaire scalable pour votre plateforme SaaS IA.

**Objectif**: Construire un système où ajouter une nouvelle fonctionnalité IA prend 1 heure au lieu de 1 semaine.

---

## 🎯 Phase 0: Setup Initial (Jour 1)

### Étape 1: Structure de Base

```bash
# Créer la structure du projet
mkdir -p ai-saas-platform/{backend,frontend,nginx,monitoring,docs}
cd ai-saas-platform/backend

# Structure backend
mkdir -p app/{api/v1,models,schemas,services,ai/{modules,providers},core,tasks,middleware,utils}
mkdir -p app/ai/modules/{transcription,summarization,translation,analysis}
mkdir -p tests/{unit,integration,e2e,performance}
mkdir -p scripts migrations
```

### Étape 2: Fichiers Core Essentiels

#### 1. Base Module Interface

```python
# app/ai/base_module.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class ModuleMetadata(BaseModel):
    """Métadonnées standardisées pour chaque module"""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str] = []
    endpoints: List[str] = []
    permissions_required: List[str] = []
    events_emitted: List[str] = []
    events_subscribed: List[str] = []

class ModuleHealth(BaseModel):
    """État de santé d'un module"""
    status: str  # "healthy" | "degraded" | "unhealthy"
    dependencies_ok: bool
    last_check: str
    metrics: Dict[str, Any] = {}

class BaseAIModule(ABC):
    """
    Interface abstraite pour tous les modules IA.
    Chaque module DOIT implémenter ces méthodes.
    """
    
    @abstractmethod
    def get_metadata(self) -> ModuleMetadata:
        """Retourne les métadonnées du module"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialise le module (connexions, ressources, etc.)
        Retourne True si succès, False sinon
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """Arrête proprement le module"""
        pass
    
    @abstractmethod
    async def health_check(self) -> ModuleHealth:
        """Vérifie la santé du module et de ses dépendances"""
        pass
    
    @abstractmethod
    def get_router(self) -> "APIRouter":
        """Retourne le routeur FastAPI du module"""
        pass
    
    @abstractmethod
    def register_events(self, event_bus: "EventBus") -> None:
        """Enregistre les handlers d'événements"""
        pass
    
    @abstractmethod
    async def process(self, request: BaseModel) -> BaseModel:
        """Méthode principale de traitement du module"""
        pass
    
    # Méthodes optionnelles
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques du module"""
        return {}
    
    def get_config_schema(self) -> Optional[Dict]:
        """Retourne le schéma de configuration JSON Schema"""
        return None
```

#### 2. Event Bus (Communication Inter-Modules)

```python
# app/core/event_bus.py

from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Représente un événement dans le système"""
    name: str
    data: Dict[str, Any]
    source_module: str
    timestamp: datetime
    correlation_id: Optional[str] = None

class EventBus:
    """
    Bus d'événements central.
    Permet aux modules de communiquer sans se connaître.
    """
    
    def __init__(self, redis_client: Optional[Any] = None):
        self._handlers: Dict[str, List[Callable]] = {}
        self._redis = redis_client
        self._event_history: List[Event] = []
        
    def subscribe(self, event_name: str, handler: Callable) -> None:
        """Enregistre un handler pour un événement"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        
        self._handlers[event_name].append(handler)
        logger.debug(f"📡 Handler enregistré pour: {event_name}")
    
    def on(self, event_name: str):
        """Décorateur pour enregistrer un handler facilement"""
        def decorator(func: Callable):
            self.subscribe(event_name, func)
            return func
        return decorator
    
    async def publish(
        self, 
        event_name: str, 
        data: Dict[str, Any],
        source_module: str,
        correlation_id: Optional[str] = None
    ) -> None:
        """Publie un événement (appelle tous les handlers)"""
        event = Event(
            name=event_name,
            data=data,
            source_module=source_module,
            timestamp=datetime.utcnow(),
            correlation_id=correlation_id
        )
        
        # Historique limité
        self._event_history.append(event)
        if len(self._event_history) > 1000:
            self._event_history.pop(0)
        
        logger.info(f"📡 Événement publié: {event_name} (source: {source_module})")
        
        # Appel des handlers
        if event_name in self._handlers:
            for handler in self._handlers[event_name]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"❌ Erreur handler {handler.__name__}: {e}")
        
        # Publication Redis (multi-instance)
        if self._redis:
            await self._redis.publish(
                f"events:{event_name}",
                json.dumps({
                    "name": event.name,
                    "data": event.data,
                    "source_module": event.source_module,
                    "timestamp": event.timestamp.isoformat(),
                    "correlation_id": event.correlation_id
                })
            )

# Instance globale
event_bus = EventBus()
```

#### 3. Service Registry (Découverte de Services)

```python
# app/core/service_registry.py

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
import asyncio
import logging

logger = logging.getLogger(__name__)

class ModuleRegistration(BaseModel):
    """Enregistrement d'un module dans le registre"""
    name: str
    version: str
    endpoints: List[str]
    status: str  # "initializing" | "healthy" | "degraded" | "unhealthy"
    registered_at: datetime
    last_heartbeat: datetime

class ServiceRegistry:
    """
    Registre central des modules actifs.
    Permet la découverte dynamique des services.
    """
    
    def __init__(self, redis_client=None):
        self._modules: Dict[str, ModuleRegistration] = {}
        self._redis = redis_client
        
    async def register_module(
        self, 
        module: "BaseAIModule",
        endpoints: List[str],
        health_check_interval: int = 30
    ) -> bool:
        """Enregistre un nouveau module"""
        metadata = module.get_metadata()
        
        registration = ModuleRegistration(
            name=metadata.name,
            version=metadata.version,
            endpoints=endpoints,
            status="initializing",
            registered_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        
        self._modules[metadata.name] = registration
        
        # Enregistrement Redis (optionnel)
        if self._redis:
            await self._redis.hset(
                "service:registry",
                metadata.name,
                registration.json()
            )
        
        # Health check loop
        asyncio.create_task(
            self._health_check_loop(module, health_check_interval)
        )
        
        logger.info(f"✅ Module enregistré: {metadata.name}")
        return True
    
    async def unregister_module(self, module_name: str) -> bool:
        """Désenregistre un module"""
        if module_name in self._modules:
            del self._modules[module_name]
            if self._redis:
                await self._redis.hdel("service:registry", module_name)
            logger.info(f"✅ Module désenregistré: {module_name}")
            return True
        return False
    
    async def get_module(self, module_name: str) -> Optional[ModuleRegistration]:
        """Récupère les infos d'un module"""
        return self._modules.get(module_name)
    
    async def list_modules(self, status: Optional[str] = None) -> List[ModuleRegistration]:
        """Liste tous les modules (avec filtre optionnel)"""
        modules = list(self._modules.values())
        if status:
            modules = [m for m in modules if m.status == status]
        return modules
    
    async def discover_endpoints(self) -> Dict[str, List[str]]:
        """Retourne tous les endpoints disponibles par module"""
        return {
            name: reg.endpoints
            for name, reg in self._modules.items()
            if reg.status == "healthy"
        }
    
    async def _health_check_loop(self, module: "BaseAIModule", interval: int):
        """Boucle de vérification de santé périodique"""
        metadata = module.get_metadata()
        
        while metadata.name in self._modules:
            try:
                health = await module.health_check()
                registration = self._modules[metadata.name]
                registration.status = health.status
                registration.last_heartbeat = datetime.utcnow()
                
                if self._redis:
                    await self._redis.hset(
                        "service:registry",
                        metadata.name,
                        registration.json()
                    )
                    
            except Exception as e:
                logger.error(f"❌ Health check échoué pour {metadata.name}: {e}")
                self._modules[metadata.name].status = "unhealthy"
            
            await asyncio.sleep(interval)
```

#### 4. Module Orchestrator (Gestion du Cycle de Vie)

```python
# app/core/module_orchestrator.py

from typing import Dict, List, Optional
from pathlib import Path
from importlib import import_module
import yaml
import logging

logger = logging.getLogger(__name__)

class ModuleOrchestrator:
    """
    Orchestrateur qui gère le cycle de vie de tous les modules.
    - Découverte automatique
    - Chargement dynamique
    - Initialisation
    - Arrêt propre
    """
    
    def __init__(self, service_registry: "ServiceRegistry"):
        self.service_registry = service_registry
        self.modules: Dict[str, "BaseAIModule"] = {}
        self.app: Optional["FastAPI"] = None
        
    async def discover_modules(self, modules_path: Path) -> List[str]:
        """
        Découvre automatiquement tous les modules.
        Cherche les dossiers contenant un manifest.yaml
        """
        discovered = []
        
        for module_dir in modules_path.iterdir():
            if module_dir.is_dir():
                manifest_path = module_dir / "manifest.yaml"
                if manifest_path.exists():
                    discovered.append(module_dir.name)
                    logger.info(f"📦 Module découvert: {module_dir.name}")
        
        return discovered
    
    async def load_module(
        self, 
        module_name: str, 
        modules_path: Path
    ) -> Optional["BaseAIModule"]:
        """
        Charge un module dynamiquement.
        1. Lit le manifest.yaml
        2. Importe le package Python
        3. Instancie la classe
        """
        module_dir = modules_path / module_name
        manifest_path = module_dir / "manifest.yaml"
        
        if not manifest_path.exists():
            logger.error(f"❌ Manifest introuvable: {module_name}")
            return None
        
        try:
            # Lecture manifest
            with open(manifest_path) as f:
                manifest = yaml.safe_load(f)
            
            # Import dynamique
            module_package = import_module(f"app.ai.modules.{module_name}")
            module_class = getattr(module_package, manifest.get("class_name"))
            
            # Instanciation
            module_instance = module_class()
            
            logger.info(f"✅ Module chargé: {module_name} v{manifest['version']}")
            return module_instance
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement {module_name}: {e}")
            return None
    
    async def initialize_module(
        self, 
        module: "BaseAIModule", 
        event_bus: "EventBus"
    ) -> bool:
        """
        Initialise un module :
        1. Appelle initialize()
        2. Enregistre dans le service registry
        3. Monte le routeur FastAPI
        4. Enregistre les événements
        """
        metadata = module.get_metadata()
        
        try:
            # 1. Initialisation
            success = await module.initialize()
            if not success:
                return False
            
            # 2. Enregistrement
            await self.service_registry.register_module(
                module=module,
                endpoints=metadata.endpoints
            )
            
            # 3. Montage du routeur
            if self.app:
                router = module.get_router()
                self.app.include_router(
                    router,
                    prefix=f"/api/v1/modules/{metadata.name}",
                    tags=[metadata.name]
                )
            
            # 4. Événements
            module.register_events(event_bus)
            
            # 5. Stockage
            self.modules[metadata.name] = module
            
            logger.info(f"✅ Module initialisé: {metadata.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation {metadata.name}: {e}")
            return False
    
    async def start_all_modules(
        self, 
        app: "FastAPI", 
        event_bus: "EventBus",
        modules_path: Path = Path("app/ai/modules")
    ) -> Dict[str, bool]:
        """Démarre tous les modules automatiquement"""
        self.app = app
        results = {}
        
        # Découverte
        module_names = await self.discover_modules(modules_path)
        logger.info(f"🔍 {len(module_names)} modules découverts")
        
        # Chargement et initialisation
        for module_name in module_names:
            module = await self.load_module(module_name, modules_path)
            
            if module:
                success = await self.initialize_module(module, event_bus)
                results[module_name] = success
            else:
                results[module_name] = False
        
        # Résumé
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"✅ {success_count}/{len(module_names)} modules démarrés")
        
        return results
    
    async def stop_all_modules(self) -> None:
        """Arrête proprement tous les modules"""
        for name, module in self.modules.items():
            try:
                await module.shutdown()
                await self.service_registry.unregister_module(name)
                logger.info(f"✅ Module arrêté: {name}")
            except Exception as e:
                logger.error(f"❌ Erreur arrêt {name}: {e}")
    
    async def reload_module(self, module_name: str) -> bool:
        """Recharge un module à chaud (hot reload)"""
        if module_name not in self.modules:
            return False
        
        # Arrêt
        old_module = self.modules[module_name]
        await old_module.shutdown()
        await self.service_registry.unregister_module(module_name)
        
        # Rechargement
        modules_path = Path("app/ai/modules")
        new_module = await self.load_module(module_name, modules_path)
        
        if new_module:
            from app.core.event_bus import event_bus
            return await self.initialize_module(new_module, event_bus)
        
        return False
```

---

## 🎯 Phase 1: Premier Module (Transcription) (Jour 2-3)

### Étape 1: Structure du Module

```bash
cd app/ai/modules/transcription
touch manifest.yaml __init__.py config.py models.py schemas.py
touch routes.py service.py tasks.py events.py utils.py dependencies.py
mkdir tests
```

### Étape 2: Manifest du Module

```yaml
# app/ai/modules/transcription/manifest.yaml

name: transcription
version: 1.0.0
description: Module de transcription automatique de vidéos YouTube
author: AI SaaS Platform Team
class_name: TranscriptionModule

dependencies:
  - celery
  - redis
  - yt-dlp
  - assemblyai

endpoints:
  - /transcribe
  - /status/{job_id}
  - /list
  - /download/{transcription_id}

permissions_required:
  - transcription:create
  - transcription:read
  - transcription:delete

events_emitted:
  - transcription.started
  - transcription.progress
  - transcription.completed
  - transcription.failed

events_subscribed:
  - video.uploaded
  - user.deleted

resources:
  cpu: "1"
  memory: "2Gi"

configuration:
  max_video_duration: 7200
  supported_languages:
    - en
    - fr
    - es
    - ar
  ai_providers:
    primary: assemblyai
    fallback: whisper
```

### Étape 3: Implémentation du Module

```python
# app/ai/modules/transcription/__init__.py

from app.ai.base_module import BaseAIModule, ModuleMetadata, ModuleHealth
from app.ai.modules.transcription.routes import router
from app.ai.modules.transcription.service import TranscriptionService
from fastapi import APIRouter
import yaml
from pathlib import Path

class TranscriptionModule(BaseAIModule):
    """Module de transcription YouTube"""
    
    def __init__(self):
        self.service = None
        self.router = router
        self._metadata = self._load_metadata()
        
    def _load_metadata(self) -> ModuleMetadata:
        """Charge les métadonnées depuis manifest.yaml"""
        manifest_path = Path(__file__).parent / "manifest.yaml"
        with open(manifest_path) as f:
            data = yaml.safe_load(f)
        
        return ModuleMetadata(**data)
    
    def get_metadata(self) -> ModuleMetadata:
        return self._metadata
    
    async def initialize(self) -> bool:
        """Initialise le module"""
        try:
            self.service = TranscriptionService()
            await self.service.initialize()
            return True
        except Exception as e:
            logger.error(f"Erreur init: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Arrête le module"""
        if self.service:
            await self.service.shutdown()
        return True
    
    async def health_check(self) -> ModuleHealth:
        """Vérifie la santé"""
        dependencies_ok = True
        
        try:
            # Test connexions
            await self.service.test_assemblyai_connection()
            await self.service.test_celery_connection()
        except Exception:
            dependencies_ok = False
        
        return ModuleHealth(
            status="healthy" if dependencies_ok else "degraded",
            dependencies_ok=dependencies_ok,
            last_check=datetime.utcnow().isoformat(),
            metrics=self.get_metrics()
        )
    
    def get_router(self) -> APIRouter:
        return self.router
    
    def register_events(self, event_bus):
        """Enregistre les événements"""
        from app.ai.modules.transcription.events import register_handlers
        register_handlers(event_bus, self.service)
    
    async def process(self, request):
        """Traite une requête"""
        return await self.service.process_transcription(request)
    
    def get_metrics(self):
        """Métriques du module"""
        return {
            "total_transcriptions": self.service.get_total_count(),
            "pending_jobs": self.service.get_pending_count()
        }

# Point d'entrée pour le chargement
def load_module() -> BaseAIModule:
    return TranscriptionModule()
```

### Étape 4: Service Métier

```python
# app/ai/modules/transcription/service.py

from app.ai.modules.transcription.models import TranscriptionJob
from app.ai.providers.assemblyai_provider import AssemblyAIProvider
from app.core.event_bus import event_bus
import yt_dlp

class TranscriptionService:
    """Service de transcription"""
    
    def __init__(self):
        self.assemblyai = AssemblyAIProvider()
        
    async def initialize(self):
        """Initialise les providers"""
        await self.assemblyai.initialize()
    
    async def shutdown(self):
        """Arrête les providers"""
        await self.assemblyai.shutdown()
    
    async def start_transcription(
        self, 
        youtube_url: str, 
        user_id: str,
        language: str = "auto"
    ) -> TranscriptionJob:
        """
        Démarre une transcription.
        1. Crée un job
        2. Lance la tâche Celery
        3. Émet un événement
        """
        # Création du job
        job = TranscriptionJob(
            youtube_url=youtube_url,
            user_id=user_id,
            language=language,
            status="pending"
        )
        await job.save()
        
        # Tâche async
        from app.ai.modules.transcription.tasks import process_transcription_task
        process_transcription_task.delay(job.id)
        
        # Événement
        await event_bus.publish(
            event_name="transcription.started",
            data={
                "job_id": str(job.id),
                "user_id": user_id,
                "youtube_url": youtube_url
            },
            source_module="transcription",
            correlation_id=f"trans-{job.id}"
        )
        
        return job
    
    async def process_transcription_sync(self, job_id: str):
        """Traitement synchrone (appelé par Celery)"""
        job = await TranscriptionJob.get(job_id)
        
        try:
            # 1. Extraction audio YouTube
            audio_path = await self._extract_youtube_audio(job.youtube_url)
            
            # 2. Upload Assembly AI
            audio_url = await self.assemblyai.upload_file(audio_path)
            
            # 3. Transcription
            transcript_id = await self.assemblyai.transcribe(
                audio_url=audio_url,
                language_code=job.language
            )
            
            # 4. Polling + événements de progression
            while True:
                status = await self.assemblyai.get_status(transcript_id)
                
                if status["status"] == "completed":
                    raw_text = status["text"]
                    corrected_text = await self._correct_text(raw_text)
                    
                    # Sauvegarde
                    transcription = Transcription(
                        job_id=job.id,
                        user_id=job.user_id,
                        raw_text=raw_text,
                        corrected_text=corrected_text
                    )
                    await transcription.save()
                    
                    job.status = "completed"
                    job.transcription_id = transcription.id
                    await job.save()
                    
                    # Événement de succès
                    await event_bus.publish(
                        event_name="transcription.completed",
                        data={
                            "job_id": str(job.id),
                            "transcription_id": str(transcription.id)
                        },
                        source_module="transcription"
                    )
                    break
                    
                elif status["status"] == "error":
                    raise Exception(status["error"])
                
                else:
                    # Progression
                    await event_bus.publish(
                        event_name="transcription.progress",
                        data={
                            "job_id": str(job.id),
                            "status": status["status"],
                            "progress": status.get("progress", 0)
                        },
                        source_module="transcription"
                    )
                    await asyncio.sleep(3)
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            await job.save()
            
            await event_bus.publish(
                event_name="transcription.failed",
                data={"job_id": str(job.id), "error": str(e)},
                source_module="transcription"
            )
    
    async def _extract_youtube_audio(self, youtube_url: str) -> str:
        """Extrait l'audio avec yt-dlp"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'outtmpl': '/tmp/%(id)s.%(ext)s',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            return f"/tmp/{info['id']}.mp3"
    
    async def _correct_text(self, raw_text: str) -> str:
        """Corrige le texte (LanguageTool ou GPT)"""
        # TODO: Implémenter correction
        return raw_text
```

### Étape 5: Routes API

```python
# app/ai/modules/transcription/routes.py

from fastapi import APIRouter, Depends, HTTPException
from app.ai.modules.transcription.service import TranscriptionService
from app.ai.modules.transcription.schemas import (
    TranscriptionRequest,
    JobStatusResponse
)

router = APIRouter()

def get_service():
    # TODO: Récupérer depuis app.state
    return TranscriptionService()

@router.post("/transcribe", response_model=JobStatusResponse)
async def create_transcription(
    request: TranscriptionRequest,
    service: TranscriptionService = Depends(get_service),
    current_user = Depends(get_current_user)
):
    """Démarre une transcription YouTube"""
    job = await service.start_transcription(
        youtube_url=request.youtube_url,
        user_id=current_user.id,
        language=request.language
    )
    return JobStatusResponse.from_orm(job)

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user = Depends(get_current_user)
):
    """Récupère le statut d'un job"""
    job = await TranscriptionJob.get(job_id)
    
    if not job:
        raise HTTPException(404, "Job non trouvé")
    
    if job.user_id != current_user.id:
        raise HTTPException(403, "Accès refusé")
    
    return JobStatusResponse.from_orm(job)

@router.get("/list", response_model=List[JobStatusResponse])
async def list_transcriptions(
    current_user = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20
):
    """Liste les transcriptions de l'utilisateur"""
    jobs = await TranscriptionJob.find(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return [JobStatusResponse.from_orm(job) for job in jobs]
```

---

## 🚀 Phase 2: Intégration dans FastAPI (Jour 4)

### Point d'Entrée Principal

```python
# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.module_orchestrator import ModuleOrchestrator
from app.core.service_registry import ServiceRegistry
from app.core.event_bus import event_bus
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    
    logger.info("🚀 Démarrage de l'application...")
    
    # 1. Service Registry
    service_registry = ServiceRegistry()
    app.state.service_registry = service_registry
    
    # 2. Event Bus
    app.state.event_bus = event_bus
    
    # 3. Module Orchestrator
    orchestrator = ModuleOrchestrator(service_registry)
    app.state.orchestrator = orchestrator
    
    # 4. Démarrage de tous les modules
    results = await orchestrator.start_all_modules(
        app=app,
        event_bus=event_bus,
        modules_path=Path("app/ai/modules")
    )
    
    # 5. Résumé
    success = sum(1 for v in results.values() if v)
    logger.info(f"✅ {success}/{len(results)} modules démarrés")
    
    yield
    
    # Shutdown
    logger.info("🛑 Arrêt...")
    await orchestrator.stop_all_modules()

# Application FastAPI
app = FastAPI(
    title="AI SaaS Platform",
    version="2.0.0",
    lifespan=lifespan
)

# Routes core (non-modules)
from app.api.v1 import auth, users
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

# Les routes des modules sont ajoutées dynamiquement !
```

---

## 🎯 Phase 3: Ajouter un Nouveau Module (15 minutes !)

### Exemple: Module de Résumé

```bash
# 1. Créer la structure
mkdir -p app/ai/modules/summarization
cd app/ai/modules/summarization

# 2. Copier le template
cp -r ../transcription/* .

# 3. Adapter manifest.yaml
cat > manifest.yaml << EOF
name: summarization
version: 1.0.0
description: Module de résumé de texte avec IA
author: AI SaaS Team
class_name: SummarizationModule

dependencies:
  - openai
  - redis

endpoints:
  - /summarize
  - /status/{job_id}

permissions_required:
  - summarization:create

events_emitted:
  - summarization.started
  - summarization.completed
EOF

# 4. Adapter le code
# - Renommer TranscriptionModule -> SummarizationModule
# - Adapter la logique métier

# 5. Redémarrer l'app
# Le module est automatiquement découvert et intégré ! 🎉
```

---

## 📊 Checklist de Déploiement

```yaml
✅ Backend Core:
  - [ ] BaseAIModule implémenté
  - [ ] EventBus fonctionnel
  - [ ] ServiceRegistry opérationnel
  - [ ] ModuleOrchestrator déployé
  - [ ] FastAPI main.py configuré

✅ Module Transcription:
  - [ ] manifest.yaml créé
  - [ ] TranscriptionModule implémente BaseAIModule
  - [ ] Service métier fonctionnel
  - [ ] Routes API exposées
  - [ ] Événements configurés
  - [ ] Tests unitaires passent

✅ Infrastructure:
  - [ ] Docker Compose configuré
  - [ ] PostgreSQL + Redis démarrés
  - [ ] Celery workers actifs
  - [ ] Nginx configuré

✅ Monitoring:
  - [ ] Prometheus metrics
  - [ ] Grafana dashboards
  - [ ] Health checks actifs

✅ Documentation:
  - [ ] README.md complet
  - [ ] API docs générées
  - [ ] Guide d'ajout de module
```

---

## 🎓 Patterns et Bonnes Pratiques

### ✅ Pattern 1: Module Autonome

```
Chaque module doit être :
- Auto-contenu (dépendances dans manifest.yaml)
- Testable isolément
- Déployable indépendamment
- Documenté (README.md)
```

### ✅ Pattern 2: Communication par Événements

```python
# ❌ MAUVAIS: Couplage fort
from app.ai.modules.notification import NotificationService
notification_service.send(...)

# ✅ BON: Découplage par événements
await event_bus.publish(
    event_name="transcription.completed",
    data={...},
    source_module="transcription"
)
```

### ✅ Pattern 3: Health Checks Robustes

```python
async def health_check(self) -> ModuleHealth:
    """Vérifie TOUTES les dépendances"""
    checks = {
        "database": await self._check_database(),
        "redis": await self._check_redis(),
        "external_api": await self._check_external_api()
    }
    
    all_ok = all(checks.values())
    
    return ModuleHealth(
        status="healthy" if all_ok else "degraded",
        dependencies_ok=all_ok,
        last_check=datetime.utcnow().isoformat(),
        metrics={
            "checks": checks,
            **self.get_metrics()
        }
    )
```

### ✅ Pattern 4: Gestion d'Erreurs

```python
try:
    result = await self.process_something()
    
    await event_bus.publish(
        event_name="module.success",
        data={"result": result},
        source_module=self._metadata.name
    )
    
except Exception as e:
    logger.error(f"Erreur: {e}")
    
    await event_bus.publish(
        event_name="module.error",
        data={"error": str(e)},
        source_module=self._metadata.name
    )
    
    raise
```

---

## 🚀 Prochaines Étapes

### Court Terme (Semaine 1-2)
1. ✅ Implémenter les 4 fichiers core (base_module, event_bus, service_registry, orchestrator)
2. ✅ Créer le module de transcription complet
3. ✅ Tester le système de découverte automatique
4. ✅ Déployer avec Docker Compose

### Moyen Terme (Semaine 3-4)
1. 📝 Ajouter module de résumé
2. 🌐 Ajouter module de traduction
3. 📊 Dashboard admin pour gérer les modules
4. 🔄 CI/CD pour déploiement automatique

### Long Terme (Mois 2-3)
1. 🎯 5+ modules IA actifs
2. 🔍 Monitoring avancé (Grafana)
3. ⚡ Auto-scaling des workers
4. 🌍 Déploiement multi-région

---

## 💡 Tips & Astuces

### Debugging

```bash
# Voir les modules actifs
curl http://localhost:8000/api/v1/modules/list

# Health check d'un module
curl http://localhost:8000/api/v1/modules/transcription/health

# Voir l'historique des événements
curl http://localhost:8000/api/v1/events/history?event_name=transcription.completed
```

### Hot Reload d'un Module

```python
# Depuis un endpoint admin
@router.post("/admin/modules/{module_name}/reload")
async def reload_module(module_name: str):
    orchestrator = request.app.state.orchestrator
    success = await orchestrator.reload_module(module_name)
    return {"reloaded": success}
```

### Tests d'un Module

```python
# tests/unit/test_transcription_module.py

import pytest
from app.ai.modules.transcription import TranscriptionModule

@pytest.mark.asyncio
async def test_module_initialization():
    module = TranscriptionModule()
    success = await module.initialize()
    assert success == True

@pytest.mark.asyncio
async def test_health_check():
    module = TranscriptionModule()
    await module.initialize()
    health = await module.health_check()
    assert health.status == "healthy"
```

---

## 🎯 Objectif Final

**Atteindre cet état idéal** :

```
Développeur: Je veux ajouter une nouvelle fonctionnalité IA.

Actions:
1. mkdir app/ai/modules/nouvelle_feature
2. Copier le template
3. Adapter la logique
4. docker-compose restart backend

Résultat: Module intégré automatiquement ! ⚡

Temps total: 15 minutes au lieu de 2 jours 🚀
```

---

**Cette architecture transforme l'ajout de fonctionnalités IA d'un projet complexe en une opération simple et répétitive ! 🎉**
