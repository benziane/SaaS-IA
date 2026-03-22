# Sprint 4 : Compare Multi-Modele + Pipeline Builder

**Date** : 2026-03-22
**Version** : MVP 2.4.0
**Statut** : Termine

---

## 1. Analyse Comparative Multi-Modele

### Architecture

```
Frontend (/compare)              Backend (FastAPI)
      |                                |
      |-- POST /compare/run ---------> |
      |   {prompt, providers}          |-- asyncio.gather()
      |                                |   -> GeminiProvider.complete()
      |                                |   -> ClaudeProvider.complete()
      |                                |   -> GroqProvider.complete()
      |<-- {results: [...]} ---------- |-- save ComparisonResult
      |                                |
      |-- POST /compare/{id}/vote ---> |-- save ComparisonVote
      |<-- 200 OK ------------------- |
      |                                |
      |-- GET /compare/stats --------> |-- aggregate votes
      |<-- [{provider, avg_score}] --- |
```

### Backend

**Modeles** (`app/models/compare.py`) :

```
comparison_results
  id                UUID PK
  user_id           UUID FK -> users.id
  prompt            TEXT (max 10000)
  providers_used    VARCHAR(500) (comma-separated)
  results_json      TEXT (JSON array of results)
  created_at        DATETIME

comparison_votes
  id                UUID PK
  comparison_id     UUID FK -> comparison_results.id
  user_id           UUID FK -> users.id
  provider_name     VARCHAR(50)
  quality_score     INT (1-5)
  created_at        DATETIME
```

**Service** (`app/modules/compare/service.py`) :
- `run_comparison()` : Execute le prompt en parallele via `asyncio.gather()` sur tous les providers selectionnes
- `_call_provider()` : Appel individuel avec mesure du temps de reponse (ms)
- `record_vote()` : Enregistre un vote qualite par provider
- `get_stats()` : Statistiques aggregees par provider (avg score, total votes)

**Endpoints** :

| Methode | Endpoint | Description | Auth | Rate Limit |
|---------|----------|-------------|------|------------|
| POST | /api/compare/run | Lancer une comparaison multi-modele | Oui (+ quota AI) | 5/min |
| POST | /api/compare/{id}/vote | Voter pour le meilleur provider | Oui | 10/min |
| GET | /api/compare/stats | Statistiques qualite par provider | Oui | 20/min |

**AIAssistantService.process_text_with_provider()** :
Nouvelle methode statique permettant d'appeler un provider specifique directement (Gemini, Claude, ou Groq). Utilisee par le service Compare et le Pipeline Builder.

### Frontend

**Page** : `/compare` (`src/app/(dashboard)/compare/page.tsx`)
- Champ texte pour le prompt
- Checkboxes pour selectionner les providers (Gemini Flash, Claude Sonnet, Groq Llama 70B)
- Resultats cote a cote en colonnes (Grid responsive)
- Chip temps de reponse (vert < 2s, orange < 5s, rouge > 5s)
- Rating 5 etoiles pour voter
- Section statistiques par provider

---

## 2. AI Pipeline Builder

### Architecture

```
Frontend (/pipelines)            Backend (FastAPI)
      |                                |
      |-- POST /pipelines -----------> | create Pipeline
      |<-- {id, name, steps} --------- |
      |                                |
      |-- POST /pipelines/{id}/execute |
      |                                |-- step 1: transcription
      |                                |-- step 2: summarize (AI)
      |                                |-- step 3: translate (AI)
      |                                |-- step 4: export
      |<-- {execution, results} ------ |
```

### Backend

**Modeles** (`app/models/pipeline.py`) :

```
pipelines
  id            UUID PK
  user_id       UUID FK -> users.id
  name          VARCHAR(200)
  description   VARCHAR(1000)
  steps_json    TEXT (JSON array)
  status        ENUM (draft, active, archived)
  is_template   BOOL
  created_at    DATETIME
  updated_at    DATETIME

pipeline_executions
  id            UUID PK
  pipeline_id   UUID FK -> pipelines.id
  user_id       UUID FK -> users.id
  status        ENUM (pending, running, completed, failed)
  current_step  INT
  total_steps   INT
  results_json  TEXT (JSON array)
  error         VARCHAR(2000)
  started_at    DATETIME
  completed_at  DATETIME
  created_at    DATETIME
```

**Types de steps supportes** :

| Type | Description | Config |
|------|-------------|--------|
| transcription | Transcription audio/video | language, source_type |
| summarize | Resume via IA | provider, max_length |
| translate | Traduction via IA | target_language, provider |
| export | Export du resultat | format (txt, json) |

**Service** (`app/modules/pipelines/service.py`) :
- CRUD complet : `create_pipeline`, `get_pipeline`, `list_pipelines`, `update_pipeline`, `delete_pipeline`
- `execute_pipeline()` : Execute les steps sequentiellement, chaque step recoit l'output du precedent
- `_execute_step()` : Dispatch vers le handler du type de step
- `_step_summarize()` / `_step_translate()` : Utilisent `AIAssistantService.process_text_with_provider()`

**Endpoints** :

| Methode | Endpoint | Description | Auth | Rate Limit |
|---------|----------|-------------|------|------------|
| POST | /api/pipelines/ | Creer un pipeline | Oui | 10/min |
| GET | /api/pipelines/ | Lister les pipelines | Oui | 20/min |
| GET | /api/pipelines/{id} | Detail d'un pipeline | Oui | 30/min |
| PUT | /api/pipelines/{id} | Modifier un pipeline | Oui | 10/min |
| DELETE | /api/pipelines/{id} | Supprimer un pipeline | Oui | 10/min |
| POST | /api/pipelines/{id}/execute | Executer un pipeline | Oui | 3/min |
| GET | /api/pipelines/{id}/executions | Historique executions | Oui | 20/min |
| GET | /api/pipelines/executions/{id} | Detail d'une execution | Oui | 30/min |

### Frontend

**Page** : `/pipelines` (`src/app/(dashboard)/pipelines/page.tsx`)
- Grille de cartes avec nom, description, steps chips, status
- Boutons Execute / Delete par pipeline
- Dialog de creation (nom + description, steps par defaut)
- Alertes pour resultats d'execution
- Skeleton loading et empty state

---

## 3. Nouveaux endpoints API

| Methode | Endpoint | Description | Auth | Rate Limit |
|---------|----------|-------------|------|------------|
| POST | /api/compare/run | Comparaison multi-modele | Oui | 5/min |
| POST | /api/compare/{id}/vote | Vote qualite | Oui | 10/min |
| GET | /api/compare/stats | Stats providers | Oui | 20/min |
| POST | /api/pipelines/ | Creer pipeline | Oui | 10/min |
| GET | /api/pipelines/ | Lister pipelines | Oui | 20/min |
| GET | /api/pipelines/{id} | Detail pipeline | Oui | 30/min |
| PUT | /api/pipelines/{id} | Modifier pipeline | Oui | 10/min |
| DELETE | /api/pipelines/{id} | Supprimer pipeline | Oui | 10/min |
| POST | /api/pipelines/{id}/execute | Executer pipeline | Oui | 3/min |
| GET | /api/pipelines/{id}/executions | Historique | Oui | 20/min |
| GET | /api/pipelines/executions/{id} | Detail execution | Oui | 30/min |

---

## 4. Migration base de donnees

```sql
CREATE TABLE comparison_results (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  prompt TEXT NOT NULL,
  providers_used VARCHAR(500),
  results_json TEXT DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE comparison_votes (
  id UUID PRIMARY KEY,
  comparison_id UUID REFERENCES comparison_results(id),
  user_id UUID REFERENCES users(id),
  provider_name VARCHAR(50) NOT NULL,
  quality_score INT NOT NULL CHECK (quality_score BETWEEN 1 AND 5),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pipelines (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  name VARCHAR(200) NOT NULL,
  description VARCHAR(1000),
  steps_json TEXT DEFAULT '[]',
  status VARCHAR(20) DEFAULT 'draft',
  is_template BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pipeline_executions (
  id UUID PRIMARY KEY,
  pipeline_id UUID REFERENCES pipelines(id),
  user_id UUID REFERENCES users(id),
  status VARCHAR(20) DEFAULT 'pending',
  current_step INT DEFAULT 0,
  total_steps INT DEFAULT 0,
  results_json TEXT DEFAULT '[]',
  error VARCHAR(2000),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_comparison_results_user ON comparison_results(user_id);
CREATE INDEX idx_comparison_votes_comparison ON comparison_votes(comparison_id);
CREATE INDEX idx_pipelines_user ON pipelines(user_id);
CREATE INDEX idx_pipeline_executions_pipeline ON pipeline_executions(pipeline_id);
```

---

## 5. Nouvelles pages frontend

| Route | Description |
|-------|-------------|
| /compare | Comparaison multi-modele IA cote a cote |
| /pipelines | Pipeline builder IA avec creation et execution |

**Navigation mise a jour** :
```
Dashboard
AI Modules
  Transcription
  Chat IA
  Compare           <-- NOUVEAU
  Pipelines         <-- NOUVEAU
Platform
  Modules
Account
  Profile
  Billing
```
