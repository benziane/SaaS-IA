# Architecture Technique - SaaS-IA

## Vue d'ensemble

```
                    ┌──────────────┐
                    │   Frontend   │
                    │  Next.js 15  │
                    │  Port 3002   │
                    └──────┬───────┘
                           │ HTTPS
                    ┌──────▼───────┐
                    │   Backend    │
                    │  FastAPI     │
                    │  Port 8004   │
                    └──┬───┬───┬──┘
                       │   │   │
            ┌──────────┘   │   └──────────┐
            │              │              │
     ┌──────▼──────┐ ┌────▼────┐  ┌──────▼──────┐
     │ PostgreSQL  │ │  Redis  │  │   Celery    │
     │   Port 5435 │ │  6382   │  │   Worker    │
     │  13 tables  │ │ broker  │  │  + Flower   │
     └─────────────┘ └─────────┘  └─────────────┘
```

## Backend - FastAPI

### Couches applicatives

```
┌─────────────────────────────────────────────┐
│                  main.py                     │
│  FastAPI app + CORS + Rate Limiting          │
├─────────────────────────────────────────────┤
│              Core Routers                    │
│  auth.py (JWT)  │  ai_assistant/ (AI Router) │
├─────────────────────────────────────────────┤
│           ModuleRegistry                     │
│  Auto-decouverte via manifest.json           │
├──────┬──────┬──────┬──────┬──────┬──────┬───┤
│trans │conv  │bill  │comp  │pipe  │know  │ws │
│crip  │ersa  │ing   │are   │lines │ledge │   │
│tion  │tion  │      │      │      │      │   │
├──────┴──────┴──────┴──────┴──────┴──────┴───┤
│              Service Layer                   │
│  Business logic (async, no HTTP concerns)    │
├─────────────────────────────────────────────┤
│              Data Layer                      │
│  SQLModel + AsyncSession (PostgreSQL)        │
│  Redis (rate limiting, Celery broker)        │
└─────────────────────────────────────────────┘
```

### Module Plugin Pattern

Chaque module est un dossier auto-decouvert sous `app/modules/` :

```
app/modules/{name}/
├── manifest.json    # Metadata (name, version, prefix, tags, enabled)
├── routes.py        # APIRouter expose comme `router`
├── service.py       # Logique metier (classes statiques async)
├── schemas.py       # Pydantic schemas (request/response)
├── middleware.py     # Dependencies FastAPI (optionnel)
└── __init__.py      # Package marker
```

**Flux de decouverte** :
1. `ModuleRegistry.discover_modules(app)` au demarrage
2. Scan des sous-dossiers de `app/modules/`
3. Lecture et validation de `manifest.json`
4. Import dynamique de `routes.py` via `importlib`
5. `app.include_router(router, prefix=manifest.prefix)`

### 7 Modules enregistres

| Module | Prefix | Description |
|--------|--------|-------------|
| transcription | /api/transcription | Transcription multi-source (YouTube, upload, micro) |
| conversation | /api/conversations | Chat IA avec SSE streaming |
| billing | /api/billing | Plans, quotas, Stripe checkout/webhooks |
| compare | /api/compare | Comparaison multi-modele parallele |
| pipelines | /api/pipelines | Pipeline builder avec execution sequentielle |
| knowledge | /api/knowledge | Knowledge base, chunking, TF-IDF search, RAG |
| api_keys | /api/keys | Gestion cles API + endpoints publics /v1 |
| workspaces | /api/workspaces | Collaboration, membres, partage, commentaires |

## AI Router

```
Input text
    │
    ▼
ContentClassifier.classify()
    │ domain, tone, sensitivity, language
    ▼
ModelSelector.select_model(classification, strategy)
    │ provider, model, parameters
    ▼
PromptSelector.select_prompt(classification, task)
    │ system prompt + user prompt
    ▼
Provider.generate() / Provider.stream()
    │ Gemini / Claude / Groq
    ▼
Output (text or SSE stream)
```

**Strategies de selection** :
- `BALANCED` : Meilleur modele pour le domaine
- `COST_OPTIMIZED` : Privilege les modeles gratuits (Groq > Gemini > Claude)
- `CONSERVATIVE` : Modeles les plus fiables pour contenu sensible

## Base de donnees - 13 tables

### Diagramme des relations

```
users ─────┬──────────────────────────────────────────────────┐
           │                                                   │
           ├── transcriptions                                  │
           │                                                   │
           ├── conversations ── messages                       │
           │                                                   │
           ├── user_quotas ── plans                           │
           │                                                   │
           ├── comparison_results ── comparison_votes          │
           │                                                   │
           ├── pipelines ── pipeline_executions                │
           │                                                   │
           ├── documents ── document_chunks                    │
           │                                                   │
           ├── api_keys                                        │
           │                                                   │
           └── workspaces ── workspace_members                 │
                          ── shared_items ── comments          │
```

### Tables par module

| Table | Module | Champs cles |
|-------|--------|-------------|
| users | auth | email, role (admin/user), hashed_password |
| transcriptions | transcription | video_url, source_type, status, text, confidence |
| conversations | conversation | user_id, transcription_id, title |
| messages | conversation | conversation_id, role, content, provider |
| plans | billing | name (free/pro/enterprise), limites, stripe_price_id |
| user_quotas | billing | user_id, plan_id, *_used counters, stripe IDs |
| comparison_results | compare | prompt, providers_used, results_json |
| comparison_votes | compare | comparison_id, provider_name, quality_score (1-5) |
| pipelines | pipelines | name, steps_json, status (draft/active/archived) |
| pipeline_executions | pipelines | pipeline_id, status, current_step, results_json |
| documents | knowledge | filename, content_type, total_chunks, status |
| document_chunks | knowledge | document_id, content, chunk_index |
| api_keys | api_keys | key_hash (SHA-256), key_prefix, permissions_json |
| workspaces | workspaces | name, owner_id, is_active |
| workspace_members | workspaces | workspace_id, user_id, role (owner/editor/viewer) |
| shared_items | workspaces | workspace_id, item_type, item_id |
| comments | workspaces | shared_item_id, user_id, content |

## Authentification

### JWT Flow

```
Login (email/password)
    │
    ▼
POST /api/auth/login
    │
    ├── access_token (30 min, type=access)
    └── refresh_token (7 jours, type=refresh)

Requete authentifiee
    │
    ▼
Header: Authorization: Bearer {access_token}
    │
    ▼
get_current_user() dependency
    │ decode JWT, verify type=access, lookup user
    ▼
User object injected

Token expire?
    │
    ▼
POST /api/auth/refresh {refresh_token}
    │
    ▼
Nouvelle paire access+refresh (rotation)
```

### API Key Auth (Public API v1)

```
Header: X-API-Key: sk-{token}
    │
    ▼
verify_api_key() dependency
    │ SHA-256 hash, lookup in api_keys table
    │ check is_active, check expiration
    │ update last_used_at
    ▼
(user_id, permissions) tuple
```

## Celery Workers

```
FastAPI (web)                    Celery Worker
    │                                │
    │  _celery_available()?          │
    │  ├── YES: task.delay() ───────>│  process_transcription_task()
    │  └── NO: BackgroundTasks       │  process_upload_task()
    │                                │
    │                          Redis (broker)
    │                                │
    │                          Flower (monitoring :5555)
```

**Configuration** :
- Broker + Backend : Redis
- Serializer : JSON
- Retries : 3 max, backoff exponentiel (max 600s)
- Concurrency : 2 workers
- `task_acks_late=True` (pas de perte de taches)

## Frontend - Next.js 15

### Architecture

```
src/
├── app/
│   ├── (auth)/          # Login, Register (public)
│   ├── (dashboard)/     # 10 pages protegees
│   └── layout.tsx
├── features/            # Domain modules
│   ├── {name}/
│   │   ├── types.ts     # TypeScript interfaces
│   │   ├── api.ts       # Axios API calls
│   │   └── hooks/       # React Query hooks
├── components/          # Shared UI components
├── contexts/            # AuthContext (React Context)
├── hooks/               # useSSE, shared hooks
└── lib/
    └── apiClient.ts     # Axios + intercepteurs (retry, refresh)
```

### Flux de donnees

```
Component
    │ useQuery / useMutation (TanStack Query)
    ▼
Hook (features/{name}/hooks/)
    │ appelle API function
    ▼
API (features/{name}/api.ts)
    │ apiClient.get/post/put/delete
    ▼
Axios interceptor
    │ ajoute Bearer token
    │ retry 5xx (3 fois, backoff)
    │ refresh token auto sur 401
    ▼
Backend FastAPI
```

## Stripe Integration

```
Frontend                    Backend                     Stripe
    │                          │                          │
    │ Click "Upgrade"          │                          │
    ├─ POST /billing/checkout ─>│                          │
    │                          ├─ stripe.checkout.create ─>│
    │                          │<── checkout_url ──────────│
    │<── redirect ─────────────│                          │
    │                          │                          │
    │ (user pays on Stripe)    │                          │
    │                          │<── webhook ───────────────│
    │                          │  checkout.session.completed
    │                          │  -> upgrade plan           │
    │                          │  -> save subscription_id   │
    │                          │                          │
    │ Click "Manage"           │                          │
    ├─ POST /billing/portal ──>│                          │
    │                          ├─ billing_portal.create ──>│
    │<── redirect ─────────────│                          │
```

## Securite

| Couche | Implementation |
|--------|----------------|
| Auth | JWT access (30min) + refresh (7j), bcrypt passwords |
| RBAC | Roles user/admin, `require_role()` dependency |
| Rate Limiting | SlowAPI + Redis (par endpoint, fallback in-memory) |
| Quotas | Verification automatique avant operations couteuses (402) |
| API Keys | SHA-256 hash, prefix visible, secret jamais stocke |
| CORS | Origins configurables via env var |
| Input validation | Pydantic schemas, field_validators, sanitize HTML |
| Secrets | Pas de credentials dans le code, tout en .env |
| CI/CD | GitHub Actions (lint, test, build, Trivy security scan) |

## Monitoring

| Outil | Usage |
|-------|-------|
| Prometheus | Metriques HTTP, transcription jobs, AI provider calls |
| Flower | Dashboard Celery workers (port 5555) |
| structlog | Logging structure JSON |
| `/health` | Health check endpoint |
| `/metrics` | Prometheus endpoint (dev ou token) |
