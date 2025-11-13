# ⚡ QUICKSTART - Démarrage en 10 Minutes

## 🎯 Objectif

Avoir un système fonctionnel avec le module de transcription en **10 minutes**.

---

## 📋 Prérequis

```bash
✅ Docker + Docker Compose installés
✅ Python 3.11+ installé
✅ Node.js 18+ installé (pour le frontend)
```

---

## 🚀 Étape 1: Setup Initial (3 minutes)

### Créer la Structure

```bash
# Créer le projet
mkdir ai-saas-platform
cd ai-saas-platform

# Structure backend
mkdir -p backend/app/{api/v1,models,schemas,services,core,tasks,ai/{modules/transcription,providers}}
mkdir -p backend/tests backend/scripts backend/migrations

# Structure frontend
mkdir -p frontend/src

# Configuration
mkdir -p nginx monitoring/{prometheus,grafana}

# Fichiers Docker
touch docker-compose.yml backend/Dockerfile frontend/Dockerfile
```

### Docker Compose Minimal

```yaml
# docker-compose.yml

version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: aiplatform
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Backend FastAPI
  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://admin:admin123@postgres:5432/aiplatform
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  # Celery Worker
  celery_worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
    environment:
      DATABASE_URL: postgresql://admin:admin123@postgres:5432/aiplatform
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile Backend

```dockerfile
# backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Requirements.txt

```txt
# backend/requirements.txt

fastapi==0.109.0
uvicorn[standard]==0.25.0
sqlmodel==0.0.25
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
redis==5.0.1
celery==5.4.0
yt-dlp==2024.1.1
pyyaml==6.0.1
asyncio==3.4.3
```

---

## 🎯 Étape 2: Fichiers Core (4 minutes)

### 1. Base Module

```python
# backend/app/ai/base_module.py

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Dict, Any

class ModuleMetadata(BaseModel):
    name: str
    version: str

class ModuleHealth(BaseModel):
    status: str
    dependencies_ok: bool

class BaseAIModule(ABC):
    @abstractmethod
    def get_metadata(self) -> ModuleMetadata:
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        pass
    
    @abstractmethod
    async def health_check(self) -> ModuleHealth:
        pass
    
    @abstractmethod
    def get_router(self):
        pass
```

### 2. Event Bus Minimal

```python
# backend/app/core/event_bus.py

from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Event:
    name: str
    data: Dict[str, Any]
    source_module: str
    timestamp: datetime

class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_name: str, handler: Callable):
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
    
    async def publish(self, event_name: str, data: Dict, source_module: str):
        event = Event(
            name=event_name,
            data=data,
            source_module=source_module,
            timestamp=datetime.utcnow()
        )
        
        if event_name in self._handlers:
            for handler in self._handlers[event_name]:
                await handler(event)

event_bus = EventBus()
```

### 3. Service Registry Minimal

```python
# backend/app/core/service_registry.py

from typing import Dict

class ServiceRegistry:
    def __init__(self):
        self._modules: Dict = {}
    
    async def register_module(self, module, endpoints: list):
        metadata = module.get_metadata()
        self._modules[metadata.name] = {
            "module": module,
            "endpoints": endpoints
        }
        return True
    
    def list_modules(self):
        return list(self._modules.keys())
```

### 4. Module Orchestrator Minimal

```python
# backend/app/core/module_orchestrator.py

from pathlib import Path
import yaml
from importlib import import_module

class ModuleOrchestrator:
    def __init__(self, service_registry):
        self.service_registry = service_registry
        self.modules = {}
    
    async def discover_modules(self, modules_path: Path):
        discovered = []
        for module_dir in modules_path.iterdir():
            if module_dir.is_dir() and (module_dir / "manifest.yaml").exists():
                discovered.append(module_dir.name)
        return discovered
    
    async def load_module(self, module_name: str, modules_path: Path):
        try:
            module_package = import_module(f"app.ai.modules.{module_name}")
            return module_package.load_module()
        except Exception as e:
            print(f"Erreur chargement {module_name}: {e}")
            return None
    
    async def start_all_modules(self, app, event_bus, modules_path):
        results = {}
        module_names = await self.discover_modules(modules_path)
        
        for module_name in module_names:
            module = await self.load_module(module_name, modules_path)
            if module:
                await module.initialize()
                await self.service_registry.register_module(
                    module,
                    module.get_metadata().endpoints
                )
                
                # Montage du routeur
                router = module.get_router()
                app.include_router(
                    router,
                    prefix=f"/api/v1/modules/{module_name}",
                    tags=[module_name]
                )
                
                self.modules[module_name] = module
                results[module_name] = True
        
        return results
```

---

## 🎯 Étape 3: Module Transcription (3 minutes)

### manifest.yaml

```yaml
# backend/app/ai/modules/transcription/manifest.yaml

name: transcription
version: 1.0.0
class_name: TranscriptionModule
endpoints:
  - /transcribe
  - /status/{job_id}
```

### __init__.py (Module Principal)

```python
# backend/app/ai/modules/transcription/__init__.py

from app.ai.base_module import BaseAIModule, ModuleMetadata, ModuleHealth
from fastapi import APIRouter
import yaml
from pathlib import Path

router = APIRouter()

@router.post("/transcribe")
async def transcribe(youtube_url: str):
    return {"status": "started", "message": "Transcription démarrée"}

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    return {"job_id": job_id, "status": "processing"}

class TranscriptionModule(BaseAIModule):
    def __init__(self):
        self.router = router
        manifest_path = Path(__file__).parent / "manifest.yaml"
        with open(manifest_path) as f:
            data = yaml.safe_load(f)
        self._metadata = ModuleMetadata(**data)
    
    def get_metadata(self):
        return self._metadata
    
    async def initialize(self):
        print(f"✅ {self._metadata.name} initialisé")
        return True
    
    async def health_check(self):
        return ModuleHealth(status="healthy", dependencies_ok=True)
    
    def get_router(self):
        return self.router

def load_module():
    return TranscriptionModule()
```

---

## 🚀 Étape 4: Main FastAPI (1 minute)

```python
# backend/app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.module_orchestrator import ModuleOrchestrator
from app.core.service_registry import ServiceRegistry
from app.core.event_bus import event_bus
from pathlib import Path

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Démarrage...")
    
    # Service Registry
    service_registry = ServiceRegistry()
    app.state.service_registry = service_registry
    
    # Orchestrator
    orchestrator = ModuleOrchestrator(service_registry)
    
    # Démarrage modules
    results = await orchestrator.start_all_modules(
        app=app,
        event_bus=event_bus,
        modules_path=Path("app/ai/modules")
    )
    
    print(f"✅ {sum(results.values())}/{len(results)} modules démarrés")
    
    yield
    
    print("🛑 Arrêt...")

app = FastAPI(title="AI SaaS Platform", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "AI SaaS Platform - Actif"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

---

## 🎯 Étape 5: Démarrage (1 minute)

```bash
# Démarrer tous les services
docker-compose up -d --build

# Vérifier les logs
docker-compose logs -f backend

# Tester l'API
curl http://localhost:8000/
curl http://localhost:8000/health

# Tester le module
curl -X POST "http://localhost:8000/api/v1/modules/transcription/transcribe?youtube_url=https://youtube.com/watch?v=test"

# Voir la doc API
# Ouvrir: http://localhost:8000/docs
```

---

## ✅ Résultat

Vous avez maintenant :

```
✅ Infrastructure de base (PostgreSQL, Redis, Celery)
✅ Système de modules fonctionnel
✅ Module de transcription (MVP basique)
✅ API REST documentée (OpenAPI)
✅ Découverte automatique des modules
```

---

## 🎯 Prochaines Étapes

### Court Terme (1h)
1. Ajouter l'authentification (JWT)
2. Compléter la logique du module transcription
3. Ajouter les tests unitaires

### Moyen Terme (1 jour)
1. Implémenter yt-dlp pour extraction audio
2. Intégrer Assembly AI pour transcription
3. Ajouter le système de tâches Celery

### Long Terme (1 semaine)
1. Créer l'interface Next.js
2. Ajouter 2-3 nouveaux modules IA
3. Monitoring (Prometheus + Grafana)
4. CI/CD (GitHub Actions)

---

## 📚 Documentation Complète

Pour aller plus loin, consultez :

1. **INDEX-DOCUMENTATION.md** - Navigation complète
2. **ARCHITECTURE-SAAS-IA-SCALABLE-V2.md** - Architecture détaillée
3. **GUIDE-IMPLEMENTATION-MODULAIRE.md** - Guide pas-à-pas
4. **TEMPLATES-CODE-MODULES.md** - Templates de code

---

## 🆘 Dépannage Rapide

### Problème: Module non découvert
```bash
# Vérifier la structure
ls backend/app/ai/modules/transcription/manifest.yaml

# Vérifier les logs
docker-compose logs backend | grep "découvert"
```

### Problème: Erreur import
```bash
# Rebuild l'image
docker-compose up -d --build backend

# Vérifier les dépendances
docker-compose exec backend pip list
```

### Problème: Base de données
```bash
# Recréer la DB
docker-compose down -v
docker-compose up -d
```

---

## 🎉 Félicitations !

Vous avez un système fonctionnel en **10 minutes** ! 🚀

**Prochaine étape** : Lire la documentation complète pour construire un système production-ready.

---

*Temps total: 10 minutes*  
*Difficulté: ⭐⭐ (Facile)*  
*Version: 1.0.0*
