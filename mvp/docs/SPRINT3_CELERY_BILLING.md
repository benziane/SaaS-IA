# Sprint 3 : Celery Workers + Multi-tenancy / Quotas

**Date** : 2026-03-22
**Version** : MVP 2.3.0
**Statut** : Termine

---

## 1. Event-Driven Architecture avec Celery

### Architecture

```
Frontend                    Backend (FastAPI)                  Celery Worker
   |                              |                                |
   |-- POST /transcription ------>|                                |
   |                              |-- celery_available()? -------->|
   |                              |   YES: task.delay() ---------> |-- process_transcription_task()
   |                              |   NO: BackgroundTasks          |-- DB: pending -> processing
   |<-- 201 {job_id} ------------|                                |-- AssemblyAI / MOCK
   |                              |                                |-- DB: completed/failed
   |-- GET /transcription/{id} -->|                                |-- retry x3 (backoff)
   |<-- {status, text, ...} -----|                                |
```

### Backend

**Fichiers crees** :
- `app/celery_app.py` : Instance Celery avec Redis broker/backend, auto-decouverte des taches
- `app/modules/transcription/tasks.py` : Taches `process_transcription_task` et `process_upload_task`
- `app/modules/conversation/tasks.py` : Placeholder pour futur traitement IA async

**Fichiers modifies** :
- `app/modules/transcription/routes.py` : Dispatch Celery avec fallback BackgroundTasks
- `docker-compose.yml` : Services `worker` et `flower` ajoutes
- `requirements.txt` / `pyproject.toml` : celery[redis], flower

**Configuration Celery** :
```python
celery_app = Celery("saas_ia", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
celery_app.autodiscover_tasks([
    "app.modules.transcription",
    "app.modules.conversation",
])
```

**Taches Celery** :

| Tache | Nom | Retries | Backoff |
|-------|-----|---------|---------|
| process_transcription_task | transcription.process | 3 | Exponentiel (max 600s) |
| process_upload_task | transcription.process_upload | 3 | Exponentiel (max 600s) |
| process_ai_response_task | conversation.process_ai_response | - | Placeholder |

**Fallback** :
Le systeme detecte automatiquement si un worker Celery est disponible via `_celery_available()`.
Si aucun worker n'est joignable, les taches sont executees via `BackgroundTasks` FastAPI (mode dev).

**Docker Compose** :

| Service | Image | Port | Commande |
|---------|-------|------|----------|
| worker | backend | - | `celery -A app.celery_app worker --loglevel=info --concurrency=2` |
| flower | backend | 5555 | `celery -A app.celery_app flower --port=5555` |

---

## 2. Multi-tenancy et Systeme de Quotas

### Architecture

```
Frontend                    Backend (FastAPI)
   |                              |
   |-- POST /transcription ------>| require_transcription_quota (Depends)
   |                              |   -> BillingService.check_quota()
   |                              |   -> 402 si quota depasse
   |                              |   -> BillingService.consume_quota()
   |<-- 201 / 402 ---------------|
   |                              |
   |-- GET /billing/quota ------->| get_user_quota()
   |<-- {plan, usage, limits} ---|
   |                              |
   |-- GET /billing/plans ------->| get_or_create_plans()
   |<-- [{free, pro, enterprise}]-|
```

### Backend

**Modeles** (`app/models/billing.py`) :

```
plans
  id                    UUID PK
  name                  ENUM (free, pro, enterprise) UNIQUE
  display_name          VARCHAR(50)
  max_transcriptions_month  INT
  max_audio_minutes_month   INT
  max_ai_calls_month        INT
  price_cents           INT
  is_active             BOOL
  created_at            DATETIME

user_quotas
  id                    UUID PK
  user_id               UUID FK -> users.id
  plan_id               UUID FK -> plans.id
  transcriptions_used   INT (default 0)
  audio_minutes_used    INT (default 0)
  ai_calls_used         INT (default 0)
  period_start          DATE
  period_end            DATE
  created_at            DATETIME
  updated_at            DATETIME
```

**Plans par defaut** :

| Plan | Transcriptions/mois | Minutes audio | Appels IA | Prix |
|------|---------------------|---------------|-----------|------|
| Free | 10 | 60 | 50 | 0 EUR |
| Pro | 100 | 600 | 500 | 19 EUR/mois |
| Enterprise | Illimite | Illimite | Illimite | Sur devis |

**Service** (`app/modules/billing/service.py`) :
- `get_or_create_plans()` : Seed les plans par defaut si absents
- `get_user_quota()` : Retourne ou cree le quota mensuel (Free par defaut)
- `check_quota()` : Verifie si le quota n'est pas depasse
- `consume_quota()` : Incremente l'usage apres une operation
- `reset_monthly_quotas()` : Reset les compteurs en fin de periode

**Endpoints** :

| Methode | Endpoint | Description | Auth | Rate Limit |
|---------|----------|-------------|------|------------|
| GET | /api/billing/plans | Liste des plans disponibles | Non | 30/min |
| GET | /api/billing/quota | Quota de l'utilisateur courant | Oui | 30/min |

**Integration quotas** :

| Endpoint protege | Resource | Erreur si depasse |
|-----------------|----------|-------------------|
| POST /api/transcription/ | transcription | 402 Payment Required |
| POST /api/transcription/upload | transcription | 402 Payment Required |
| POST /api/conversations/{id}/messages | ai_call | 402 Payment Required |

### Frontend

**Page** : `/billing` (`src/app/(dashboard)/billing/page.tsx`)
- Plan actuel de l'utilisateur avec chip
- Barres de progression pour chaque ressource (transcriptions, minutes audio, appels IA)
- Alertes quand usage >= 80% (warning) ou >= 100% (error)
- Grille comparative des plans disponibles

**Composants** :
- `QuotaWidget` (`components/ui/QuotaWidget.tsx`) : widget compact pour le dashboard
- `QuotaBar` : barre de progression coloree (vert/orange/rouge)

**API + Hooks** (`features/billing/`) :
- `api.ts` : `getPlans()`, `getQuota()`
- `hooks/useBilling.ts` : `usePlans()` (staleTime 5min), `useQuota()` (refetch 30s)

**Navigation** : "Billing" ajoute dans la section Account avec icone `tabler:credit-card`

---

## 3. Nouveaux endpoints API

| Methode | Endpoint | Description | Auth | Rate Limit |
|---------|----------|-------------|------|------------|
| GET | /api/billing/plans | Plans disponibles | Non | 30/min |
| GET | /api/billing/quota | Quota utilisateur | Oui | 30/min |

---

## 4. Migration base de donnees

```sql
CREATE TABLE plans (
  id UUID PRIMARY KEY,
  name VARCHAR(20) UNIQUE NOT NULL,
  display_name VARCHAR(50) NOT NULL,
  max_transcriptions_month INT NOT NULL DEFAULT 10,
  max_audio_minutes_month INT NOT NULL DEFAULT 60,
  max_ai_calls_month INT NOT NULL DEFAULT 50,
  price_cents INT NOT NULL DEFAULT 0,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_quotas (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  plan_id UUID REFERENCES plans(id),
  transcriptions_used INT NOT NULL DEFAULT 0,
  audio_minutes_used INT NOT NULL DEFAULT 0,
  ai_calls_used INT NOT NULL DEFAULT 0,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_quotas_user ON user_quotas(user_id);
CREATE INDEX idx_plans_name ON plans(name);
```

---

## 5. Dependances ajoutees

| Package | Version | Usage |
|---------|---------|-------|
| celery[redis] | 5.3.6 | Task queue, workers |
| flower | 2.0.1 | Worker monitoring UI |
| python-dateutil | 2.8.0+ | Date manipulation (billing periods) |

---

## 6. Nouvelle page frontend

| Route | Description |
|-------|-------------|
| /billing | Plan actuel, usage, plans disponibles |

**Navigation mise a jour** :
```
Dashboard
AI Modules
  Transcription
  Chat IA
Platform
  Modules
Account
  Profile
  Billing          <-- NOUVEAU
```
