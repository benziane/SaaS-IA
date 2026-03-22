# Sprint 5 : Knowledge Base RAG + API Publique

**Date** : 2026-03-22
**Version** : MVP 2.5.0
**Statut** : Termine

---

## 1. Knowledge Base et RAG

### Architecture

```
Frontend (/knowledge)           Backend (FastAPI)
      |                               |
      |-- POST /knowledge/upload ---->| _extract_text() + chunk_text()
      |   (multipart TXT/MD/CSV)     |-- Store Document + DocumentChunks
      |<-- {document} ---------------|
      |                               |
      |-- POST /knowledge/search ---->| TF-IDF cosine similarity
      |   {query}                     |-- Score all user chunks
      |<-- {results: [...]} ---------|
      |                               |
      |-- POST /knowledge/ask ------->| Search + Build context
      |   {question}                  |-- AIAssistantService.process_text_with_provider()
      |<-- {answer, sources} --------|
```

### Backend

**Modeles** (`app/models/knowledge.py`) :

```
documents
  id            UUID PK
  user_id       UUID FK -> users.id
  filename      VARCHAR(500)
  content_type  VARCHAR(100)
  total_chunks  INT
  status        ENUM (pending, processing, indexed, failed)
  error         VARCHAR(1000)
  created_at    DATETIME
  updated_at    DATETIME

document_chunks
  id            UUID PK
  document_id   UUID FK -> documents.id
  user_id       UUID FK -> users.id
  content       TEXT
  chunk_index   INT
  metadata_json TEXT (JSON)
  created_at    DATETIME
```

**Service** (`app/modules/knowledge/service.py`) :
- `_chunk_text()` : Decoupe par paragraphes, 500 chars, 50 chars overlap
- `_tokenize()` : Tokenisation simple (lowercase, alphanum)
- `_compute_tf()` : Term Frequency
- `_cosine_similarity()` : Similarite cosinus entre vecteurs TF
- `upload_document()` : Upload, chunk, indexer
- `search()` : Recherche TF-IDF sur tous les chunks de l'utilisateur
- `rag_query()` : Recherche + construction contexte + appel IA

**Endpoints** :

| Methode | Endpoint | Description | Auth | Rate Limit |
|---------|----------|-------------|------|------------|
| POST | /api/knowledge/upload | Upload document (TXT, MD, CSV) | Oui | 5/min |
| GET | /api/knowledge/documents | Lister les documents | Oui | 20/min |
| DELETE | /api/knowledge/documents/{id} | Supprimer document + chunks | Oui | 10/min |
| POST | /api/knowledge/search | Recherche semantique | Oui | 20/min |
| POST | /api/knowledge/ask | Question RAG (+ quota IA) | Oui | 10/min |

### Frontend

**Page** : `/knowledge` (`src/app/(dashboard)/knowledge/page.tsx`)
- Upload de fichiers (TXT, MD, CSV) avec bouton et support drag
- Liste des documents avec status chips et bouton delete
- Barre de recherche semantique avec resultats
- Interface question/reponse RAG avec sources citees

---

## 2. API Publique et Cles API

### Architecture

```
Client externe                  Backend (FastAPI)
      |                               |
      |-- POST /v1/transcribe ------->| verify_api_key (X-API-Key header)
      |   X-API-Key: sk-...          |-- Permission check
      |<-- {job_id, status} ---------|
      |                               |
      |-- GET /v1/jobs/{id} --------->| verify_api_key
      |<-- {status, text, ...} ------|

Dashboard (/api-docs)           Backend
      |                               |
      |-- POST /api/keys ------------>| APIKeyService.create_key()
      |<-- {key: sk-..., prefix} ----|  (plain text, once only)
      |                               |
      |-- GET /api/keys ------------->| list_keys() (no secrets)
      |-- DELETE /api/keys/{id} ----->| revoke_key()
```

### Backend

**Modele** (`app/models/api_key.py`) :

```
api_keys
  id                UUID PK
  user_id           UUID FK -> users.id
  name              VARCHAR(100)
  key_hash          VARCHAR(255) (SHA-256)
  key_prefix        VARCHAR(8)
  permissions_json  TEXT (JSON array)
  rate_limit_per_day INT (default 1000)
  is_active         BOOL
  last_used_at      DATETIME
  created_at        DATETIME
  expires_at        DATETIME
```

**Service** (`app/modules/api_keys/service.py`) :
- `generate_key()` : Genere `sk-{secrets.token_urlsafe(32)}`
- `hash_key()` : SHA-256 hash pour stockage
- `create_key()` : Cree la cle, retourne en clair UNE SEULE FOIS
- `verify_key()` : Verifie le hash, met a jour last_used_at
- `list_keys()` / `revoke_key()` : Gestion

**Endpoints de gestion** :

| Methode | Endpoint | Description | Auth | Rate Limit |
|---------|----------|-------------|------|------------|
| POST | /api/keys | Creer une cle API | JWT | 5/min |
| GET | /api/keys | Lister les cles (sans secret) | JWT | 20/min |
| DELETE | /api/keys/{id} | Revoquer une cle | JWT | 10/min |

**Endpoints API publique v1** :

| Methode | Endpoint | Description | Auth | Rate Limit |
|---------|----------|-------------|------|------------|
| POST | /v1/transcribe | Soumettre transcription | API Key | 10/min |
| POST | /v1/process | Traitement IA | API Key | 10/min |
| GET | /v1/jobs/{id} | Statut d'un job | API Key | 30/min |

### Frontend

**Page** : `/api-docs` (`src/app/(dashboard)/api-docs/page.tsx`)
- Gestion des cles API (creation, listing, revocation)
- Affichage de la cle en clair une seule fois avec bouton copier
- Documentation interactive avec exemples curl
- Authentification via header X-API-Key

---

## 3. Nouveaux endpoints API

| Methode | Endpoint | Description | Auth |
|---------|----------|-------------|------|
| POST | /api/knowledge/upload | Upload document | JWT |
| GET | /api/knowledge/documents | Lister documents | JWT |
| DELETE | /api/knowledge/documents/{id} | Supprimer document | JWT |
| POST | /api/knowledge/search | Recherche semantique | JWT |
| POST | /api/knowledge/ask | Question RAG | JWT |
| POST | /api/keys | Creer cle API | JWT |
| GET | /api/keys | Lister cles | JWT |
| DELETE | /api/keys/{id} | Revoquer cle | JWT |
| POST | /v1/transcribe | Transcription publique | API Key |
| POST | /v1/process | Traitement IA publique | API Key |
| GET | /v1/jobs/{id} | Statut job publique | API Key |

---

## 4. Nouvelles pages frontend

| Route | Description |
|-------|-------------|
| /knowledge | Knowledge base: upload, recherche, RAG |
| /api-docs | Gestion cles API + documentation publique |

**Navigation mise a jour** :
```
Dashboard
AI Modules
  Transcription
  Chat IA
  Compare
  Pipelines
  Knowledge Base     <-- NOUVEAU
Platform
  Modules
  API & Keys         <-- NOUVEAU
Account
  Profile
  Billing
```
