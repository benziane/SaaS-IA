# Documentation API

Base URL : `http://localhost:8000/api/v1`

Documentation interactive : `http://localhost:8000/docs`

## Authentication

Actuellement, l'API ne nécessite pas d'authentification. L'authentification sera ajoutée dans les versions futures.

## Endpoints

### Health Check

#### GET `/health`

Vérifier l'état de l'API

**Response 200**
```json
{
  "status": "healthy",
  "service": "transcription-api"
}
```

---

### Transcriptions

#### POST `/transcriptions/`

Créer une nouvelle transcription

**Request Body**
```json
{
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "language": "auto"  // Options: "auto", "fr", "en", "ar"
}
```

**Response 201**
```json
{
  "id": 1,
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "video_id": "dQw4w9WgXcQ",
  "video_title": null,
  "video_duration": null,
  "channel_name": null,
  "language": "auto",
  "detected_language": null,
  "status": "pending",
  "progress": 0,
  "error_message": null,
  "raw_transcript": null,
  "corrected_transcript": null,
  "transcription_service": null,
  "model_used": null,
  "processing_time": null,
  "confidence_score": null,
  "word_count": null,
  "metadata": null,
  "is_public": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": null,
  "completed_at": null
}
```

---

#### GET `/transcriptions/{id}`

Obtenir une transcription par ID

**Parameters**
- `id` (path, required) : ID de la transcription

**Response 200**
```json
{
  "id": 1,
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "video_id": "dQw4w9WgXcQ",
  "video_title": "Example Video Title",
  "video_duration": 213.5,
  "channel_name": "Example Channel",
  "language": "auto",
  "detected_language": "en",
  "status": "completed",
  "progress": 100,
  "error_message": null,
  "raw_transcript": "This is the raw transcript...",
  "corrected_transcript": "This is the corrected transcript with proper punctuation and formatting...",
  "transcription_service": "whisper",
  "model_used": "base",
  "processing_time": 45.2,
  "confidence_score": 0.95,
  "word_count": 1234,
  "metadata": {
    "segments": [...]
  },
  "is_public": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:45Z",
  "completed_at": "2024-01-15T10:35:45Z"
}
```

**Response 404**
```json
{
  "detail": "Transcription not found"
}
```

---

#### GET `/transcriptions/`

Lister toutes les transcriptions avec pagination

**Query Parameters**
- `page` (integer, default: 1) : Numéro de page
- `page_size` (integer, default: 20, max: 100) : Nombre d'éléments par page
- `status` (string, optional) : Filtrer par statut
- `language` (string, optional) : Filtrer par langue

**Response 200**
```json
{
  "transcriptions": [
    {
      "id": 1,
      "youtube_url": "https://www.youtube.com/watch?v=...",
      ...
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

#### GET `/transcriptions/video/{video_id}`

Obtenir une transcription par ID vidéo YouTube

**Parameters**
- `video_id` (path, required) : ID de la vidéo YouTube

**Response 200**
```json
{
  "id": 1,
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  ...
}
```

**Response 404**
```json
{
  "detail": "Transcription not found for this video"
}
```

---

#### POST `/transcriptions/preview`

Prévisualiser les informations d'une vidéo sans créer de transcription

**Query Parameters**
- `url` (string, required) : URL de la vidéo YouTube

**Response 200**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Example Video",
  "duration": 213.5,
  "channel": "Example Channel",
  "description": "Video description...",
  "thumbnail": "https://i.ytimg.com/...",
  "upload_date": "20240115",
  "view_count": 1000000
}
```

**Response 400**
```json
{
  "detail": "Failed to get video info: ..."
}
```

---

#### DELETE `/transcriptions/{id}`

Supprimer une transcription (soft delete)

**Parameters**
- `id` (path, required) : ID de la transcription

**Response 200**
```json
{
  "message": "Transcription deleted successfully"
}
```

**Response 404**
```json
{
  "detail": "Transcription not found"
}
```

---

#### GET `/transcriptions/stats/overview`

Obtenir les statistiques globales des transcriptions

**Response 200**
```json
{
  "total_transcriptions": 150,
  "completed": 120,
  "in_progress": 25,
  "failed": 5,
  "total_duration": 18000.5,
  "total_processing_time": 3600.2,
  "average_confidence": 0.92,
  "languages": {
    "fr": 80,
    "en": 50,
    "ar": 20
  }
}
```

---

## Statuts de Transcription

| Statut | Description |
|--------|-------------|
| `pending` | En attente de traitement |
| `downloading` | Téléchargement de l'audio en cours |
| `extracting` | Extraction de l'audio en cours |
| `transcribing` | Transcription IA en cours |
| `post_processing` | Correction et formatage du texte |
| `completed` | Transcription terminée avec succès |
| `failed` | Échec du traitement |

## Codes d'Erreur

| Code | Description |
|------|-------------|
| 200 | Succès |
| 201 | Créé avec succès |
| 400 | Requête invalide |
| 404 | Ressource non trouvée |
| 422 | Erreur de validation |
| 500 | Erreur serveur |

## Rate Limiting

Actuellement, il n'y a pas de limite de taux. Une limite sera implémentée dans les versions futures :
- 10 requêtes/minute par IP
- 100 transcriptions/jour par utilisateur

## Exemples d'Utilisation

### cURL

```bash
# Créer une transcription
curl -X POST "http://localhost:8000/api/v1/transcriptions/" \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "language": "auto"}'

# Obtenir le statut
curl "http://localhost:8000/api/v1/transcriptions/1"

# Lister les transcriptions
curl "http://localhost:8000/api/v1/transcriptions/?page=1&page_size=10"

# Statistiques
curl "http://localhost:8000/api/v1/transcriptions/stats/overview"
```

### Python

```python
import requests

API_URL = "http://localhost:8000/api/v1"

# Créer une transcription
response = requests.post(
    f"{API_URL}/transcriptions/",
    json={
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "language": "auto"
    }
)
transcription = response.json()
print(f"Created transcription ID: {transcription['id']}")

# Suivre la progression
import time
while True:
    response = requests.get(f"{API_URL}/transcriptions/{transcription['id']}")
    data = response.json()

    print(f"Status: {data['status']} - Progress: {data['progress']}%")

    if data['status'] in ['completed', 'failed']:
        break

    time.sleep(3)

# Afficher le résultat
if data['status'] == 'completed':
    print("\nTranscription:")
    print(data['corrected_transcript'])
```

### JavaScript/TypeScript

```typescript
const API_URL = 'http://localhost:8000/api/v1';

// Créer une transcription
const createTranscription = async (youtubeUrl: string) => {
  const response = await fetch(`${API_URL}/transcriptions/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      youtube_url: youtubeUrl,
      language: 'auto',
    }),
  });

  return await response.json();
};

// Obtenir une transcription
const getTranscription = async (id: number) => {
  const response = await fetch(`${API_URL}/transcriptions/${id}`);
  return await response.json();
};

// Utilisation
const transcription = await createTranscription('https://www.youtube.com/watch?v=...');
console.log(`Created transcription ID: ${transcription.id}`);

// Polling pour le statut
const pollStatus = async (id: number) => {
  const data = await getTranscription(id);
  console.log(`Status: ${data.status} - Progress: ${data.progress}%`);

  if (data.status === 'completed') {
    console.log('Transcription:', data.corrected_transcript);
  } else if (data.status !== 'failed') {
    setTimeout(() => pollStatus(id), 3000);
  }
};

pollStatus(transcription.id);
```

## Webhooks (À venir)

Les webhooks permettront de recevoir des notifications lors de changements d'état :

```json
POST https://your-domain.com/webhook
{
  "event": "transcription.completed",
  "transcription_id": 1,
  "status": "completed",
  "timestamp": "2024-01-15T10:35:45Z"
}
```
