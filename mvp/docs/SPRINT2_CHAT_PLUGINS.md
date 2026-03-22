# Sprint 2 : Chat Contextuel IA + Plugin Registry

**Date** : 2026-03-22
**Version** : MVP 2.2.0
**Statut** : Termine

---

## 1. Chat Contextuel Post-Transcription

### Vision

Permettre a l'utilisateur de dialoguer avec l'IA en contexte de sa transcription.
Le texte transcrit devient le contexte systeme de la conversation : "Resume en 3 points",
"Traduis en anglais", "Quels sont les arguments principaux ?"

### Architecture

```
Frontend (/chat)                    Backend
      |                                |
      |-- POST /conversations -------->| (create, inject transcription as system msg)
      |<-- {id, title, ...} ----------|
      |                                |
      |-- POST /conversations/{id}/messages -->|
      |   {content: "Resume..."}       |
      |                                |-- Load conversation history
      |                                |-- AIAssistantService.stream_text()
      |<-- SSE: {"token":"..."} ------|  (streaming)
      |<-- SSE: {"done":true} --------|
      |                                |-- Save assistant message to DB
      |                                |
      |-- GET /conversations/{id} ---->| (reload full conversation)
      |<-- {messages: [...]} ----------|
```

### Backend

**Modeles** (`app/models/conversation.py`) :

```
conversations
  id              UUID PK
  user_id         UUID FK -> users.id
  transcription_id UUID FK -> transcriptions.id (nullable)
  title           VARCHAR (auto-genere depuis 1er message)
  created_at      DATETIME
  updated_at      DATETIME

messages
  id              UUID PK
  conversation_id UUID FK -> conversations.id
  role            VARCHAR (user, assistant, system)
  content         TEXT
  provider        VARCHAR (nullable)
  tokens_used     INT (nullable)
  created_at      DATETIME
```

**Service** (`app/modules/conversation/service.py`) :
- `create_conversation(user_id, transcription_id?)` : cree la conversation, injecte le texte transcrit comme message systeme si transcription_id fourni
- `add_message(conversation_id, role, content, provider?, tokens_used?)` : persiste un message, auto-genere le titre depuis le 1er message utilisateur
- `get_conversation(conversation_id, user_id)` : recupere avec tous les messages
- `list_conversations(user_id, skip, limit)` : liste paginee avec message_count
- `delete_conversation(conversation_id, user_id)` : suppression en cascade
- `get_conversation_history(conversation_id)` : format `[{role, content}]` pour les providers IA

**Endpoints** (`app/modules/conversation/routes.py`) :

| Methode | Endpoint | Description | Rate Limit |
|---------|----------|-------------|------------|
| POST | /api/conversations | Creer conversation | 10/min |
| GET | /api/conversations | Lister conversations | 30/min |
| GET | /api/conversations/{id} | Detail + messages | 30/min |
| DELETE | /api/conversations/{id} | Supprimer | 10/min |
| POST | /api/conversations/{id}/messages | Envoyer message (SSE) | 20/min |

**Flux du message SSE** :
1. Sauvegarde message utilisateur en base
2. Charge l'historique complet de la conversation
3. Classification du contenu via AI Router
4. Selection du provider optimal
5. Streaming de la reponse via SSE
6. Detection deconnexion client a chaque chunk
7. Sauvegarde message assistant en base apres completion

### Frontend

**Page** : `/chat` (`src/app/(dashboard)/chat/page.tsx`)
- Layout deux panneaux : sidebar conversations (300px) + zone de chat (flex)
- Parametre URL `?transcription_id=` pour auto-creation avec contexte
- Rendu optimiste des messages utilisateur pendant l'attente serveur

**Composants** :

| Composant | Fichier | Role |
|-----------|---------|------|
| ChatPanel | `components/chat/ChatPanel.tsx` | Zone messages avec scroll auto |
| ChatInput | `components/chat/ChatInput.tsx` | Input avec Enter/Shift+Enter, bouton stop |
| ConversationList | `components/chat/ConversationList.tsx` | Sidebar avec liste, delete, skeleton |

**Style des messages** :
- User : bulle droite, couleur primaire, bords arrondis
- Assistant : bulle gauche, fond gris, chip provider
- System : Alert MUI subtile, style info

**API + Hooks** (`features/conversation/`) :
- `api.ts` : CRUD conversations via apiClient
- `useConversations()` : liste avec polling 10s
- `useConversation(id)` : detail avec messages
- `useCreateConversation()` / `useDeleteConversation()` : mutations

**Integration page transcription** :
- Bouton "Chat about this" sur les transcriptions completees
- Navigue vers `/chat?transcription_id={id}`

---

## 2. Plugin Registry Auto-Discoverable

### Vision

Remplacer l'inclusion manuelle des routers dans `main.py` par un systeme de decouverte
automatique des modules. Chaque module declare un `manifest.json` et le registry
scanne, valide et monte les routes au demarrage.

### Architecture

```
app/modules/
  __init__.py              <-- ModuleRegistry
  transcription/
    manifest.json          <-- {name, version, prefix, enabled, ...}
    routes.py              <-- router FastAPI
    service.py
  conversation/
    manifest.json
    routes.py
    service.py
  future_module/           <-- Ajouter un module = creer un dossier
    manifest.json
    routes.py
```

### Backend

**ModuleRegistry** (`app/modules/__init__.py`) :

```python
class ModuleRegistry:
    discover_modules(app: FastAPI) -> list[dict]
    get_registered_modules() -> list[dict]
```

**Flux de decouverte** :
1. Scanne les sous-dossiers de `app/modules/`
2. Cherche `manifest.json` dans chaque dossier
3. Valide le schema du manifest (name, version, description, prefix, tags, enabled, dependencies)
4. Verifie que le module n'est pas dans `DISABLED_MODULES` (env var)
5. Si `enabled: true`, importe `routes.py` via `importlib`
6. Inclut le router avec prefix et tags du manifest
7. Log le resultat (succes ou erreur)

**Schema manifest** :
```json
{
  "name": "transcription",
  "version": "1.0.0",
  "description": "YouTube and multi-source audio/video transcription",
  "prefix": "/api/transcription",
  "tags": ["transcription"],
  "enabled": true,
  "dependencies": ["assemblyai"]
}
```

**Configuration** :
- `DISABLED_MODULES` : variable d'environnement, liste comma-separee
- Exemple : `DISABLED_MODULES=conversation,future_module`

**Endpoint** : `GET /api/modules`
- Retourne la liste des modules enregistres avec metadata
- Accessible sans authentification (info publique)

**Gestion erreurs** :
- Manifest invalide : warning log, module ignore
- Import echoue : warning log, module ignore
- Module desactive : info log, module ignore
- L'application demarre toujours, meme si un module echoue

### Frontend

**Page** : `/modules` (`src/app/(dashboard)/modules/page.tsx`)
- Grid 3 colonnes (responsive)
- Chaque module = Card avec : nom, version, description, status chip, prefix, dependencies
- Skeleton loading + error state + empty state

**Navigation** :
- Section "Platform" ajoutee dans le menu lateral
- Item "Modules" avec icone `tabler:puzzle`

---

## 3. Impact sur main.py

**Avant** (hardcode) :
```python
from app.modules.transcription.routes import router as transcription_router
app.include_router(transcription_router, prefix="/api/transcription", tags=["transcription"])
```

**Apres** (auto-discovery) :
```python
from app.modules import ModuleRegistry
registered = ModuleRegistry.discover_modules(app)
logger.info("modules_registered", count=len(registered))
```

Les routers core (auth, ai-assistant) restent hardcodes car ce sont des composants fondamentaux, pas des plugins.

---

## 4. Nouvelles pages frontend

| Route | Description |
|-------|-------------|
| /chat | Chat contextuel IA avec historique conversations |
| /modules | Vue admin des modules de la plateforme |

**Navigation mise a jour** :
```
Dashboard
AI Modules
  Transcriptions
  Chat IA          <-- NOUVEAU
Platform
  Modules          <-- NOUVEAU
Account
  Profile
```

---

## 5. Migration base de donnees

```sql
CREATE TABLE conversations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  transcription_id UUID REFERENCES transcriptions(id),
  title VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE messages (
  id UUID PRIMARY KEY,
  conversation_id UUID REFERENCES conversations(id),
  role VARCHAR(20) NOT NULL,
  content TEXT NOT NULL,
  provider VARCHAR(50),
  tokens_used INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
```

---

## 6. Comment ajouter un nouveau module

1. Creer le dossier : `app/modules/mon_module/`
2. Creer `manifest.json` avec les metadonnees
3. Creer `routes.py` avec un `router = APIRouter()`
4. Creer `service.py` avec la logique metier
5. Redemarrer le backend : le module est auto-detecte et monte

Aucune modification de `main.py` necessaire.
