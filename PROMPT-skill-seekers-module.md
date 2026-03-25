# Prompt : Implémenter le module `skill_seekers` dans SaaS-IA

## Contexte

Tu es un agent expert de la plateforme **SaaS-IA MVP** — une plateforme SaaS modulaire d'IA enterprise construite sur **FastAPI + Next.js 15**. Tu connais parfaitement son architecture.

**Objectif** : Ajouter un nouveau module complet `skill_seekers` qui expose une interface web pour piloter l'outil CLI [Skill Seekers](https://github.com/yusufkaraaslan/Skill_Seekers) (`pip install skill-seekers`). Ce module permet à l'utilisateur de scraper des repos GitHub, packager le résultat au format Claude et télécharger les fichiers `.md` générés — le tout depuis l'interface SaaS-IA.

---

## Architecture de référence

### Stack
- **Backend** : FastAPI 0.135 + Python 3.13 + SQLModel + AsyncPG + Redis + Celery
- **Frontend** : Next.js 15 (App Router) + React 18 + MUI 6 + TanStack Query 5 + Axios
- **Auth** : JWT via `Depends(get_current_user)`
- **Logging** : `structlog.get_logger()`
- **Rate limiting** : `@limiter.limit("10/minute")`

### Pattern de module (à reproduire exactement)

Chaque module suit cette structure dans `mvp/backend/app/modules/<nom>/` :

```
manifest.json     ← déclaration + auto-discovery
__init__.py       ← vide ou minimal
schemas.py        ← Pydantic BaseModel (request / response)
service.py        ← logique métier (class XxxService)
routes.py         ← APIRouter avec endpoints + auth + rate limit
```

#### Référence : module `transcription`
- `manifest.json` → `{"name": "transcription", "version": "1.0.0", "prefix": "/api/transcription", "tags": ["transcription"], "enabled": true, "dependencies": ["assemblyai"]}`
- `service.py` → classe `TranscriptionService`, mock mode si clé absente, `structlog`
- `routes.py` → `router = APIRouter()`, `Depends(get_current_user)`, `Depends(get_session)`, `@limiter.limit()`

#### Référence : module `pipelines`
- `service.py` → orchestration multi-steps, statuts (pending/running/completed/failed)
- `schemas.py` → `PipelineStep`, `PipelineCreate`, `PipelineRead`, `ExecutionRead`

### Pattern frontend (à reproduire exactement)

Chaque feature dans `mvp/frontend/src/features/<nom-kebab>/` :

```
types.ts          ← interfaces TypeScript + enums
api.ts            ← endpoints Axios centralisés (ENDPOINTS const)
hooks/
  useSkillSeekers.ts          ← React Query (useQuery)
  useSkillSeekersMutations.ts ← mutations (useMutation)
```

#### Référence : feature `transcription`
- `api.ts` → `const TRANSCRIPTION_ENDPOINTS = { LIST: '/api/transcription', ... } as const`
- `hooks/useTranscriptions.ts` → `useQuery({ queryKey: ['transcriptions'], queryFn: ... })`
- `types.ts` → `enum TranscriptionStatus { PENDING = 'pending', ... }`

---

## Ce que Skill Seekers CLI peut faire

```bash
# Installer
pip install skill-seekers

# Scraper un repo GitHub
skill-seekers create <owner/repo>  --output <dossier>
# Exemple : skill-seekers create travisvn/awesome-claude-skills --output output/awesome

# Packager pour Claude
skill-seekers package <dossier> --target claude --output <fichier.md>
# Exemple : skill-seekers package output/awesome --target claude --output result/awesome-claude.md

# Enhancement IA (optionnel, nécessite ANTHROPIC_API_KEY)
skill-seekers enhance <dossier>

# Autres targets disponibles : gemini, openai, langchain, llama-index, markdown
```

---

## Fichiers à créer

### Backend — 5 fichiers

#### 1. `mvp/backend/app/modules/skill_seekers/manifest.json`
```json
{
  "name": "skill_seekers",
  "version": "1.0.0",
  "description": "Skill Seekers — scraping de repos GitHub et packaging pour Claude AI",
  "prefix": "/api/skill-seekers",
  "tags": ["skill-seekers"],
  "enabled": true,
  "dependencies": ["skill-seekers"]
}
```

#### 2. `mvp/backend/app/modules/skill_seekers/__init__.py`
Vide.

#### 3. `mvp/backend/app/modules/skill_seekers/schemas.py`

Modèles Pydantic requis :

```python
# Request : lancer un job de scraping
class ScrapeJobCreate(BaseModel):
    repos: list[str]           # ex: ["travisvn/awesome-claude-skills", "obra/superpowers"]
    targets: list[str] = ["claude"]  # formats d'export : claude, gemini, openai, markdown…
    enhance: bool = False      # lancer skill-seekers enhance (nécessite ANTHROPIC_API_KEY)

# Response : état d'un job
class ScrapeJobRead(BaseModel):
    id: UUID
    user_id: UUID
    repos: list[str]
    targets: list[str]
    enhance: bool
    status: str                # pending | running | completed | failed
    progress: int              # 0-100
    current_step: str          # ex: "Scraping travisvn/awesome-claude-skills…"
    output_files: list[str]    # chemins des .md générés
    error: str | None
    created_at: datetime
    updated_at: datetime

# Response paginée
class PaginatedJobs(BaseModel):
    items: list[ScrapeJobRead]
    total: int
    skip: int
    limit: int
    has_more: bool
```

#### 4. `mvp/backend/app/modules/skill_seekers/service.py`

Classe `SkillSeekersService` avec :

- **`__init__`** : détecter si `skill-seekers` est installé via `shutil.which("skill-seekers")`. Si absent, activer `mock_mode = True` (simuler les jobs). Logger via `structlog`.
- **`create_job(repos, targets, enhance, user_id, session)`** : créer un enregistrement `ScrapeJob` en DB avec statut `pending`, retourner l'objet.
- **`run_job(job_id, session)`** : méthode async qui :
  1. Met le statut à `running`
  2. Pour chaque repo dans `job.repos` :
     - Appelle `skill-seekers create <repo> --output <tmpdir>/<repo_slug>` via `asyncio.create_subprocess_exec`
     - Capture stdout/stderr
     - Appelle `skill-seekers package <tmpdir>/<repo_slug> --target <target> --output <output_path>` pour chaque target
  3. Si `enhance=True` et `ANTHROPIC_API_KEY` défini : appelle `skill-seekers enhance <dossier>`
  4. Met à jour `progress`, `current_step`, `output_files` au fur et à mesure
  5. Met le statut à `completed` ou `failed`
- **`get_jobs(user_id, skip, limit, session)`** : lister les jobs paginés
- **`get_job(job_id, user_id, session)`** : récupérer un job par ID
- **`delete_job(job_id, user_id, session)`** : supprimer un job
- **`get_output_file(job_id, filename, user_id, session)`** : retourner le chemin du fichier généré pour téléchargement
- **`is_installed()`** : retourne `bool`, vérifie `shutil.which("skill-seekers")`

**Mock mode** : si `skill-seekers` non installé, simuler un job qui progresse de 0% à 100% avec `asyncio.sleep`, générer un `.md` factice.

**Stockage des fichiers** : dans `settings.UPLOAD_DIR / "skill_seekers" / str(user_id) / str(job_id)/`. Créer ce dossier si absent.

#### 5. `mvp/backend/app/modules/skill_seekers/routes.py`

Endpoints à créer :

```
POST   /api/skill-seekers/jobs              → créer + lancer un job (background task)
GET    /api/skill-seekers/jobs              → lister les jobs (paginé, ?skip=0&limit=20)
GET    /api/skill-seekers/jobs/{job_id}     → détail d'un job
DELETE /api/skill-seekers/jobs/{job_id}     → supprimer un job
GET    /api/skill-seekers/jobs/{job_id}/download/{filename}  → télécharger un .md
GET    /api/skill-seekers/status            → {"installed": bool, "version": str|None}
```

Tous les endpoints nécessitent `Depends(get_current_user)` sauf éventuellement `/status`.
Rate limit : `@limiter.limit("5/minute")` sur POST, `@limiter.limit("30/minute")` sur GET.
Le job est lancé en arrière-plan via `BackgroundTasks` (FastAPI) — ne pas bloquer la réponse.

---

### Base de données — 1 fichier

#### 6. `mvp/backend/app/models/skill_seekers.py`

Modèle SQLModel :

```python
class ScrapeJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScrapeJob(SQLModel, table=True):
    __tablename__ = "scrape_jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)

    # Config
    repos_json: str = Field(default="[]")       # JSON list of repo strings
    targets_json: str = Field(default='["claude"]')
    enhance: bool = Field(default=False)

    # State
    status: ScrapeJobStatus = Field(default=ScrapeJobStatus.PENDING)
    progress: int = Field(default=0)            # 0-100
    current_step: str = Field(default="")
    output_files_json: str = Field(default="[]") # JSON list of filenames
    error: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

Ajouter l'import dans `mvp/backend/app/database.py` dans `init_db()` :
```python
from app.models.skill_seekers import ScrapeJob, ScrapeJobStatus  # noqa: F401
```

Créer une migration Alembic :
```bash
cd mvp/backend
alembic revision --autogenerate -m "add scrape_jobs table"
alembic upgrade head
```

---

### Frontend — 4 fichiers

#### 7. `mvp/frontend/src/features/skill-seekers/types.ts`

```typescript
export enum ScrapeJobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export type ExportTarget = 'claude' | 'gemini' | 'openai' | 'langchain' | 'llama-index' | 'markdown';

export interface ScrapeJob {
  id: string;
  user_id: string;
  repos: string[];
  targets: ExportTarget[];
  enhance: boolean;
  status: ScrapeJobStatus;
  progress: number;           // 0-100
  current_step: string;
  output_files: string[];
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScrapeJobCreateRequest {
  repos: string[];
  targets: ExportTarget[];
  enhance?: boolean;
}

export interface ScrapeJobListResponse {
  items: ScrapeJob[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface SkillSeekersStatus {
  installed: boolean;
  version: string | null;
}
```

#### 8. `mvp/frontend/src/features/skill-seekers/api.ts`

```typescript
import apiClient from '@/lib/apiClient';
import type { ScrapeJob, ScrapeJobCreateRequest, ScrapeJobListResponse, SkillSeekersStatus } from './types';

const ENDPOINTS = {
  JOBS: '/api/skill-seekers/jobs',
  JOB: (id: string) => `/api/skill-seekers/jobs/${id}`,
  DOWNLOAD: (id: string, filename: string) => `/api/skill-seekers/jobs/${id}/download/${filename}`,
  STATUS: '/api/skill-seekers/status',
} as const;

export const createScrapeJob = (data: ScrapeJobCreateRequest) =>
  apiClient.post<ScrapeJob>(ENDPOINTS.JOBS, data).then(r => r.data);

export const getScrapeJobs = (params?: { skip?: number; limit?: number }) =>
  apiClient.get<ScrapeJobListResponse>(ENDPOINTS.JOBS, { params }).then(r => r.data);

export const getScrapeJob = (id: string) =>
  apiClient.get<ScrapeJob>(ENDPOINTS.JOB(id)).then(r => r.data);

export const deleteScrapeJob = (id: string) =>
  apiClient.delete(ENDPOINTS.JOB(id)).then(r => r.data);

export const getSkillSeekersStatus = () =>
  apiClient.get<SkillSeekersStatus>(ENDPOINTS.STATUS).then(r => r.data);

export const getDownloadUrl = (jobId: string, filename: string) =>
  `${process.env.NEXT_PUBLIC_API_URL || ''}${ENDPOINTS.DOWNLOAD(jobId, filename)}`;
```

#### 9. `mvp/frontend/src/features/skill-seekers/hooks/index.ts`

```typescript
export * from './useSkillSeekers';
export * from './useSkillSeekersMutations';
```

#### 10. `mvp/frontend/src/features/skill-seekers/hooks/useSkillSeekers.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { getScrapeJobs, getScrapeJob, getSkillSeekersStatus } from '../api';

export const useSkillSeekersJobs = (params?: { skip?: number; limit?: number }) =>
  useQuery({
    queryKey: ['skill-seekers-jobs', params],
    queryFn: () => getScrapeJobs(params),
    staleTime: 1000 * 30,
  });

export const useSkillSeekersJob = (id: string) =>
  useQuery({
    queryKey: ['skill-seekers-job', id],
    queryFn: () => getScrapeJob(id),
    enabled: !!id,
    refetchInterval: (data) =>
      data?.status === 'running' || data?.status === 'pending' ? 2000 : false,
  });

export const useSkillSeekersStatus = () =>
  useQuery({
    queryKey: ['skill-seekers-status'],
    queryFn: getSkillSeekersStatus,
    staleTime: 1000 * 60 * 5,
  });
```

#### 11. `mvp/frontend/src/features/skill-seekers/hooks/useSkillSeekersMutations.ts`

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createScrapeJob, deleteScrapeJob } from '../api';

export const useCreateScrapeJob = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createScrapeJob,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['skill-seekers-jobs'] }),
  });
};

export const useDeleteScrapeJob = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteScrapeJob,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['skill-seekers-jobs'] }),
  });
};
```

---

### Page UI — 1 fichier

#### 12. `mvp/frontend/src/app/(dashboard)/skill-seekers/page.tsx`

Créer une page Next.js App Router complète avec MUI 6 :

**Layout de la page** :
```
┌─────────────────────────────────────────────────────┐
│  Skill Seekers                          [+ Nouveau]  │
│  Scraper des repos GitHub pour Claude Code           │
├──────────────────┬──────────────────────────────────┤
│  NOUVEAU JOB     │  HISTORIQUE DES JOBS              │
│                  │                                   │
│  Repos GitHub    │  [Card job 1 - completed ✓]       │
│  ─────────────   │    travisvn/awesome-claude-skills  │
│  [Input + Add]   │    ████████████ 100%               │
│  • repo1         │    📥 awesome-claude.md           │
│  • repo2         │                                   │
│                  │  [Card job 2 - running ⟳]         │
│  Format export   │    obra/superpowers               │
│  [claude ✓]      │    ████░░░░░░ 40%                 │
│  [gemini]        │    Packaging superpowers…         │
│  [openai]        │                                   │
│                  │  [Card job 3 - failed ✗]          │
│  Enhancement IA  │    invalid/repo                   │
│  [Toggle]        │    Repo not found                 │
│                  │                                   │
│  [Lancer]        │                                   │
└──────────────────┴──────────────────────────────────┘
```

**Composants à utiliser** (MUI 6) :
- `Typography`, `Button`, `TextField`, `Chip`, `CircularProgress`
- `LinearProgress` pour la barre de progression
- `Card`, `CardContent`, `CardActions`
- `Alert` si skill-seekers non installé
- `Checkbox` ou `ToggleButtonGroup` pour les targets
- `Switch` pour l'enhancement IA
- `Tooltip` sur les boutons download

**Comportement** :
- Poll automatique toutes les 2s sur les jobs en `running` ou `pending` (géré par `refetchInterval` dans `useSkillSeekersJob`)
- Bouton download déclenche un `window.open(getDownloadUrl(...))` pour télécharger le `.md`
- Si `status.installed === false` : afficher un `Alert` warning "Skill Seekers non installé — Lancez `pip install skill-seekers`"
- Validation : au moins 1 repo et 1 target avant de soumettre

---

## Contraintes impératives

1. **Ne jamais supprimer** de module existant ni de technologie en place
2. **Toujours utiliser** `structlog.get_logger()` pour les logs backend
3. **Auth obligatoire** sur tous les endpoints sauf `/status` via `Depends(get_current_user)`
4. **Mock mode** : si `skill-seekers` CLI non installé, simuler les jobs avec `asyncio.sleep` + progression fictive + fichier `.md` factice contenant un message explicatif
5. **Pas de `subprocess.run` bloquant** — utiliser `asyncio.create_subprocess_exec` pour ne pas bloquer la boucle d'événements
6. **Nettoyage** : supprimer les fichiers temporaires après récupération, ou proposer un TTL (ex: 24h via Celery periodic task)
7. **Erreurs** : capturer les exceptions subprocess, logger l'erreur, mettre `status=failed` + `error=str(e)`
8. **Sécurité** : valider que les noms de repos ne contiennent pas de caractères dangereux (whitelist `[a-zA-Z0-9_\-\./]`)
9. **Grade S+++** : suivre exactement les patterns existants (PaginatedResponse, structlog, async sessions, Pydantic v2)

---

## Fichiers de référence à lire AVANT d'implémenter

```
# Module complet de référence
mvp/backend/app/modules/transcription/manifest.json
mvp/backend/app/modules/transcription/routes.py
mvp/backend/app/modules/transcription/service.py
mvp/backend/app/schemas/transcription.py
mvp/backend/app/models/transcription.py

# Module avec jobs multi-steps
mvp/backend/app/modules/pipelines/manifest.json
mvp/backend/app/modules/pipelines/routes.py
mvp/backend/app/modules/pipelines/service.py
mvp/backend/app/modules/pipelines/schemas.py
mvp/backend/app/models/pipeline.py

# Auto-discovery
mvp/backend/app/modules/__init__.py

# Config & Auth
mvp/backend/app/config.py
mvp/backend/app/auth.py

# Frontend référence
mvp/frontend/src/features/transcription/types.ts
mvp/frontend/src/features/transcription/api.ts
mvp/frontend/src/features/transcription/hooks/useTranscriptions.ts
mvp/frontend/src/features/transcription/hooks/useTranscriptionMutations.ts
mvp/frontend/src/features/pipelines/types.ts
```

---

## Ordre d'implémentation recommandé

```
1. mvp/backend/app/models/skill_seekers.py          ← modèle DB
2. mvp/backend/app/modules/skill_seekers/manifest.json
3. mvp/backend/app/modules/skill_seekers/__init__.py
4. mvp/backend/app/modules/skill_seekers/schemas.py
5. mvp/backend/app/modules/skill_seekers/service.py  ← logique CLI + mock
6. mvp/backend/app/modules/skill_seekers/routes.py   ← endpoints API
7. Alembic migration (scrape_jobs table)
8. mvp/frontend/src/features/skill-seekers/types.ts
9. mvp/frontend/src/features/skill-seekers/api.ts
10. mvp/frontend/src/features/skill-seekers/hooks/
11. mvp/frontend/src/app/(dashboard)/skill-seekers/page.tsx
```

---

## Vérification finale

Après implémentation, vérifier :

```bash
# Backend démarre sans erreur
cd mvp/backend && uvicorn app.main:app --reload

# Module auto-découvert dans les logs
# → modules_registered: [..., "skill_seekers"]

# Endpoints visibles dans Swagger
# → http://localhost:8000/docs#/skill-seekers

# Frontend compile sans erreur TypeScript
cd mvp/frontend && pnpm build

# Test manuel
# 1. POST /api/skill-seekers/jobs avec {"repos": ["travisvn/awesome-claude-skills"], "targets": ["claude"]}
# 2. GET /api/skill-seekers/jobs/{id} → progress augmente
# 3. GET /api/skill-seekers/jobs/{id} → status = "completed"
# 4. GET /api/skill-seekers/jobs/{id}/download/awesome-claude-skills-claude.md → téléchargement
```
