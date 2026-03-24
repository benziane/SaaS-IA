---
name: saas-backend
description: |
  Skill pour le developpement backend FastAPI du projet SaaS-IA.
  TRIGGER quand: creation/modification d'endpoints API, services, models SQLModel,
  schemas Pydantic, routes FastAPI, ou tout code dans mvp/backend/.
---

# Developpement Backend FastAPI

## Architecture modulaire

Chaque module backend suit cette structure dans `mvp/backend/app/modules/<nom>/`:

```
<nom>/
├── manifest.json   # Declaration du module
├── __init__.py
├── routes.py       # APIRouter avec endpoints
├── service.py      # Logique metier (async)
└── schemas.py      # Schemas Pydantic (request/response)
```

### manifest.json (obligatoire)
```json
{
  "name": "<nom>",
  "version": "1.0.0",
  "description": "<description>",
  "prefix": "/api/<nom>",
  "tags": ["<nom>"],
  "enabled": true,
  "dependencies": []
}
```

## Patterns obligatoires

### Routes (routes.py)
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.auth import get_current_user
from app.models.user import User
from app.rate_limit import limiter, get_rate_limit

router = APIRouter()

@router.get("/")
@limiter.limit(get_rate_limit)
async def list_items(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = MyService(session)
    return await service.list_for_user(current_user.id)
```

### Service layer (service.py)
```python
from sqlmodel.ext.asyncio.session import AsyncSession
import structlog

logger = structlog.get_logger()

class MyService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list:
        logger.info("listing_items", user_id=str(user_id))
        # ... logique metier
```

## Regles

1. **Toujours async/await** pour les operations I/O (database, API externes, fichiers)
2. **SQLModel** pour les modeles de donnees (dans `app/models/`)
3. **Pydantic** pour la validation des entrees/sorties
4. **structlog** pour le logging (jamais print())
5. **Dependency injection** via FastAPI Depends()
6. **Rate limiting** avec `@limiter.limit(get_rate_limit)` sur tous les endpoints publics
7. **Auth JWT** via `get_current_user` pour les endpoints proteges
8. **HTTPException** avec status codes explicites pour les erreurs
9. **Tests**: creer/mettre a jour les tests dans `mvp/backend/tests/`
10. **Pas de secrets en dur**: utiliser `app.config.settings`
