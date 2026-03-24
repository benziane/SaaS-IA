# SaaS-IA - Plateforme d'Orchestration IA

## Description
Plateforme SaaS d'orchestration IA multi-providers avec transcription, RAG, pipelines, agents et collaboration multi-tenant.

## Stack Technique
- **Backend**: FastAPI 0.135 / Python 3.11+ / SQLModel / Alembic
- **Frontend**: Next.js 15 / React 18 / Material-UI 6 / TypeScript strict
- **Base de donnees**: PostgreSQL 16 + Redis 7
- **Queue**: Celery 5.6 + Flower
- **Auth**: JWT (python-jose + passlib/bcrypt)
- **Paiement**: Stripe (Free/Pro/Enterprise)
- **Providers IA**: Gemini, Claude, Groq, OpenAI, AssemblyAI
- **Monitoring**: Prometheus + structlog

## Architecture

### Backend modulaire
Chaque module est dans `mvp/backend/app/modules/<nom>/` et contient:
- `manifest.json` - declaration du module (name, version, prefix, tags, enabled, dependencies)
- `routes.py` - expose un `router` APIRouter
- `service.py` - logique metier
- `schemas.py` - schemas Pydantic (optionnel)

Les modules sont auto-decouverts par `ModuleRegistry` dans `app/modules/__init__.py`.

### Modules existants (12)
agents, api_keys, billing, compare, conversation, cost_tracker, knowledge, pipelines, sentiment, transcription, web_crawler, workspaces

### Frontend Sneat
**OBLIGATOIRE**: Utiliser exclusivement le template **Sneat MUI Next.js Admin Template v3.0.0**.
- NE JAMAIS creer de composants UI from scratch si Sneat/MUI les a
- Composants features dans `mvp/frontend/src/features/`
- Layouts dans `mvp/frontend/src/@layouts/`
- Etat: Zustand + TanStack Query 5
- Formulaires: React Hook Form + Zod

## Conventions

### Commits
Format Conventional Commits: `<type>(<scope>): <description>`
Types: feat, fix, docs, style, refactor, test, chore, perf, ci

### Backend (Python)
- Style: PEP 8 / Formatter: Black / Linter: Ruff / Types: mypy
- async/await pour toutes les operations I/O
- structlog pour le logging
- Pydantic pour la validation des entrees

### Frontend (TypeScript)
- ESLint + Prettier
- Composants fonctionnels + Hooks
- TypeScript strict mode
- Import MUI depuis `@mui/material`

## Commandes utiles

### Backend
```bash
cd mvp/backend
ruff check app/                          # Linting
mypy app/                                # Type checking
python -m pytest tests/ -v --cov=app     # Tests + coverage
alembic revision --autogenerate -m "desc" # Migration
alembic upgrade head                      # Appliquer migrations
```

### Frontend
```bash
cd mvp/frontend
npm run lint          # ESLint
npm run type-check    # TypeScript
npm run build         # Build production
npx vitest            # Tests unitaires
npx playwright test   # Tests E2E
```

### Docker
```bash
docker compose up -d          # Demarrer tous les services
docker compose logs -f backend # Logs backend
```

## Securite
- Secrets dans `.env` uniquement (jamais en dur dans le code)
- Validation Pydantic sur toutes les entrees API
- JWT avec rotation de tokens
- Rate limiting via slowapi + Redis
- Webhooks Stripe signes
