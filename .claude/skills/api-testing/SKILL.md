---
name: api-testing
description: |
  Skill pour la creation de tests API complets du projet SaaS-IA.
  TRIGGER quand: l'utilisateur demande d'ajouter des tests, de tester un endpoint,
  d'ameliorer la coverage, ou apres creation/modification d'un endpoint API.
---

# Tests API - pytest + FastAPI

## Stack de test
- **pytest** + **pytest-asyncio** pour les tests async
- **httpx.AsyncClient** pour les appels HTTP
- **unittest.mock** / **pytest-mock** pour les mocks
- **SQLite** en memoire pour les tests DB

## Structure des tests

```
mvp/backend/tests/
├── conftest.py              # Fixtures partagees (client, session, user)
├── test_<module>.py         # Tests par module
├── test_auth.py             # Tests authentification
└── test_<module>_service.py # Tests service layer
```

## Patterns obligatoires

### Test d'endpoint basique
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_items(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/items/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_create_item(client: AsyncClient, auth_headers: dict):
    payload = {"name": "Test Item", "description": "Test"}
    response = await client.post("/api/items/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"

@pytest.mark.asyncio
async def test_create_item_unauthorized(client: AsyncClient):
    payload = {"name": "Test"}
    response = await client.post("/api/items/", json=payload)
    assert response.status_code == 401
```

### Test avec mock de provider IA
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_ai_endpoint(client: AsyncClient, auth_headers: dict):
    mock_response = {"text": "Mocked AI response"}
    with patch("app.modules.conversation.service.generate_response", new_callable=AsyncMock) as mock:
        mock.return_value = mock_response
        response = await client.post("/api/conversation/", json={"prompt": "test"}, headers=auth_headers)
        assert response.status_code == 200
        mock.assert_called_once()
```

## Ce qu'il faut tester

Pour chaque endpoint:
1. **Happy path** - requete valide, reponse attendue
2. **Auth** - 401 sans token, 403 sans permission
3. **Validation** - 422 avec donnees invalides
4. **Not found** - 404 avec ID inexistant
5. **Edge cases** - champs vides, limites de pagination, caracteres speciaux

## Commande
```bash
cd mvp/backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

## Regles

1. **Jamais d'appels reels** aux providers IA en test - toujours mocker
2. **Fixtures partagees** dans conftest.py (client, session, user, auth_headers)
3. **Isolation** - chaque test est independant, pas d'etat partage
4. **Nommage** - `test_<action>_<contexte>` (ex: `test_create_item_unauthorized`)
5. **Coverage minimum** 80% sur le code modifie
