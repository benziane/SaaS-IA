# ROADMAP - SaaS-IA Platform

**Date de mise a jour** : 2026-03-22
**Version actuelle** : MVP 2.0.0
**Objectif** : Plateforme SaaS d'orchestration IA multi-modules, production-ready

---

## VUE D'ENSEMBLE

SaaS-IA est une plateforme modulaire d'intelligence artificielle. La vision est de passer d'un outil de transcription a une **plateforme d'orchestration IA** permettant de chainer, comparer et deployer des services IA via une interface unifiee.

### Legendes

- FAIT : Implemente et fonctionnel
- EN COURS : Partiellement implemente
- A FAIRE : Planifie, non demarre
- FUTUR : Vision long terme

---

## PHASE 0 : ASSAINISSEMENT SECURITE [FAIT]

> Reprise du projet apres plusieurs semaines d'arret. Nettoyage complet.

| Tache | Statut |
|-------|--------|
| Suppression cles API hardcodees (gemini.py, 3 cles retirees) | FAIT |
| Suppression credentials par defaut dans config.py | FAIT |
| Checks de securite au demarrage (SECRET_KEY, DATABASE_URL) | FAIT |
| Protection endpoints debug (role ADMIN ou env development) | FAIT |
| Correction bare `except:` en `except Exception:` | FAIT |
| Ajout .gitignore defense en profondeur (mvp/, mvp/backend/) | FAIT |
| Remplacement URLs localhost hardcodees par env vars | FAIT |
| UserDropdown : donnees reelles depuis AuthContext | FAIT |

---

## PHASE 1 : STABILISATION TECHNIQUE [FAIT]

> TypeScript strict, auth unifiee, error boundaries, nettoyage code.

| Tache | Statut |
|-------|--------|
| TypeScript strict mode reactive (ignoreBuildErrors retire) | FAIT |
| Correction de toutes les erreurs TypeScript | FAIT |
| Unification systeme auth (AuthContext seul, suppression useAuthStore) | FAIT |
| Suppression AuthGuard duplique (hocs/) | FAIT |
| Error boundaries Next.js (error.tsx, not-found.tsx) | FAIT |
| Nettoyage console.log de debug (AuthContext, AuthGuard, store) | FAIT |
| Reorganisation fichiers orphelins (docs/changelog/, tests/) | FAIT |
| Declaration types CSS modules et SVG | FAIT |

---

## PHASE 2 : FONCTIONNALITES CORE [FAIT]

> Refresh token, pagination, dashboard, transcription complete, profil.

| Tache | Statut |
|-------|--------|
| **Refresh token** : rotation JWT 7 jours backend + intercepteur auto frontend | FAIT |
| **Pagination** : PaginatedResponse generique, total count, has_more | FAIT |
| **Dashboard** : stats reelles (total, completed, failed, duree), transcriptions recentes | FAIT |
| **Transcription** : selection langue, affichage resultats, export TXT/SRT, copie clipboard | FAIT |
| **Profil** : page profil, edition nom, changement mot de passe, validation Zod | FAIT |
| Navigation : entree "Profile" dans le menu lateral | FAIT |

---

## PHASE 3 : PRODUCTION-READY [FAIT]

> Redis rate limit, validation, CI/CD, tests, metriques.

| Tache | Statut |
|-------|--------|
| **Rate limiting Redis** : migration in-memory vers Redis avec fallback graceful | FAIT |
| **Validation renforcee** : YouTube URL regex, password strength, sanitize HTML, path traversal | FAIT |
| **CI/CD GitHub Actions** : lint, type check, tests, build, Trivy security scan, Codecov | FAIT |
| **Tests unitaires** : 105 tests (auth, schemas, classification) - 100% pass | FAIT |
| **Prometheus metrics** : http_requests, request_duration, active_requests, transcription_jobs, ai_provider | FAIT |
| **Dependabot** : mises a jour automatiques pip, npm, docker, GitHub Actions | FAIT |

---

## PHASE 4 : AMELIORATIONS IMMEDIATES — Sprint 1 [FAIT]

> Quick wins a fort impact. Infrastructure backend deja prete.

### 4.1 Streaming SSE des reponses IA [FAIT]

**Effort** : 3-5 jours | **Impact** : Haut

**Backend** :
- `POST /api/ai-assistant/stream` : endpoint SSE avec `StreamingResponse` + `text/event-stream`
- Pipeline AI Router complet (classification, selection modele, prompt dynamique)
- Format : `data: {"token": "...", "provider": "gemini"}\n\n` par chunk
- Event final : `data: {"done": true, "provider": "...", "tokens_streamed": N}\n\n`
- Gestion deconnexion client (`request.is_disconnected()`)
- Headers anti-buffering : `Cache-Control: no-cache`, `X-Accel-Buffering: no`

**Frontend** :
- Hook `useSSE.ts` reutilisable (fetch + ReadableStream + AbortController)
- Composant `StreamingText.tsx` avec curseur anime et metadata provider
- Bouton "Improve with AI" sur les transcriptions completees
- Affichage progressif token par token (effet ChatGPT)

### 4.2 Multi-source de transcription [FAIT]

**Backend** :
- `POST /api/transcription/upload` : upload multipart (MP3, WAV, MP4, M4A, OGG, WEBM, FLAC)
- Validation MIME type + extension + taille (max 500MB)
- Champs `source_type` et `original_filename` en base de donnees
- Support URLs non-YouTube via `source_type="url"` (yt-dlp multi-plateforme)
- Rate limiting upload 5 req/min

**Frontend 3 onglets** :
- **YouTube / URL** : formulaire existant, etendu aux URLs non-YouTube
- **Upload File** : zone drag & drop, preview fichier (nom/taille/type), barre de progression upload
- **Record Audio** : composant `AudioRecorder.tsx` (MediaRecorder API, timer, preview audio, auto-upload)
- Icones source dans la liste (YouTube, Upload, Link) avec tooltip

### 4.3 Chat contextuel post-transcription [FAIT]

**Effort** : 5-7 jours | **Impact** : Haut

- Models Conversation + Message (SQLModel, UUID, timestamps)
- 5 endpoints API : CRUD conversations + POST messages avec SSE streaming
- Page /chat : panneau conversations + zone de chat avec streaming
- Composants ChatPanel, ChatInput, ConversationList
- Auto-creation conversation avec contexte transcription via query param
- Bouton "Chat about this" sur transcriptions completees

---

## PHASE 5 : RENOVATIONS ARCHITECTURE [EN COURS]

> Refactoring structurel pour passer a l'echelle.

### 5.1 Event-Driven Architecture avec Celery [FAIT]

**Effort** : 1-2 semaines | **Impact** : Haut | **Priorite** : P1

Les transcriptions tournent dans `BackgroundTasks` FastAPI (liees au processus web, perdues en cas de crash).

- Migrer vers **Celery + Redis** comme broker de taches
- Jobs persistants survivant aux redemarrages
- Retry automatique avec backoff exponentiel
- Monitoring des workers via Flower dashboard
- Scaling horizontal : ajouter des workers independamment
- Le Redis est deja dans le `docker-compose.yml`

**Critere de migration** : >100 transcriptions/jour ou duree moyenne >10 minutes.

### 5.2 Plugin Registry auto-discoverable [FAIT]

**Effort** : 1-2 semaines | **Impact** : Moyen

- ModuleRegistry : scan modules/, chargement manifest.json, import dynamique via importlib
- Manifests pour transcription et conversation modules
- Validation schema manifest, gestion erreurs gracieuse (module ignore si erreur)
- Support DISABLED_MODULES env var pour desactiver des modules
- GET /api/modules : liste des modules enregistres
- Page /modules : cards modules (nom, version, status, deps)
- Ajout d'un module = creer un dossier avec manifest.json + routes.py, zero config

### 5.3 Multi-tenancy et systeme de quotas [FAIT]

**Effort** : 2-3 semaines | **Impact** : Tres haut | **Priorite** : P2

Introduire des plans (Free / Pro / Enterprise) :

- Table `plans` : nom, limites (transcriptions/mois, minutes audio, appels IA)
- Table `user_quotas` : consommation courante par utilisateur
- Middleware de verification de quota avant chaque operation couteuse
- Dashboard utilisateur avec barre de progression de consommation
- Webhook/notification quand quota atteint 80%, 100%
- Prepare la monetisation

**Plans suggeres** :

| Plan | Transcriptions/mois | Minutes audio | Appels IA | Prix |
|------|---------------------|---------------|-----------|------|
| Free | 10 | 60 | 50 | 0 EUR |
| Pro | 100 | 600 | 500 | 19 EUR/mois |
| Enterprise | Illimite | Illimite | Illimite | Sur devis |

---

## PHASE 6 : INNOVATIONS DIFFERENCIANTES [FAIT]

> Vision produit a long terme. Ce qui positionne SaaS-IA comme plateforme.

### 6.1 AI Pipeline Builder (drag and drop) [FAIT]

**Effort** : 3-4 semaines | **Impact** : Tres haut | **Priorite** : P3

Permettre a l'utilisateur de chainer des operations IA visuellement :

```
[YouTube URL] -> [Transcription] -> [Resume] -> [Traduction FR->EN] -> [Export PDF]
```

- Interface drag and drop avec React Flow
- Chaque bloc = un module IA avec entree/sortie typee
- Sauvegarde des pipelines comme templates reutilisables
- Execution asynchrone avec suivi de progression par etape
- Marketplace de templates communautaires

Positionne SaaS-IA comme une **plateforme d'orchestration IA**, pas juste un outil.

### 6.2 Analyse comparative multi-modele [FAIT]

**Effort** : 1-2 semaines | **Impact** : Haut | **Priorite** : P2

L'AI Router choisit actuellement UN modele automatiquement. Offrir un mode "Compare" :

- Envoie le meme prompt a 2-3 providers en parallele (Gemini, Claude, Groq)
- Affiche les resultats cote a cote avec temps de reponse et cout estime
- L'utilisateur vote pour la meilleure reponse
- Les votes alimentent un feedback loop pour affiner le ModelSelector
- Metriques de qualite par provider et par domaine de contenu

**Differenciateur marche** : aucun outil grand public ne propose cette fonctionnalite.

### 6.3 API publique et Marketplace [FAIT]

**Effort** : 3-4 semaines | **Impact** : Tres haut | **Priorite** : P3

- Cles API par utilisateur (gerees dans le profil)
- Documentation OpenAPI interactive avec exemples
- SDK client auto-genere (Python, TypeScript)
- **Marketplace de modules** : les developpeurs tiers publient des modules IA
- Webhooks pour integration dans des workflows externes (Zapier, Make, n8n)
- Modele economique : commission sur les modules payants

**Endpoints API publique** :
```
POST /v1/transcribe          # Transcription directe
POST /v1/process             # Traitement IA generique
GET  /v1/jobs/{id}           # Statut d'un job
POST /v1/pipelines/{id}/run  # Executer un pipeline
```

### 6.4 Knowledge Base et RAG [FAIT]

**Effort** : 3-4 semaines | **Impact** : Tres haut | **Priorite** : P3

Base de connaissances par utilisateur avec recherche semantique :

- Upload de documents (PDF, DOCX, TXT) indexes en **vector database** (pgvector dans PostgreSQL)
- Les transcriptions sont automatiquement indexees
- Les requetes IA utilisent le RAG (Retrieval-Augmented Generation) pour repondre en se basant sur les documents de l'utilisateur
- Recherche semantique cross-document
- Exemple : "Qu'est-ce qui a ete dit sur le budget dans toutes mes reunions transcrites ?"

**Stack technique** :
- pgvector (extension PostgreSQL, pas de service supplementaire)
- Embeddings via modele gratuit (Gemini embedding ou all-MiniLM-L6-v2)
- Chunking intelligent (respect des paragraphes, overlap)

### 6.5 Collaboration temps reel

**Effort** : 3-4 semaines | **Impact** : Haut | **Priorite** : P4

Transformer SaaS-IA en outil collaboratif :

- **Workspaces** partages entre utilisateurs
- Annotations collaboratives sur les transcriptions
- Commentaires et tags
- Partage de resultats par lien public (avec expiration)
- Notifications en temps reel (WebSocket deja en place)
- Roles par workspace (owner, editor, viewer)

---

## MATRICE PRIORITE / IMPACT

| # | Proposition | Effort | Impact Business | Priorite |
|---|-------------|--------|----------------|----------|
| 4.1 | Streaming SSE | Faible | Haut | **P0** |
| 4.2 | Multi-source transcription | Moyen | Haut | **P0** |
| 4.3 | Chat contextuel | Moyen | Haut | **P1** |
| 5.1 | Celery workers | Moyen | Moyen | **P1** |
| 5.2 | Plugin registry | Moyen | Moyen | **P1** |
| 6.2 | Compare multi-modele | Moyen | Haut | **P2** |
| 5.3 | Multi-tenancy / quotas | Eleve | Tres haut | **P2** |
| 6.1 | Pipeline builder | Eleve | Tres haut | **P3** |
| 6.3 | API publique / marketplace | Eleve | Tres haut | **P3** |
| 6.4 | Knowledge base RAG | Eleve | Tres haut | **P3** |
| 6.5 | Collaboration temps reel | Eleve | Haut | **P4** |

---

## SPRINTS RECOMMANDES

**Sprint 1** (immediat) : 4.1 + 4.2 -- Streaming SSE + Multi-source. Effet "wow" maximal, infrastructure backend deja prete.

**Sprint 2** : 4.3 + 5.2 -- Chat contextuel + Plugin registry. Transforme la plateforme d'un outil mono-feature en architecture extensible.

**Sprint 3** : 5.1 + 5.3 -- Celery workers + Quotas/plans. Prepare la mise en production reelle et la monetisation. **[FAIT]**

**Sprint 4** : 6.1 + 6.2 -- Pipeline builder + Compare multi-modele. Differenciateurs plateforme. **[FAIT]**

**Sprint 5** : 6.3 + 6.4 -- API publique + Knowledge base RAG. Ouvre la plateforme aux developpeurs et au RAG. **[FAIT]**

---

## STACK TECHNIQUE ACTUELLE

### Backend
- **Framework** : FastAPI 0.109 (async Python 3.11)
- **ORM** : SQLModel 0.0.14 (SQLAlchemy async + Pydantic)
- **Database** : PostgreSQL 16 (AsyncPG)
- **Cache** : Redis 7 (rate limiting, sessions)
- **Auth** : JWT access + refresh tokens, RBAC (user/admin)
- **AI Providers** : Gemini Flash, Claude Sonnet, Groq Llama 70B
- **AI Router** : Classification contenu + selection modele + prompt dynamique
- **Transcription** : AssemblyAI + yt-dlp + detection langue
- **Monitoring** : Prometheus metrics, structlog
- **Tests** : pytest + pytest-asyncio (105 tests)

### Frontend
- **Framework** : Next.js 15 (App Router) + React 18
- **UI** : Material-UI 6 + Sneat Admin Template + Tailwind CSS 3
- **State** : AuthContext (React Context) + TanStack Query 5
- **Forms** : React Hook Form + Zod
- **HTTP** : Axios avec intercepteurs (retry, refresh token auto)
- **Notifications** : Sonner

### Infrastructure
- **Containers** : Docker Compose (backend, PostgreSQL, Redis)
- **CI/CD** : GitHub Actions (lint, test, build, security scan)
- **Ports** : Backend 8004, Frontend 3002, PostgreSQL 5435, Redis 6382

---

## API ENDPOINTS ACTUELS

### Auth (`/api/auth`)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | /register | Inscription utilisateur |
| POST | /login | Connexion (retourne access + refresh token) |
| POST | /refresh | Rotation de tokens |
| GET | /me | Utilisateur courant |
| PUT | /profile | Mise a jour profil |
| PUT | /password | Changement mot de passe |

### Transcription (`/api/transcription`)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | / | Creer une transcription |
| GET | / | Lister (pagine, filtre par statut) |
| GET | /stats | Statistiques utilisateur |
| GET | /{id} | Detail d'une transcription |
| DELETE | /{id} | Supprimer |
| WS | /debug/{id} | WebSocket debug (dev/admin) |
| GET | /debug/{id}/audio | Telecharger audio cache (dev/admin) |
| POST | /debug/transcribe/{id} | Transcription sync (dev/admin) |

### AI Assistant (`/api/ai-assistant`)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | /providers | Liste des providers IA |
| POST | /process-text | Traitement IA (avec AI Router) |
| GET | /health | Sante du module |
| POST | /classify-content | Classification de contenu |
| POST | /classify-batch | Classification batch |

### System
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | / | Info application |
| GET | /health | Health check |
| GET | /metrics | Prometheus (dev ou token) |

### Billing (`/api/billing`)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | /plans | Plans disponibles |
| GET | /quota | Quota et usage de l'utilisateur courant |

### Compare (`/api/compare`)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | /run | Comparaison multi-modele parallele |
| POST | /{id}/vote | Vote qualite provider |
| GET | /stats | Statistiques qualite par provider |

### Pipelines (`/api/pipelines`)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | / | Creer un pipeline |
| GET | / | Lister les pipelines |
| GET | /{id} | Detail d'un pipeline |
| PUT | /{id} | Modifier un pipeline |
| DELETE | /{id} | Supprimer un pipeline |
| POST | /{id}/execute | Executer un pipeline |
| GET | /{id}/executions | Historique des executions |
| GET | /executions/{id} | Detail d'une execution |

### Knowledge Base (`/api/knowledge`)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | /upload | Upload et indexer un document |
| GET | /documents | Lister les documents |
| DELETE | /documents/{id} | Supprimer un document |
| POST | /search | Recherche semantique |
| POST | /ask | Question RAG avec IA |

### API Keys (`/api/keys`)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | / | Creer une cle API |
| GET | / | Lister les cles |
| DELETE | /{id} | Revoquer une cle |

### Public API (`/v1`)
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | /transcribe | Soumettre une transcription |
| POST | /process | Traitement IA |
| GET | /jobs/{id} | Statut d'un job |

---

## PAGES FRONTEND

| Route | Description | Statut |
|-------|-------------|--------|
| /login | Connexion | FAIT |
| /register | Inscription | FAIT |
| /dashboard | Tableau de bord avec stats reelles | FAIT |
| /transcription | Gestion transcriptions (create, list, export) | FAIT |
| /transcription/debug | Interface debug temps reel (dev/admin) | FAIT |
| /profile | Profil utilisateur et changement mot de passe | FAIT |
| /billing | Plan, usage quotas et plans disponibles | FAIT |
| /compare | Comparaison multi-modele IA | FAIT |
| /pipelines | Pipeline builder IA | FAIT |
| /knowledge | Knowledge base: upload, recherche, RAG | FAIT |
| /api-docs | Gestion cles API + documentation publique | FAIT |

---

## CHANGELOG

### v2.5.0 (2026-03-22)
- Sprint 5 : Knowledge Base RAG (upload documents, chunking, TF-IDF search, RAG queries)
- Sprint 5 : API publique v1 (cles API SHA-256, endpoints /v1/transcribe, /v1/process, /v1/jobs)
- 14 nouveaux fichiers backend, 9 fichiers frontend, 28 nouveaux tests
- Documentation technique : docs/SPRINT5_KNOWLEDGE_API.md

### v2.4.0 (2026-03-22)
- Sprint 4 : Compare multi-modele (execution parallele, voting, stats)
- Sprint 4 : AI Pipeline Builder (CRUD, execution sequentielle, 4 types de steps)
- 12 nouveaux fichiers backend, 8 fichiers frontend, 22 nouveaux tests
- Documentation technique : docs/SPRINT4_COMPARE_PIPELINES.md

### v2.3.0 (2026-03-22)
- Sprint 3 : Celery workers (taches persistantes, retry backoff, Flower monitoring)
- Sprint 3 : Multi-tenancy et quotas (plans Free/Pro/Enterprise, verification automatique)
- 7 nouveaux fichiers backend, 5 fichiers frontend, 24 nouveaux tests
- Documentation technique : docs/SPRINT3_CELERY_BILLING.md

### v2.0.0 (2026-03-22)
- Roadmap reecrite integralement pour refleter l'etat reel du projet
- Phases 0-3 completees et documentees (securite, stabilisation, features core, production-ready)
- Ajout Phase 4 : ameliorations immediates (SSE, multi-source, chat contextuel)
- Ajout Phase 5 : renovations architecture (Celery, plugin registry, multi-tenancy)
- Ajout Phase 6 : innovations differenciantes (pipeline builder, compare, API publique, RAG, collaboration)
- Matrice priorite/impact et sprints recommandes
- Documentation complete de la stack technique et des endpoints

### v1.1.0 (2025-11-14)
- Ajout Phase 0 : Module Transcription YouTube
- Architecture MVP simplifiee V2 validee

### v1.0.0 (2025-11-14)
- Version initiale de la roadmap
- Phases 1-4 definies
