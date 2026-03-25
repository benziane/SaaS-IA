---
name: module-scaffold
description: |
  Skill pour le scaffolding de nouveaux modules dans le projet SaaS-IA.
  TRIGGER quand: l'utilisateur demande de creer un nouveau module, une nouvelle
  fonctionnalite complete (backend + frontend), ou mentionne "nouveau module".
---

# Scaffolding de Module SaaS-IA

## Structure a generer

Pour un nouveau module `<nom>`, creer:

### Backend (`mvp/backend/app/modules/<nom>/`)

#### manifest.json
```json
{
  "name": "<nom>",
  "version": "1.0.0",
  "description": "<description du module>",
  "prefix": "/api/<nom>",
  "tags": ["<nom>"],
  "enabled": true,
  "dependencies": []
}
```

#### __init__.py
```python
"""<Nom> module."""
```

#### schemas.py
```python
"""<Nom> schemas."""
from uuid import UUID
from pydantic import BaseModel

class <Nom>Create(BaseModel):
    """Schema for creating a <nom>."""
    name: str

class <Nom>Read(BaseModel):
    """Schema for reading a <nom>."""
    id: UUID
    name: str

    model_config = {"from_attributes": True}
```

#### service.py
```python
"""<Nom> service."""
from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
import structlog

logger = structlog.get_logger()

class <Nom>Service:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list:
        logger.info("<nom>_list", user_id=str(user_id))
        # TODO: implement
        return []
```

#### routes.py
```python
"""<Nom> API routes."""
from fastapi import APIRouter, Depends, Request
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.auth import get_current_user
from app.models.user import User
from app.rate_limit import limiter, get_rate_limit
from app.modules.<nom>.service import <Nom>Service

router = APIRouter()

@router.get("/")
@limiter.limit(get_rate_limit)
async def list_items(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = <Nom>Service(session)
    return await service.list_for_user(current_user.id)
```

### Tests (`mvp/backend/tests/test_<nom>.py`)
```python
"""Tests for <nom> module."""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_<nom>(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/<nom>/", headers=auth_headers)
    assert response.status_code == 200
```

### Frontend (`mvp/frontend/src/features/<nom>/`)
```
<nom>/
├── components/     # Composants UI du module
├── hooks/          # useQuery/useMutation hooks
├── types.ts        # Types TypeScript
└── api.ts          # Fonctions d'appel API
```

### Modele DB (`mvp/backend/app/models/<nom>.py`)
```python
"""<Nom> database models."""
import uuid as uuid_pkg
from datetime import datetime
from sqlmodel import SQLModel, Field

class <Nom>Base(SQLModel):
    name: str = Field(max_length=200)
    description: str | None = None
    user_id: uuid_pkg.UUID = Field(index=True)

class <Nom>(<Nom>Base, table=True):
    __tablename__ = "<noms>"  # pluriel
    id: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Migration Alembic
Generer apres creation du modele :
```bash
cd mvp/backend && alembic revision --autogenerate -m "add_<nom>_tables"
```

## Interconnexion obligatoire (3 systemes)

Chaque nouveau module doit etre connecte aux 3 systemes d'orchestration :

### 1. Agent Executor (`mvp/backend/app/modules/agents/executor.py`)
```python
elif action == "<nom>_action":
    from app.modules.<nom>.service import <Nom>Service
    svc = <Nom>Service(self.session)
    result = await svc.process(params.get("input", ""), user_id)
    return {"result": result}
```

### 2. Pipeline Steps (`mvp/backend/app/modules/pipelines/service.py`)
```python
elif step_type == "<nom>":
    from app.modules.<nom>.service import <Nom>Service
    svc = <Nom>Service(session)
    result = await svc.process(step_input, user_id)
    return {"output": result}
```

### 3. Workflow Actions (`mvp/backend/app/modules/ai_workflows/service.py`)
```python
elif action == "<nom>_process":
    from app.modules.<nom>.service import <Nom>Service
    svc = <Nom>Service(session)
    result = await svc.process(params.get("input", ""), user_id)
    return {"result": result}
```

### 4. Agent Planner (`mvp/backend/app/modules/agents/planner.py`)
Ajouter le module dans les heuristiques du planner pour la planification automatique.

## Pattern open-source (auto-detection + fallback)

Si le module integre une lib open-source, toujours suivre ce pattern :
```python
try:
    import some_lib
    HAS_SOME_LIB = True
except ImportError:
    HAS_SOME_LIB = False

async def process(self, input: str) -> dict:
    if HAS_SOME_LIB:
        return await self._process_with_lib(input)
    return await self._process_fallback(input)
```

## Checklist apres scaffolding
- [ ] manifest.json valide (tous les champs requis)
- [ ] Le module est auto-decouvert par ModuleRegistry
- [ ] Modele DB + migration Alembic creee
- [ ] Connecte aux 3 systemes (executor, pipeline, workflow)
- [ ] Ajoute dans le planner heuristique
- [ ] Les tests passent
- [ ] La route frontend est ajoutee dans la navigation
- [ ] Les types TypeScript correspondent aux schemas Pydantic
- [ ] Open-source lib avec auto-detection + fallback (si applicable)
