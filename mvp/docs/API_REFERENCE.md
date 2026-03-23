# Reference API - SaaS-IA

Base URL : `http://localhost:8004` (dev) ou `https://api.votre-domaine.com` (prod)

Documentation interactive : `/docs` (Swagger) ou `/redoc` (ReDoc)

## Authentification

### JWT Bearer Token

La plupart des endpoints requierent un token JWT dans le header :
```
Authorization: Bearer {access_token}
```

### API Key (Public API v1)

Les endpoints `/v1/*` acceptent une cle API :
```
X-API-Key: sk-{votre_cle}
```

---

## Auth (`/api/auth`)

### POST /api/auth/register
Inscription d'un nouvel utilisateur.

**Body** :
```json
{"email": "user@example.com", "password": "SecureP@ss123", "full_name": "John Doe"}
```

**Response** `201` : `{id, email, full_name, role, is_active, created_at}`

### POST /api/auth/login
Connexion (OAuth2 form data).

**Body** : `username=email&password=pass` (form-urlencoded)

**Response** `200` :
```json
{"access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 1800}
```

### POST /api/auth/refresh
Rotation de tokens.

**Body** : `{"refresh_token": "..."}`

**Response** `200` : Nouvelle paire access + refresh

### GET /api/auth/me
Utilisateur courant. **Auth requise.**

### PUT /api/auth/profile
Modifier le profil. **Body** : `{"full_name": "New Name"}`

### PUT /api/auth/password
Changer le mot de passe. **Body** : `{"current_password": "...", "new_password": "..."}`

---

## Transcription (`/api/transcription`)

### POST /api/transcription/
Creer une transcription. **Auth requise.** Rate: 10/min.

**Body** :
```json
{"video_url": "https://youtube.com/watch?v=...", "language": "auto", "source_type": "youtube"}
```

`source_type` : `youtube` | `url` | `upload`

**Response** `201` : `{id, status: "pending", video_url, ...}`

### POST /api/transcription/upload
Upload d'un fichier audio/video. **Auth requise.** Rate: 5/min.

**Body** : `multipart/form-data` avec `file` + `language` (optionnel)

Formats : MP3, WAV, MP4, M4A, OGG, WEBM, FLAC (max 500 MB)

### GET /api/transcription/
Lister les transcriptions (pagine). Rate: 20/min.

**Params** : `skip`, `limit`, `status` (pending/processing/completed/failed)

### GET /api/transcription/stats
Statistiques utilisateur. Rate: 20/min.

### GET /api/transcription/{id}
Detail d'une transcription. Rate: 30/min.

### DELETE /api/transcription/{id}
Supprimer. Rate: 10/min. **Response** `204`.

---

## Conversations (`/api/conversations`)

### POST /api/conversations/
Creer une conversation. Rate: 10/min.

**Body** : `{"transcription_id": "uuid"}` (optionnel - injecte le texte comme contexte)

### GET /api/conversations/
Lister les conversations (pagine). Rate: 30/min.

### GET /api/conversations/{id}
Detail + messages. Rate: 30/min.

### DELETE /api/conversations/{id}
Supprimer. Rate: 10/min. **Response** `204`.

### POST /api/conversations/{id}/messages
Envoyer un message et recevoir la reponse IA en SSE. Rate: 20/min.

**Body** : `{"content": "Votre message"}`

**Response** : `text/event-stream`
```
data: {"type": "token", "token": "mot "}
data: {"type": "token", "token": "par "}
data: {"type": "token", "token": "mot"}
data: {"type": "done", "provider": "gemini", "tokens_streamed": 42}
```

---

## Billing (`/api/billing`)

### GET /api/billing/plans
Liste des plans disponibles (pas d'auth requise). Rate: 30/min.

**Response** `200` :
```json
[
  {"id": "...", "name": "free", "display_name": "Free", "max_transcriptions_month": 10, "price_cents": 0},
  {"id": "...", "name": "pro", "display_name": "Pro", "max_transcriptions_month": 100, "price_cents": 1900}
]
```

### GET /api/billing/quota
Quota et consommation de l'utilisateur courant. **Auth requise.** Rate: 30/min.

**Response** `200` :
```json
{
  "plan": {"name": "free", "display_name": "Free", "...": "..."},
  "transcriptions_used": 3, "transcriptions_limit": 10,
  "audio_minutes_used": 15, "audio_minutes_limit": 60,
  "ai_calls_used": 8, "ai_calls_limit": 50,
  "period_start": "2026-03-01", "period_end": "2026-03-31",
  "usage_percent": 30.0
}
```

### POST /api/billing/checkout
Creer une session Stripe Checkout. **Auth requise.** Rate: 5/min.

**Body** : `{"plan_name": "pro"}`

**Response** `200` : `{"checkout_url": "https://checkout.stripe.com/...", "session_id": "cs_..."}`

### POST /api/billing/portal
Ouvrir le portail de gestion Stripe. **Auth requise.** Rate: 5/min.

**Response** `200` : `{"portal_url": "https://billing.stripe.com/..."}`

### POST /api/billing/webhook
Webhook Stripe (pas d'auth JWT, verification par signature).

---

## Compare (`/api/compare`)

### POST /api/compare/run
Comparaison multi-modele parallele. **Auth requise + quota IA.** Rate: 5/min.

**Body** :
```json
{"prompt": "Explain quantum computing", "providers": ["gemini", "claude", "groq"]}
```

**Response** `200` :
```json
{
  "id": "uuid",
  "prompt": "...",
  "results": [
    {"provider": "gemini", "model": "gemini-2.5-flash", "response": "...", "response_time_ms": 1200, "error": null},
    {"provider": "claude", "model": "claude-sonnet", "response": "...", "response_time_ms": 2100, "error": null}
  ]
}
```

### POST /api/compare/{id}/vote
Voter pour un provider. **Auth requise.** Rate: 10/min.

**Body** : `{"provider_name": "gemini", "quality_score": 5}`

### GET /api/compare/stats
Statistiques qualite par provider. Rate: 20/min.

---

## Pipelines (`/api/pipelines`)

### POST /api/pipelines/
Creer un pipeline. **Auth requise.** Rate: 10/min.

**Body** :
```json
{
  "name": "YouTube to Summary",
  "description": "Transcribe and summarize",
  "steps": [
    {"id": "s1", "type": "transcription", "config": {"language": "auto"}, "position": 0},
    {"id": "s2", "type": "summarize", "config": {}, "position": 1}
  ]
}
```

Types de steps : `transcription`, `summarize`, `translate`, `export`

### GET /api/pipelines/
Lister. Rate: 20/min.

### GET /api/pipelines/{id}
Detail. Rate: 30/min.

### PUT /api/pipelines/{id}
Modifier. Rate: 10/min.

### DELETE /api/pipelines/{id}
Supprimer. Rate: 10/min. **Response** `204`.

### POST /api/pipelines/{id}/execute
Executer un pipeline. Rate: 3/min.

**Response** `200` : `{id, status, current_step, total_steps, results: [...]}`

### GET /api/pipelines/{id}/executions
Historique des executions. Rate: 20/min.

### GET /api/pipelines/executions/{id}
Detail d'une execution. Rate: 30/min.

---

## Knowledge Base (`/api/knowledge`)

### POST /api/knowledge/upload
Upload et indexer un document. **Auth requise.** Rate: 5/min.

**Body** : `multipart/form-data` avec `file` (TXT, MD, CSV, max 10 MB)

**Response** `201` : `{id, filename, total_chunks, status: "indexed"}`

### GET /api/knowledge/documents
Lister les documents. Rate: 20/min.

### DELETE /api/knowledge/documents/{id}
Supprimer. Rate: 10/min. **Response** `204`.

### POST /api/knowledge/search
Recherche semantique. **Auth requise.** Rate: 20/min.

**Body** : `{"query": "machine learning", "limit": 5}`

**Response** : `{query, results: [{chunk_id, document_id, filename, content, score, chunk_index}], total}`

### POST /api/knowledge/ask
Question RAG. **Auth requise + quota IA.** Rate: 10/min.

**Body** : `{"question": "What was discussed about the budget?"}`

**Response** : `{question, answer, sources: [...], provider}`

---

## API Keys (`/api/keys`)

### POST /api/keys/
Creer une cle API. **Auth requise.** Rate: 5/min.

**Body** : `{"name": "Production Key", "permissions": ["read", "write"]}`

**Response** `201` :
```json
{"id": "...", "name": "Production Key", "key": "sk-abc123...", "key_prefix": "sk-abc12", "message": "Save this key now. It will not be shown again."}
```

### GET /api/keys/
Lister les cles (sans le secret). Rate: 20/min.

### DELETE /api/keys/{id}
Revoquer une cle. Rate: 10/min. **Response** `204`.

---

## Public API v1 (`/v1`)

Authentification via header `X-API-Key`.

### POST /v1/transcribe
Soumettre une transcription. Rate: 10/min.

**Body** : `{"video_url": "https://...", "language": "auto"}`

**Response** : `{job_id, status, message}`

### POST /v1/process
Traitement IA. Rate: 10/min.

**Body** : `{"text": "Your text", "task": "summarize", "provider": "gemini"}`

**Response** : `{result, provider, model}`

### GET /v1/jobs/{job_id}
Statut d'un job. Rate: 30/min.

**Response** : `{job_id, status, text, confidence, duration_seconds, error}`

---

## Workspaces (`/api/workspaces`)

### POST /api/workspaces/
Creer un workspace. **Auth requise.** Rate: 10/min.

**Body** : `{"name": "Mon Equipe", "description": "Workspace d'equipe"}`

### GET /api/workspaces/
Lister les workspaces (du user). Rate: 20/min.

### GET /api/workspaces/{id}
Detail. Rate: 30/min.

### PUT /api/workspaces/{id}
Modifier (owner uniquement). Rate: 10/min.

### DELETE /api/workspaces/{id}
Supprimer (owner uniquement). Rate: 5/min. **Response** `204`.

### POST /api/workspaces/{id}/invite
Inviter un membre. Owner uniquement. Rate: 10/min.

**Body** : `{"email": "user@example.com", "role": "editor"}`

Roles : `owner`, `editor`, `viewer`

### GET /api/workspaces/{id}/members
Lister les membres. Rate: 20/min.

### DELETE /api/workspaces/{id}/members/{user_id}
Retirer un membre. Owner uniquement. Rate: 10/min.

### POST /api/workspaces/{id}/share
Partager un item. Rate: 10/min.

**Body** : `{"item_type": "transcription", "item_id": "uuid"}`

### GET /api/workspaces/{id}/items
Lister les items partages. Rate: 20/min.

### POST /api/workspaces/items/{item_id}/comments
Ajouter un commentaire. Rate: 20/min.

**Body** : `{"content": "Great transcription!"}`

### GET /api/workspaces/items/{item_id}/comments
Lister les commentaires. Rate: 30/min.

---

## Systeme

### GET /
Info application.

### GET /health
Health check. Rate: 100/min.

### GET /metrics
Metriques Prometheus (dev ou token `X-Metrics-Token`).

### GET /api/modules
Liste des modules enregistres.

---

## Codes d'erreur

| Code | Signification |
|------|--------------|
| 400 | Requete invalide (validation Pydantic) |
| 401 | Non authentifie (token manquant/invalide) |
| 402 | Quota depasse (upgrade plan requis) |
| 403 | Acces refuse (mauvais role ou ownership) |
| 404 | Ressource non trouvee |
| 413 | Fichier trop volumineux |
| 429 | Rate limit depasse (retry apres 60s) |
| 500 | Erreur interne |

Format erreur standard :
```json
{"detail": "Message d'erreur descriptif"}
```
