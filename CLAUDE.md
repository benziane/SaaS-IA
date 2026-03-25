# CLAUDE.md - SaaS-IA Platform

## Projet

Plateforme SaaS modulaire d'intelligence artificielle - 32 modules backend auto-decouverts, 38 pages frontend, ~270 endpoints API. Architecture enterprise S+++ (v4.0.0).

## Stack technique

- **Backend** : FastAPI 0.135, Python 3.13, SQLModel + Pydantic 2, PostgreSQL 16 (AsyncPG), Redis 7, Celery
- **Frontend** : Next.js 15 (App Router), React 18, MUI 6, TanStack Query 5, Axios
- **AI Providers** : Gemini 2.0 Flash, Claude Sonnet, Groq Llama 3.3 70B (via AIAssistantService + LiteLLM proxy)
- **Infra** : Docker Compose (multi-stage), Prometheus, OpenTelemetry, structlog (JSON prod), Sentry/GlitchTip, Alembic
- **Enterprise** : 9 middleware layers (CORS, RequestID, ShutdownGuard, Sentry, RateLimit, Logging, Security, Compression, Prometheus), 12 enterprise components (circuit breaker, sliding window rate limit, graceful shutdown, K8s health probes, OpenTelemetry tracing, Sentry error tracking, structured logging, DB pooling, compression Gzip+Brotli, security headers OWASP, multi-stage Dockerfile, tini PID 1)
- **Ports** : Backend 8004, Frontend 3002, PostgreSQL 5435, Redis 6382, Flower 5555

## Architecture modulaire

Chaque module backend suit le pattern :
```
mvp/backend/app/modules/<module_name>/
  __init__.py
  manifest.json    # auto-discovery par ModuleRegistry
  schemas.py       # Pydantic request/response
  service.py       # Business logic
  routes.py        # FastAPI APIRouter
```

Les modeles DB sont dans `mvp/backend/app/models/<module_name>.py`.
Les migrations Alembic dans `mvp/backend/alembic/versions/`.

Frontend par module :
```
mvp/frontend/src/features/<module-name>/
  types.ts
  api.ts           # Axios calls vers le backend
  hooks/use<Module>.ts  # React Query hooks
mvp/frontend/src/app/(dashboard)/<route>/page.tsx
```

## Regles CRITIQUES

### NE JAMAIS supprimer ou ecraser un module ou une techno qui fonctionne

Cette regle concerne les **modules et les technologies**, pas le code en general :

- Si un module fonctionne avec la techno X et qu'on trouve que la techno Y fait mieux : **on garde le module avec la techno X** et on cree une **nouvelle version** (v2) avec la techno Y
- **JAMAIS** ecraser tout un module pour le remplacer par une autre implementation
- **JAMAIS** desinstaller ou retirer une dependance utilisee par un module existant
- L'ancien module/techno reste fonctionnel comme **fallback** et **reference**
- Les deux versions coexistent : l'utilisateur ou le systeme choisit la meilleure automatiquement

**Exemple concret** : le module `knowledge` utilisait TF-IDF pour la recherche.
On a ajoute pgvector + sentence-transformers (v2) SANS supprimer TF-IDF.
Resultat : `search()` auto-detecte hybrid si pgvector est dispo, sinon TF-IDF.
Les deux coexistent, zero regression, upgrade transparent.

**Modifier du code dans un fichier existant** (ajouter des methodes, corriger un bug, refactorer) est parfaitement OK.
Ce qui est interdit c'est de **supprimer un module entier ou remplacer une techno fonctionnelle**.

### Git

- Ne JAMAIS force push
- Ne JAMAIS amend un commit existant
- Toujours creer de NOUVEAUX commits
- Ne pas committer sans que l'utilisateur le demande explicitement
- Ne pas committer les fichiers .env, credentials, ou cles API

### Code

- Suivre le pattern module existant (manifest.json + schemas + service + routes)
- Les services utilisent `AIAssistantService.process_text_with_provider()` pour les appels IA
- Les routes utilisent `@limiter.limit()`, `Depends(get_current_user)`, `Depends(get_session)`
- Auth : JWT via `app.auth.get_current_user`
- DB sessions : `from app.database import get_session`
- Logging : `structlog.get_logger()`
- Ne pas ajouter de commentaires inutiles ou de docstrings sur du code qu'on n'a pas modifie
- Ne pas over-engineer : faire le minimum necessaire pour la feature demandee

### Knowledge Base / Search

- Le module `knowledge` supporte 3 modes de recherche : TF-IDF (legacy), Vector (pgvector), Hybrid (RRF fusion)
- `search()` auto-detecte le meilleur mode disponible
- Embeddings : `app.modules.knowledge.embedding_service` (all-MiniLM-L6-v2, 384 dim, singleton lazy-loaded)
- Les embeddings sont stockes dans la colonne `embedding vector(384)` via pgvector (geree par migration SQL, pas SQLModel)
- Pour ajouter un embedding a un chunk, utiliser raw SQL : `UPDATE document_chunks SET embedding = :emb WHERE id = :cid`
- Toujours garder le TF-IDF comme fallback - ne jamais le supprimer

## Modules existants (32)

### Core (12)
transcription, conversation, knowledge (hybrid search: pgvector + TF-IDF), compare, pipelines, agents, sentiment, web_crawler, workspaces, billing, api_keys, cost_tracker

### P0 - Content & Automation (2)
content_studio (10 formats), ai_workflows (DAG engine, 19 actions, 5 templates, networkx validation)

### P1 - Intelligence & Safety (4)
multi_agent_crew (9 roles, 4 templates), voice_clone (TTS OpenAI + Coqui + cloning), realtime_ai (voice/vision/meeting), security_guardian (Presidio PII + NeMo injection + audit)

### P2 - Media & Intelligence (3)
image_gen (10 styles), data_analyst (DuckDB + ydata-profiling + NL queries), video_gen (6 types)

### P3 - Custom Models (1)
fine_tuning (datasets from platform data, LoRA training, evaluation)

### Platform - Monitoring, Search, Memory (3)
ai_monitoring (LLM observability, traces, provider comparison), unified_search (cross-module search + RAG), ai_memory (persistent memory + context injection)

### Ecosystem (4)
social_publisher (multi-platform publishing, scheduling, analytics), integration_hub (10 connectors, webhooks, triggers), ai_chatbot_builder (RAG chatbots, embed widget, multi-channel), marketplace (listings, ratings, installs, 8 categories)

### New - Content & Dev Tools (3)
presentation_gen (AI slides, 5 templates, export HTML/MD/PDF), code_sandbox (secure execution, AI code gen/debug), ai_forms (conversational forms, AI generation, scoring)

## Integrations open-source (29 libs)

| Lib | Module | Fallback |
|-----|--------|----------|
| pgvector + sentence-transformers | knowledge | TF-IDF |
| litellm | ai_assistant | providers directs |
| presidio | security_guardian | regex patterns |
| faster-whisper + pyannote | transcription | AssemblyAI |
| duckdb + ydata-profiling | data_analyst | pandas parser |
| Coqui TTS | voice_clone | OpenAI TTS / mock |
| NeMo-Guardrails | security_guardian | regex injection |
| networkx | ai_workflows | Kahn's algorithm |
| cardiffnlp/RoBERTa (transformers) | sentiment | LLM analysis |
| textstat | content_studio | word count basique |
| Jina Reader API | web_crawler | crawl4ai seul |
| ffmpeg-python | video_gen | mock placeholders |
| Real-ESRGAN | image_gen | pas d'upscaling |
| unsloth | fine_tuning | mock training |
| lm-evaluation-harness | fine_tuning | mock evaluation |
| livekit-server-sdk | realtime_ai | text-based sessions |
| OpenTelemetry (7 packages) | core/telemetry | Prometheus seul |
| sentry-sdk | core/error_tracking | structlog seul |
| meilisearch | unified_search | PostgreSQL ILIKE |
| mem0ai | ai_memory | DB queries |
| langfuse | ai_monitoring | Prometheus seul |

Toutes les integrations suivent la regle : **auto-detection + fallback gracieux** (pattern `HAS_XXX`).

## Interconnexions

3 systemes d'orchestration connectent tous les modules :
- **Agent Executor** : ~30 actions (appels directs aux services)
- **Pipeline Steps** : 20 step types (chaining sequentiel)
- **Workflow Actions** : 23 types (DAG avec branches paralleles)

Quand on ajoute un nouveau module, penser a l'integrer dans les 3 systemes + le planner heuristique.

## Commandes utiles

```bash
# Backend
cd mvp && docker compose up -d
cd mvp/backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd mvp/frontend && npm run dev

# Tests
cd mvp/backend && pytest
cd mvp/frontend && npm run test

# Migrations
cd mvp/backend && alembic upgrade head
```

## Documentation

- [README.md](mvp/README.md) - Vue d'ensemble et modules
- [ROADMAP.md](mvp/ROADMAP.md) - Roadmap complete, changelog, endpoints API, connectivite
- [TECH_AUDIT_ROADMAP.md](mvp/TECH_AUDIT_ROADMAP.md) - Audit open-source : libs a integrer, priorites, checkboxes de suivi
- [backend/MIGRATIONS_GUIDE.md](mvp/backend/MIGRATIONS_GUIDE.md) - Guide migrations Alembic
