# 📦 Templates & Code Snippets - Développement Rapide

## 🎯 Vue d'Ensemble

Ce document contient tous les templates de code prêts à l'emploi pour développer rapidement de nouveaux modules IA.

---

## 📋 Template 1: Module Complet (Copier-Coller)

### Structure à Créer

```bash
app/ai/modules/mon_nouveau_module/
├── manifest.yaml
├── __init__.py
├── config.py
├── models.py
├── schemas.py
├── routes.py
├── service.py
├── tasks.py
├── events.py
├── utils.py
├── dependencies.py
├── tests/
│   ├── test_service.py
│   ├── test_routes.py
│   └── test_events.py
└── README.md
```

---

## 1️⃣ manifest.yaml (Template)

```yaml
# app/ai/modules/mon_nouveau_module/manifest.yaml

name: mon_nouveau_module  # 🔴 À ADAPTER
version: 1.0.0
description: Description de mon module  # 🔴 À ADAPTER
author: Votre Nom  # 🔴 À ADAPTER
class_name: MonNouveauModule  # 🔴 À ADAPTER (CamelCase)

dependencies:
  - redis
  - celery
  # 🔴 AJOUTER vos dépendances spécifiques

endpoints:
  - /process  # 🔴 À ADAPTER selon vos besoins
  - /status/{job_id}
  - /list
  - /cancel/{job_id}

permissions_required:
  - mon_module:create  # 🔴 À ADAPTER
  - mon_module:read
  - mon_module:delete

events_emitted:
  - mon_module.started  # 🔴 À ADAPTER
  - mon_module.progress
  - mon_module.completed
  - mon_module.failed

events_subscribed:
  - user.deleted  # 🔴 À ADAPTER selon vos besoins
  # Exemples: file.uploaded, transcription.completed, etc.

resources:
  cpu: "1"
  memory: "2Gi"
  max_concurrent_jobs: 10

configuration:
  # 🔴 AJOUTER votre configuration spécifique
  timeout_seconds: 300
  retry_attempts: 3
  api_key_env: "MY_MODULE_API_KEY"
```

---

## 2️⃣ __init__.py (Template Module Principal)

```python
# app/ai/modules/mon_nouveau_module/__init__.py

from app.ai.base_module import BaseAIModule, ModuleMetadata, ModuleHealth
from app.ai.modules.mon_nouveau_module.routes import router
from app.ai.modules.mon_nouveau_module.service import MonNouveauService  # 🔴 À ADAPTER
from app.ai.modules.mon_nouveau_module.events import register_event_handlers
from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MonNouveauModule(BaseAIModule):  # 🔴 À ADAPTER le nom de classe
    """
    Module pour [DESCRIPTION DE VOTRE MODULE]  # 🔴 À ADAPTER
    
    Fonctionnalités:
    - Feature 1  # 🔴 À ADAPTER
    - Feature 2
    - Feature 3
    """
    
    def __init__(self):
        self.service = None
        self.router = router
        self._metadata = self._load_metadata()
        self._initialized = False
        
    def _load_metadata(self) -> ModuleMetadata:
        """Charge les métadonnées depuis manifest.yaml"""
        manifest_path = Path(__file__).parent / "manifest.yaml"
        
        try:
            with open(manifest_path) as f:
                data = yaml.safe_load(f)
            
            return ModuleMetadata(
                name=data["name"],
                version=data["version"],
                description=data["description"],
                author=data["author"],
                dependencies=data.get("dependencies", []),
                endpoints=data.get("endpoints", []),
                permissions_required=data.get("permissions_required", []),
                events_emitted=data.get("events_emitted", []),
                events_subscribed=data.get("events_subscribed", [])
            )
        except Exception as e:
            logger.error(f"Erreur chargement manifest: {e}")
            raise
    
    def get_metadata(self) -> ModuleMetadata:
        """Retourne les métadonnées du module"""
        return self._metadata
    
    async def initialize(self) -> bool:
        """
        Initialise le module et ses dépendances.
        
        Returns:
            bool: True si l'initialisation réussit
        """
        if self._initialized:
            logger.warning(f"Module {self._metadata.name} déjà initialisé")
            return True
        
        try:
            logger.info(f"Initialisation de {self._metadata.name}...")
            
            # 🔴 ADAPTER: Instancier votre service
            self.service = MonNouveauService()
            await self.service.initialize()
            
            self._initialized = True
            logger.info(f"✅ {self._metadata.name} initialisé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation {self._metadata.name}: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """
        Arrête proprement le module.
        
        Returns:
            bool: True si l'arrêt réussit
        """
        if not self._initialized:
            return True
        
        try:
            logger.info(f"Arrêt de {self._metadata.name}...")
            
            if self.service:
                await self.service.shutdown()
            
            self._initialized = False
            logger.info(f"✅ {self._metadata.name} arrêté")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur arrêt {self._metadata.name}: {e}")
            return False
    
    async def health_check(self) -> ModuleHealth:
        """
        Vérifie la santé du module et de ses dépendances.
        
        Returns:
            ModuleHealth: État de santé du module
        """
        dependencies_ok = True
        health_details = {}
        
        if not self._initialized:
            return ModuleHealth(
                status="unhealthy",
                dependencies_ok=False,
                last_check=datetime.utcnow().isoformat(),
                metrics={"error": "Module non initialisé"}
            )
        
        try:
            # 🔴 ADAPTER: Vérifier vos dépendances spécifiques
            # Exemple: API externe
            health_details["external_api"] = await self.service.test_api_connection()
            
            # Exemple: Redis
            health_details["redis"] = await self.service.test_redis_connection()
            
            # Exemple: Celery
            health_details["celery"] = await self.service.test_celery_connection()
            
            # Vérifier si toutes les dépendances sont OK
            dependencies_ok = all(health_details.values())
            
        except Exception as e:
            logger.error(f"Health check échoué: {e}")
            dependencies_ok = False
            health_details["error"] = str(e)
        
        # Déterminer le statut global
        if dependencies_ok:
            status = "healthy"
        elif any(health_details.values()):
            status = "degraded"  # Certaines dépendances OK
        else:
            status = "unhealthy"
        
        return ModuleHealth(
            status=status,
            dependencies_ok=dependencies_ok,
            last_check=datetime.utcnow().isoformat(),
            metrics={
                "dependencies": health_details,
                **self.get_metrics()
            }
        )
    
    def get_router(self) -> APIRouter:
        """Retourne le routeur FastAPI du module"""
        return self.router
    
    def register_events(self, event_bus: "EventBus") -> None:
        """
        Enregistre les handlers d'événements.
        
        Args:
            event_bus: Bus d'événements global
        """
        register_event_handlers(event_bus, self.service)
        logger.info(f"Événements enregistrés pour {self._metadata.name}")
    
    async def process(self, request: "BaseModel") -> "BaseModel":
        """
        Méthode principale de traitement du module.
        Peut être appelée directement sans passer par HTTP.
        
        Args:
            request: Requête à traiter
            
        Returns:
            Response du traitement
        """
        if not self._initialized:
            raise RuntimeError("Module non initialisé")
        
        # 🔴 ADAPTER: Appeler votre logique métier
        return await self.service.process_request(request)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Retourne les métriques du module.
        
        Returns:
            Dict contenant les métriques
        """
        if not self._initialized or not self.service:
            return {"initialized": False}
        
        # 🔴 ADAPTER: Retourner vos métriques spécifiques
        return {
            "initialized": True,
            "total_processed": self.service.get_total_count(),
            "pending_jobs": self.service.get_pending_count(),
            "failed_jobs": self.service.get_failed_count(),
            "average_duration_ms": self.service.get_avg_duration_ms(),
            "uptime_seconds": self.service.get_uptime_seconds()
        }
    
    def get_config_schema(self) -> Dict:
        """
        Retourne le schéma de configuration JSON Schema.
        Utilisé pour la validation et la génération d'UI admin.
        
        Returns:
            JSON Schema de configuration
        """
        # 🔴 ADAPTER: Définir votre schéma de config
        return {
            "type": "object",
            "properties": {
                "timeout_seconds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 3600,
                    "default": 300,
                    "description": "Timeout pour les requêtes"
                },
                "retry_attempts": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 10,
                    "default": 3,
                    "description": "Nombre de tentatives en cas d'échec"
                },
                "api_key": {
                    "type": "string",
                    "description": "Clé API pour le service externe",
                    "format": "password"
                }
            },
            "required": ["api_key"]
        }

# Point d'entrée pour le chargement dynamique
def load_module() -> BaseAIModule:
    """
    Fonction appelée par l'orchestrateur pour charger le module.
    
    Returns:
        Instance du module
    """
    return MonNouveauModule()
```

---

## 3️⃣ service.py (Template Service Métier)

```python
# app/ai/modules/mon_nouveau_module/service.py

from app.ai.modules.mon_nouveau_module.models import MonJob, MonResult  # 🔴 À ADAPTER
from app.ai.modules.mon_nouveau_module.schemas import (
    ProcessRequest,  # 🔴 À ADAPTER
    ProcessResponse
)
from app.core.event_bus import event_bus
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

class MonNouveauService:  # 🔴 À ADAPTER le nom
    """
    Service métier pour [DESCRIPTION]  # 🔴 À ADAPTER
    
    Responsabilités:
    - Logique métier principale
    - Interaction avec APIs externes
    - Gestion des jobs asynchrones
    """
    
    def __init__(self):
        self._initialized = False
        self._start_time = None
        
        # 🔴 ADAPTER: Vos providers/clients
        self.external_api_client = None
        self.redis_client = None
        
        # Métriques internes
        self._total_count = 0
        self._failed_count = 0
        self._durations = []
    
    async def initialize(self) -> None:
        """Initialise les connexions et ressources"""
        try:
            # 🔴 ADAPTER: Initialiser vos clients
            self.external_api_client = ExternalAPIClient()
            await self.external_api_client.connect()
            
            from app.core.redis import get_redis_client
            self.redis_client = await get_redis_client()
            
            self._start_time = datetime.utcnow()
            self._initialized = True
            
            logger.info("Service initialisé")
            
        except Exception as e:
            logger.error(f"Erreur initialisation service: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Ferme proprement les connexions"""
        if self.external_api_client:
            await self.external_api_client.close()
        
        logger.info("Service arrêté")
    
    async def start_processing(
        self,
        request: ProcessRequest,  # 🔴 À ADAPTER
        user_id: str
    ) -> MonJob:  # 🔴 À ADAPTER
        """
        Démarre un traitement asynchrone.
        
        1. Crée un job en base
        2. Lance une tâche Celery
        3. Émet un événement
        
        Args:
            request: Requête de traitement
            user_id: ID de l'utilisateur
            
        Returns:
            Job créé
        """
        start_time = datetime.utcnow()
        
        try:
            # 1. Création du job
            job = MonJob(  # 🔴 À ADAPTER
                user_id=user_id,
                status="pending",
                # 🔴 AJOUTER vos champs spécifiques
                created_at=datetime.utcnow()
            )
            await job.save()
            
            logger.info(f"Job créé: {job.id}")
            
            # 2. Lancement de la tâche Celery
            from app.ai.modules.mon_nouveau_module.tasks import process_task
            process_task.delay(str(job.id))
            
            # 3. Émission d'événement
            await event_bus.publish(
                event_name="mon_module.started",  # 🔴 À ADAPTER
                data={
                    "job_id": str(job.id),
                    "user_id": user_id,
                    "created_at": job.created_at.isoformat()
                },
                source_module="mon_nouveau_module",  # 🔴 À ADAPTER
                correlation_id=f"job-{job.id}"
            )
            
            self._total_count += 1
            
            return job
            
        except Exception as e:
            logger.error(f"Erreur démarrage traitement: {e}")
            self._failed_count += 1
            raise
    
    async def process_job_sync(self, job_id: str) -> None:
        """
        Traitement synchrone d'un job.
        Appelé par la tâche Celery.
        
        Args:
            job_id: ID du job à traiter
        """
        job = await MonJob.get(job_id)  # 🔴 À ADAPTER
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Traitement du job {job_id}")
            
            # Mise à jour statut
            job.status = "processing"
            await job.save()
            
            # 🔴 ADAPTER: Votre logique de traitement
            # Exemple: appel API externe
            result = await self.external_api_client.process(
                data=job.input_data
            )
            
            # Polling si nécessaire
            while not result.is_complete:
                await asyncio.sleep(2)
                
                # Événement de progression
                await event_bus.publish(
                    event_name="mon_module.progress",  # 🔴 À ADAPTER
                    data={
                        "job_id": str(job.id),
                        "progress": result.progress_percent
                    },
                    source_module="mon_nouveau_module"  # 🔴 À ADAPTER
                )
                
                result = await self.external_api_client.get_status(result.id)
            
            # Sauvegarde du résultat
            mon_result = MonResult(  # 🔴 À ADAPTER
                job_id=job.id,
                user_id=job.user_id,
                output_data=result.data,
                created_at=datetime.utcnow()
            )
            await mon_result.save()
            
            # Mise à jour du job
            job.status = "completed"
            job.result_id = mon_result.id
            job.completed_at = datetime.utcnow()
            await job.save()
            
            # Événement de succès
            await event_bus.publish(
                event_name="mon_module.completed",  # 🔴 À ADAPTER
                data={
                    "job_id": str(job.id),
                    "result_id": str(mon_result.id),
                    "user_id": job.user_id,
                    "duration_seconds": (
                        datetime.utcnow() - start_time
                    ).total_seconds()
                },
                source_module="mon_nouveau_module",  # 🔴 À ADAPTER
                correlation_id=f"job-{job.id}"
            )
            
            # Métriques
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._durations.append(duration_ms)
            if len(self._durations) > 1000:
                self._durations.pop(0)
            
            logger.info(f"✅ Job {job_id} terminé en {duration_ms:.0f}ms")
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement job {job_id}: {e}")
            
            # Mise à jour échec
            job.status = "failed"
            job.error_message = str(e)
            job.failed_at = datetime.utcnow()
            await job.save()
            
            # Événement d'échec
            await event_bus.publish(
                event_name="mon_module.failed",  # 🔴 À ADAPTER
                data={
                    "job_id": str(job.id),
                    "error": str(e),
                    "user_id": job.user_id
                },
                source_module="mon_nouveau_module",  # 🔴 À ADAPTER
                correlation_id=f"job-{job.id}"
            )
            
            self._failed_count += 1
            raise
    
    # === Tests de Santé ===
    
    async def test_api_connection(self) -> bool:
        """Teste la connexion à l'API externe"""
        try:
            # 🔴 ADAPTER selon votre API
            await self.external_api_client.ping()
            return True
        except Exception:
            return False
    
    async def test_redis_connection(self) -> bool:
        """Teste la connexion Redis"""
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False
    
    async def test_celery_connection(self) -> bool:
        """Teste la connexion Celery"""
        try:
            from app.tasks.celery_app import celery_app
            # Test simple
            celery_app.control.inspect().stats()
            return True
        except Exception:
            return False
    
    # === Métriques ===
    
    def get_total_count(self) -> int:
        """Nombre total de jobs traités"""
        return self._total_count
    
    def get_pending_count(self) -> int:
        """Nombre de jobs en attente"""
        # 🔴 ADAPTER: Query DB
        return 0
    
    def get_failed_count(self) -> int:
        """Nombre de jobs échoués"""
        return self._failed_count
    
    def get_avg_duration_ms(self) -> float:
        """Durée moyenne de traitement en ms"""
        if not self._durations:
            return 0.0
        return sum(self._durations) / len(self._durations)
    
    def get_uptime_seconds(self) -> float:
        """Temps de fonctionnement en secondes"""
        if not self._start_time:
            return 0.0
        return (datetime.utcnow() - self._start_time).total_seconds()
```

---

## 4️⃣ routes.py (Template API Endpoints)

```python
# app/ai/modules/mon_nouveau_module/routes.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from app.ai.modules.mon_nouveau_module.service import MonNouveauService
from app.ai.modules.mon_nouveau_module.schemas import (
    ProcessRequest,  # 🔴 À ADAPTER
    ProcessResponse,
    JobStatusResponse,
    JobListResponse
)
from app.ai.modules.mon_nouveau_module.models import MonJob  # 🔴 À ADAPTER
from app.core.permissions import require_permission
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter()

# === Dependency Injection ===

def get_service() -> MonNouveauService:
    """
    Récupère l'instance du service depuis l'app state.
    En production, utilisé via l'orchestrateur.
    """
    # TODO: Récupérer depuis app.state.orchestrator
    return MonNouveauService()

# === Endpoints ===

@router.post(
    "/process",  # 🔴 À ADAPTER selon votre besoin
    response_model=JobStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Démarre un nouveau traitement",
    description="Crée un job asynchrone et le démarre immédiatement"
)
@require_permission("mon_module:create")  # 🔴 À ADAPTER
async def create_job(
    request: ProcessRequest,  # 🔴 À ADAPTER
    service: MonNouveauService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """
    Démarre un nouveau traitement.
    
    - **request**: Données du traitement
    
    Returns:
        Job créé avec son ID pour tracking
    """
    try:
        job = await service.start_processing(
            request=request,
            user_id=current_user.id
        )
        
        return JobStatusResponse.from_orm(job)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur création job: {str(e)}"
        )

@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Récupère le statut d'un job",
    description="Retourne l'état actuel et les métadonnées d'un job"
)
@require_permission("mon_module:read")  # 🔴 À ADAPTER
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Récupère le statut d'un job.
    
    - **job_id**: ID du job
    
    Returns:
        Statut et métadonnées du job
    """
    job = await MonJob.get(job_id)  # 🔴 À ADAPTER
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job non trouvé"
        )
    
    # Vérification des permissions (user peut voir ses propres jobs)
    if job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé à ce job"
        )
    
    return JobStatusResponse.from_orm(job)

@router.get(
    "/list",
    response_model=JobListResponse,
    summary="Liste les jobs de l'utilisateur",
    description="Retourne la liste paginée des jobs"
)
@require_permission("mon_module:read")  # 🔴 À ADAPTER
async def list_jobs(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None  # Filter by status
):
    """
    Liste les jobs de l'utilisateur.
    
    - **skip**: Nombre de résultats à sauter (pagination)
    - **limit**: Nombre maximum de résultats (max 100)
    - **status**: Filtre optionnel par statut (pending, processing, completed, failed)
    
    Returns:
        Liste de jobs avec pagination
    """
    # Validation
    if limit > 100:
        limit = 100
    
    # Query
    query = {"user_id": current_user.id}
    if status:
        query["status"] = status
    
    jobs = await MonJob.find(  # 🔴 À ADAPTER
        **query,
        skip=skip,
        limit=limit
    )
    
    total = await MonJob.count(**query)  # 🔴 À ADAPTER
    
    return JobListResponse(
        jobs=[JobStatusResponse.from_orm(job) for job in jobs],
        total=total,
        skip=skip,
        limit=limit
    )

@router.post(
    "/cancel/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Annule un job en cours",
    description="Tente d'annuler un job qui n'est pas encore terminé"
)
@require_permission("mon_module:delete")  # 🔴 À ADAPTER
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Annule un job en cours.
    
    - **job_id**: ID du job à annuler
    """
    job = await MonJob.get(job_id)  # 🔴 À ADAPTER
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job non trouvé"
        )
    
    if job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès refusé"
        )
    
    if job.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible d'annuler un job {job.status}"
        )
    
    # 🔴 ADAPTER: Logique d'annulation
    job.status = "cancelled"
    job.cancelled_at = datetime.utcnow()
    await job.save()
    
    # Événement
    await event_bus.publish(
        event_name="mon_module.cancelled",  # 🔴 À ADAPTER
        data={"job_id": str(job.id)},
        source_module="mon_nouveau_module"  # 🔴 À ADAPTER
    )
    
    return None

@router.get(
    "/result/{job_id}",
    response_model=ProcessResponse,  # 🔴 À ADAPTER
    summary="Récupère le résultat d'un job terminé",
    description="Retourne les données de sortie d'un job completed"
)
@require_permission("mon_module:read")  # 🔴 À ADAPTER
async def get_job_result(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Récupère le résultat d'un job.
    
    - **job_id**: ID du job
    
    Returns:
        Données de sortie du traitement
    """
    job = await MonJob.get(job_id)  # 🔴 À ADAPTER
    
    if not job:
        raise HTTPException(404, "Job non trouvé")
    
    if job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(403, "Accès refusé")
    
    if job.status != "completed":
        raise HTTPException(
            400,
            f"Job pas encore terminé (statut: {job.status})"
        )
    
    if not job.result_id:
        raise HTTPException(500, "Résultat introuvable")
    
    # 🔴 ADAPTER: Récupérer votre modèle de résultat
    result = await MonResult.get(job.result_id)
    
    return ProcessResponse.from_orm(result)

# === Endpoints Admin (Optionnels) ===

@router.get(
    "/admin/stats",
    summary="Statistiques globales du module",
    description="Métriques pour monitoring (admin only)"
)
@require_permission("admin:read")
async def get_module_stats(
    service: MonNouveauService = Depends(get_service),
    current_user: User = Depends(get_current_user)
):
    """Stats administrateur"""
    return {
        "total_jobs": service.get_total_count(),
        "pending_jobs": service.get_pending_count(),
        "failed_jobs": service.get_failed_count(),
        "avg_duration_ms": service.get_avg_duration_ms(),
        "uptime_seconds": service.get_uptime_seconds()
    }
```

---

## 5️⃣ events.py (Template Gestion Événements)

```python
# app/ai/modules/mon_nouveau_module/events.py

from app.core.event_bus import Event, event_bus
from app.ai.modules.mon_nouveau_module.service import MonNouveauService
import logging

logger = logging.getLogger(__name__)

def register_event_handlers(
    event_bus_instance: "EventBus",
    service: MonNouveauService
) -> None:
    """
    Enregistre tous les handlers d'événements pour ce module.
    
    Args:
        event_bus_instance: Instance du bus d'événements
        service: Instance du service métier
    """
    
    # 🔴 ADAPTER: Événements que vous écoutez
    
    # Exemple 1: Réagir à la suppression d'un utilisateur
    @event_bus_instance.on("user.deleted")
    async def on_user_deleted(event: Event):
        """
        Nettoie les jobs d'un utilisateur supprimé.
        """
        user_id = event.data.get("user_id")
        logger.info(f"Nettoyage jobs utilisateur {user_id}")
        
        # 🔴 ADAPTER: Votre logique de nettoyage
        # Exemple: Annuler les jobs en cours
        pending_jobs = await MonJob.find(
            user_id=user_id,
            status__in=["pending", "processing"]
        )
        
        for job in pending_jobs:
            job.status = "cancelled"
            job.cancelled_at = datetime.utcnow()
            await job.save()
        
        logger.info(f"{len(pending_jobs)} jobs annulés")
    
    # Exemple 2: Réagir à un autre module
    @event_bus_instance.on("transcription.completed")
    async def on_transcription_completed(event: Event):
        """
        Exemple: Démarre automatiquement un traitement
        quand une transcription est terminée.
        """
        transcription_id = event.data.get("transcription_id")
        user_id = event.data.get("user_id")
        
        logger.info(
            f"Transcription {transcription_id} terminée, "
            f"démarrage traitement automatique"
        )
        
        # 🔴 ADAPTER: Votre logique
        # Exemple: Créer automatiquement un job
        from app.ai.modules.mon_nouveau_module.schemas import ProcessRequest
        
        request = ProcessRequest(
            input_data={"transcription_id": transcription_id}
        )
        
        await service.start_processing(
            request=request,
            user_id=user_id
        )
    
    # Exemple 3: Événements internes du module
    @event_bus_instance.on("mon_module.completed")
    async def on_processing_completed(event: Event):
        """
        Logique post-traitement après succès.
        """
        job_id = event.data.get("job_id")
        logger.info(f"Post-traitement du job {job_id}")
        
        # 🔴 ADAPTER: Exemple de post-processing
        # - Envoyer notification
        # - Mettre à jour des métriques
        # - Déclencher un workflow suivant
        
        # Exemple: Émettre un événement pour le module de notification
        await event_bus_instance.publish(
            event_name="notification.send",
            data={
                "user_id": event.data.get("user_id"),
                "type": "processing_completed",
                "title": "Traitement terminé",
                "message": f"Votre traitement (Job {job_id}) est prêt !",
                "job_id": job_id
            },
            source_module="mon_nouveau_module"
        )
    
    logger.info("Handlers d'événements enregistrés")
```

---

## 6️⃣ tasks.py (Template Tâches Celery)

```python
# app/ai/modules/mon_nouveau_module/tasks.py

from app.tasks.celery_app import celery_app
from celery import Task
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CallbackTask(Task):
    """Tâche de base avec callbacks"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Appelé en cas d'échec"""
        logger.error(f"Tâche {task_id} échouée: {exc}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Appelé en cas de succès"""
        logger.info(f"Tâche {task_id} réussie")

@celery_app.task(
    bind=True,
    base=CallbackTask,
    max_retries=3,
    default_retry_delay=60  # Retry après 60 secondes
)
async def process_task(self, job_id: str):
    """
    Tâche Celery principale pour le traitement asynchrone.
    
    Args:
        job_id: ID du job à traiter
    """
    logger.info(f"Démarrage tâche pour job {job_id}")
    start_time = datetime.utcnow()
    
    try:
        # Import local pour éviter les imports circulaires
        from app.ai.modules.mon_nouveau_module.service import MonNouveauService
        
        # Instanciation du service
        service = MonNouveauService()
        await service.initialize()
        
        # Traitement
        await service.process_job_sync(job_id)
        
        # Shutdown
        await service.shutdown()
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"✅ Tâche {job_id} terminée en {duration:.2f}s")
        
    except Exception as exc:
        logger.error(f"❌ Erreur tâche {job_id}: {exc}")
        
        # Retry si possible
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries dépassé pour {job_id}")
            # Mettre à jour le job en failed
            from app.ai.modules.mon_nouveau_module.models import MonJob
            job = await MonJob.get(job_id)
            if job:
                job.status = "failed"
                job.error_message = f"Max retries: {str(exc)}"
                await job.save()

@celery_app.task
async def cleanup_old_jobs():
    """
    Tâche périodique de nettoyage (lancée par APScheduler).
    Supprime les jobs anciens.
    """
    logger.info("Nettoyage des anciens jobs...")
    
    from app.ai.modules.mon_nouveau_module.models import MonJob
    from datetime import timedelta
    
    # 🔴 ADAPTER: Votre logique de nettoyage
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    old_jobs = await MonJob.find(
        status__in=["completed", "failed", "cancelled"],
        created_at__lt=cutoff_date
    )
    
    for job in old_jobs:
        await job.delete()
    
    logger.info(f"{len(old_jobs)} anciens jobs supprimés")
```

---

## 7️⃣ schemas.py (Template Schémas Pydantic)

```python
# app/ai/modules/mon_nouveau_module/schemas.py

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    """Statuts possibles d'un job"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# === Requêtes ===

class ProcessRequest(BaseModel):
    """
    Requête de traitement.
    🔴 ADAPTER selon vos besoins
    """
    input_data: Dict[str, Any] = Field(
        ...,
        description="Données d'entrée pour le traitement"
    )
    
    options: Optional[Dict[str, Any]] = Field(
        default={},
        description="Options de traitement (optionnel)"
    )
    
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Priorité du job (1=min, 10=max)"
    )
    
    @validator("input_data")
    def validate_input_data(cls, v):
        """Validation personnalisée des données d'entrée"""
        # 🔴 ADAPTER: Votre validation
        if not v:
            raise ValueError("input_data ne peut pas être vide")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "input_data": {
                    "text": "Exemple de texte à traiter",
                    "language": "fr"
                },
                "options": {
                    "format": "json",
                    "detailed": True
                },
                "priority": 7
            }
        }

# === Réponses ===

class ProcessResponse(BaseModel):
    """
    Réponse de traitement.
    🔴 ADAPTER selon vos besoins
    """
    result_id: str = Field(..., description="ID du résultat")
    output_data: Dict[str, Any] = Field(..., description="Données de sortie")
    metadata: Optional[Dict[str, Any]] = Field(
        default={},
        description="Métadonnées additionnelles"
    )
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "result_id": "550e8400-e29b-41d4-a716-446655440000",
                "output_data": {
                    "processed_text": "Texte traité...",
                    "confidence": 0.95
                },
                "metadata": {
                    "duration_ms": 1234,
                    "tokens_used": 500
                }
            }
        }

class JobStatusResponse(BaseModel):
    """Statut d'un job"""
    job_id: str
    status: JobStatus
    user_id: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    error_message: Optional[str] = None
    progress_percent: Optional[int] = Field(
        default=0,
        ge=0,
        le=100
    )
    
    result_id: Optional[str] = None
    
    class Config:
        orm_mode = True

class JobListResponse(BaseModel):
    """Liste de jobs avec pagination"""
    jobs: List[JobStatusResponse]
    total: int = Field(..., description="Nombre total de résultats")
    skip: int = Field(..., description="Offset de pagination")
    limit: int = Field(..., description="Limite par page")
    
    @property
    def has_more(self) -> bool:
        """Indique s'il y a d'autres résultats"""
        return (self.skip + self.limit) < self.total
```

---

## 📚 Comment Utiliser Ces Templates

### Étape 1: Créer un Nouveau Module

```bash
# 1. Créer la structure
mkdir -p app/ai/modules/mon_nouveau_module
cd app/ai/modules/mon_nouveau_module

# 2. Copier tous les templates
# Copier les contenus ci-dessus dans les fichiers correspondants

# 3. Rechercher et remplacer tous les "🔴 À ADAPTER"
# Dans VS Code: Ctrl+Shift+F → "🔴"
```

### Étape 2: Adapter le Code

```
Recherchez tous les marqueurs 🔴 À ADAPTER dans les fichiers et adaptez:

1. manifest.yaml:
   - name, description, class_name
   - dependencies, endpoints, permissions
   - events_emitted, events_subscribed

2. __init__.py:
   - Nom de la classe (MonNouveauModule)
   - Nom du service (MonNouveauService)

3. service.py:
   - Nom de la classe (MonNouveauService)
   - Noms des modèles (MonJob, MonResult)
   - Logique métier dans process_job_sync()
   - Tests de santé

4. routes.py:
   - Endpoints (chemins et noms)
   - Schémas de requête/réponse
   - Permissions

5. events.py:
   - Événements écoutés
   - Logique des handlers

6. schemas.py:
   - Champs des requêtes
   - Champs des réponses
   - Validations
```

### Étape 3: Tester

```bash
# 1. Démarrer l'application
docker-compose up -d

# 2. Vérifier que le module est découvert
curl http://localhost:8000/api/v1/modules/list

# 3. Tester le health check
curl http://localhost:8000/api/v1/modules/mon_nouveau_module/health

# 4. Tester l'API
curl -X POST http://localhost:8000/api/v1/modules/mon_nouveau_module/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"input_data": {"test": "data"}}'
```

---

## ⚡ Checklist Rapide

```yaml
✅ Fichiers à créer:
  - [ ] manifest.yaml (métadonnées)
  - [ ] __init__.py (classe principale)
  - [ ] service.py (logique métier)
  - [ ] routes.py (API endpoints)
  - [ ] events.py (event handlers)
  - [ ] tasks.py (Celery tasks)
  - [ ] schemas.py (Pydantic)
  - [ ] models.py (SQLModel)

✅ Points à adapter:
  - [ ] Nom du module (partout)
  - [ ] Dépendances (manifest)
  - [ ] Endpoints (manifest + routes)
  - [ ] Permissions (manifest + routes)
  - [ ] Événements (manifest + events)
  - [ ] Logique métier (service)
  - [ ] Schémas de données (schemas)

✅ Tests:
  - [ ] Module découvert au démarrage
  - [ ] Health check passe
  - [ ] API endpoints répondent
  - [ ] Événements émis/reçus
  - [ ] Tâches Celery fonctionnent
```

---

## 🎯 Résultat Final

Avec ces templates, ajouter un nouveau module IA prend **15-30 minutes** au lieu de plusieurs jours !

```
Temps avant: 2-3 jours
Temps après: 15-30 minutes
Gain: 95% de temps économisé ! 🚀
```

---

**Ces templates sont votre accélérateur de développement pour construire rapidement un écosystème de services IA ! 🎉**
