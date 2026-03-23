# SaaS-IA MVP

Plateforme SaaS modulaire d'intelligence artificielle - Version MVP complete.

## Services Docker

| Service | Port | Description |
|---------|------|-------------|
| backend | 8004 | FastAPI API |
| worker | - | Celery worker (transcriptions async) |
| flower | 5555 | Monitoring Celery |
| postgres | 5435 | PostgreSQL 16 |
| redis | 6382 | Redis 7 (cache, broker) |

## Demarrage rapide

```bash
# 1. Configurer l'environnement
cp backend/.env.example backend/.env
# Editer backend/.env avec vos cles

# 2. Lancer les services
docker compose up -d

# 3. Frontend (developpement)
cd frontend && npm install && npm run dev
```

## Variables d'environnement requises

```env
# Obligatoire
SECRET_KEY=votre-cle-secrete-forte
DATABASE_URL=postgresql://user:pass@localhost:5435/saas_ia

# AI Providers (au moins un)
GEMINI_API_KEY=...
CLAUDE_API_KEY=...
GROQ_API_KEY=...

# Transcription (ou MOCK pour test)
ASSEMBLYAI_API_KEY=MOCK

# Stripe (optionnel, pour les paiements)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO_MONTHLY=price_...
```

## Pages frontend

| Route | Description |
|-------|-------------|
| /dashboard | Tableau de bord avec stats |
| /transcription | Transcription multi-source |
| /chat | Chat IA contextuel |
| /compare | Comparaison multi-modele |
| /pipelines | Pipeline builder IA |
| /knowledge | Knowledge base + RAG |
| /billing | Plans, quotas, Stripe |
| /workspaces | Collaboration |
| /api-docs | Gestion cles API + documentation |
| /modules | Vue admin des modules |
| /profile | Profil utilisateur |

## Modules backend (auto-decouverts)

| Module | Prefix | Endpoints |
|--------|--------|-----------|
| transcription | /api/transcription | 7 |
| conversation | /api/conversations | 5 |
| billing | /api/billing | 5 |
| compare | /api/compare | 3 |
| pipelines | /api/pipelines | 8 |
| knowledge | /api/knowledge | 5 |
| api_keys | /api/keys | 3 |
| workspaces | /api/workspaces | 12 |
| Public API v1 | /v1 | 3 |

## Tests

```bash
cd backend
pytest                    # 211 tests
pytest -k integration     # 32 tests d'integration
pytest -k billing         # Tests module billing
```

## Documentation

- [ROADMAP.md](ROADMAP.md) - Roadmap et changelog
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Architecture technique
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Guide deploiement
- [docs/API_REFERENCE.md](docs/API_REFERENCE.md) - Reference API
- [docs/SPRINT*.md](docs/) - Documentation par sprint
