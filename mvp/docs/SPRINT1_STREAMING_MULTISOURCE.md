# Sprint 1 : Streaming SSE + Transcription Multi-Source

**Date** : 2026-03-22
**Version** : MVP 2.1.0
**Statut** : Termine

---

## 1. Streaming SSE des reponses IA

### Architecture

```
Frontend (useSSE hook)          Backend (FastAPI)
       |                              |
       |-- POST /ai-assistant/stream ->|
       |                              |-- ContentClassifier.classify()
       |                              |-- ModelSelector.select_model()
       |                              |-- PromptSelector.select_prompt()
       |                              |-- Provider.stream_chat()
       |<- data: {"token":"..."}\n\n --|  (chunk par chunk)
       |<- data: {"token":"..."}\n\n --|
       |<- data: {"done":true}\n\n  --|
       |                              |
```

### Backend

**Endpoint** : `POST /api/ai-assistant/stream`

**Fichiers modifies** :
- `app/ai_assistant/routes.py` : nouveau endpoint SSE
- `app/ai_assistant/service.py` : methode `stream_text()` (AsyncGenerator)

**Request** :
```json
{
  "text": "Texte a traiter",
  "task_type": "improve",
  "target_language": "fr",
  "strategy": "balanced"
}
```

**Response** (SSE stream) :
```
data: {"type": "meta", "provider": "gemini", "model": "gemini-2.5-flash"}

data: {"type": "token", "token": "Le "}

data: {"type": "token", "token": "texte "}

data: {"type": "token", "token": "ameliore..."}

data: {"type": "done", "provider": "gemini", "tokens_streamed": 142}

```

**Headers de reponse** :
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

**Gestion des erreurs** :
- Client deconnecte : detection via `request.is_disconnected()`, arret du stream
- Erreur provider : `data: {"type": "error", "error": "message"}\n\n`
- Fallback automatique si le provider principal echoue

### Frontend

**Fichiers crees** :
- `src/hooks/useSSE.ts` : hook reutilisable
- `src/components/ui/StreamingText.tsx` : composant d'affichage

**Hook useSSE** :
```typescript
const { startStream, stopStream, isStreaming } = useSSE()

startStream('/api/ai-assistant/stream', requestBody, {
  onToken: (token) => setText(prev => prev + token),
  onDone: (info) => console.log(`Done: ${info.tokens_streamed} tokens`),
  onError: (error) => showError(error)
})
```

Implementation :
- Utilise `fetch()` (pas axios) pour supporter ReadableStream
- `TextDecoder` + parsing SSE manuel des chunks
- `AbortController` pour annulation utilisateur
- Token JWT envoye via header Authorization
- Ref pour accumulation de texte (evite stale closures)

**Composant StreamingText** :
- Props : `text`, `isStreaming`, `provider`, `tokenCount`
- Curseur anime (blinking) pendant le streaming
- Metadata provider affichee une fois termine
- Whitespace preserve (`pre-wrap`)

**Integration page transcription** :
- Bouton "Improve with AI" sur les transcriptions completees
- Bouton "Stop" pendant le streaming actif
- Texte ameliore affiche progressivement
- "Copy improved text" disponible apres completion
- Label "Original Transcription" vs "AI-Improved" pour distinguer

---

## 2. Transcription Multi-Source

### Architecture

```
                  +------------------+
                  |   Frontend       |
                  |  (3 onglets)     |
                  +--------+---------+
                           |
          +----------------+----------------+
          |                |                |
   Tab 1: URL       Tab 2: Upload    Tab 3: Record
   POST /            POST /upload     POST /upload
   (youtube/url)     (multipart)      (multipart)
          |                |                |
          +----------------+----------------+
                           |
                  +--------v---------+
                  |   Backend        |
                  |  TranscriptionSvc|
                  +--------+---------+
                           |
              +------------+------------+
              |                         |
       YouTube/URL               Local File
       (yt-dlp)                  (direct)
              |                         |
              +------------+------------+
                           |
                  +--------v---------+
                  |   AssemblyAI     |
                  |   (ou MOCK)      |
                  +------------------+
```

### Backend

**Nouveau endpoint** : `POST /api/transcription/upload`

**Fichiers modifies** :
- `app/models/transcription.py` : champs `source_type`, `original_filename`
- `app/schemas/transcription.py` : validation source-aware, TranscriptionCreate/Read
- `app/modules/transcription/routes.py` : endpoint upload + source_type sur POST /
- `app/modules/transcription/service.py` : `process_upload_transcription()`, `_real_transcribe_file()`
- `app/rate_limit.py` : `transcription_upload: 5/minute`

**Modele Transcription** (champs ajoutes) :
```python
source_type: Optional[str] = Field(default="youtube", max_length=20)
original_filename: Optional[str] = Field(default=None, max_length=500)
```

**Endpoint upload** :
```
POST /api/transcription/upload
Content-Type: multipart/form-data

file: <binary>           # Requis
language: "fr"           # Optionnel, defaut "auto"
```

**Formats acceptes** :
| Extension | MIME Type |
|-----------|-----------|
| .mp3 | audio/mpeg |
| .wav | audio/wav, audio/x-wav |
| .mp4 | video/mp4 |
| .m4a | audio/mp4, audio/x-m4a |
| .ogg | audio/ogg |
| .webm | audio/webm, video/webm |
| .flac | audio/flac |

**Limites** :
- Taille max : 500 MB
- Rate limit : 5 uploads/minute
- Fichier vide rejete

**Validation URL source-aware** :
- `source_type="youtube"` : regex YouTube (youtube.com/watch, youtu.be, youtube.com/embed)
- `source_type="url"` : validation HTTP(S) generique
- `source_type="upload"` : pas de validation URL (set en interne)

**Pipeline upload** :
1. Validation fichier (extension, MIME, taille)
2. Sauvegarde temporaire dans le cache audio
3. Creation enregistrement Transcription (status=pending)
4. BackgroundTask : envoi a AssemblyAI (ou MOCK)
5. Mise a jour status (completed/failed)
6. Nettoyage fichier temporaire (finally)

### Frontend

**Fichiers crees** :
- `src/components/ui/AudioRecorder.tsx` : composant enregistrement micro

**Fichiers modifies** :
- `src/features/transcription/types.ts` : `TranscriptionSourceType`, `TranscriptionUploadRequest`
- `src/features/transcription/api.ts` : `uploadTranscription()` avec onUploadProgress
- `src/features/transcription/hooks/useTranscriptionMutations.ts` : `useUploadTranscription()`
- `src/app/(dashboard)/transcription/page.tsx` : interface 3 onglets

**Onglet 1 - YouTube / URL** :
- Formulaire existant inchange
- Support `source_type="url"` pour URLs non-YouTube

**Onglet 2 - Upload File** :
- Zone drag & drop avec bordure en pointilles
- Validation cote client (extension, taille)
- Preview fichier : nom, taille formatee, type
- Selecteur de langue
- Barre de progression upload (`LinearProgress`)
- Bouton submit desactive pendant l'upload

**Onglet 3 - Record Audio** :
- Composant `AudioRecorder` autonome
- Machine a etats : idle -> recording -> recorded -> idle
- Timer en temps reel (MM:SS) avec duree max (10 min)
- Preview audio native (`<audio>` element)
- Boutons : "Record Again" (discard) / "Use This Recording" (submit)
- Format : WebM/Opus
- Nom fichier genere : `recording-YYYYMMDD-HHMMSS.webm`
- Auto-upload via `uploadTranscription()` apres confirmation
- Gestion erreurs micro (permission, absence, utilisation)

**Liste transcriptions** :
- Colonne "Source" avec icone (YouTube/Upload/Link) + tooltip
- Uploads affichent le nom du fichier original au lieu de l'URL

---

## 3. Nouveaux endpoints API

| Methode | Endpoint | Description | Auth | Rate Limit |
|---------|----------|-------------|------|------------|
| POST | /api/ai-assistant/stream | Streaming SSE traitement IA | Oui | - |
| POST | /api/transcription/upload | Upload fichier audio/video | Oui | 5/min |

---

## 4. Migration base de donnees

Nouveaux champs sur la table `transcriptions` :
```sql
ALTER TABLE transcriptions ADD COLUMN source_type VARCHAR(20) DEFAULT 'youtube';
ALTER TABLE transcriptions ADD COLUMN original_filename VARCHAR(500) DEFAULT NULL;
```

Backward-compatible : les enregistrements existants ont `source_type='youtube'` par defaut.

---

## 5. Dependances

Aucune nouvelle dependance ajoutee. Toutes les fonctionnalites utilisent les packages existants :
- `python-multipart` (deja present) pour les uploads
- `yt-dlp` (deja present) pour les URLs multi-plateformes
- `assemblyai` (deja present) pour la transcription de fichiers locaux
- `fetch()` API native du navigateur pour le SSE (pas de lib supplementaire)
