# Architecture Technique

## Vue d'ensemble

Cette plateforme SaaS est construite sur une architecture moderne en microservices, avec séparation claire entre le frontend, le backend et les services de données.

## Stack Technologique

### Backend
- **Framework** : FastAPI (Python 3.11+)
- **Base de données** : PostgreSQL 15 avec SQLAlchemy (async)
- **Cache** : Redis 7
- **Transcription IA** : OpenAI Whisper
- **Post-traitement** : Language Tool, spaCy, DeepMultilingualPunctuation
- **Extraction YouTube** : yt-dlp
- **Task Queue** : Celery (prévu)

### Frontend
- **Framework** : Next.js 14 (React 18)
- **Langage** : TypeScript
- **UI Library** : Material-UI (MUI) v5
- **State Management** : SWR pour la gestion du cache
- **HTTP Client** : Axios

### Infrastructure
- **Containerisation** : Docker & Docker Compose
- **Base de données** : PostgreSQL avec pgAdmin
- **Cache/Broker** : Redis

## Architecture des Services

### Backend API (FastAPI)

#### Structure en couches

```
app/
├── api/              # Couche API (endpoints REST)
├── core/             # Configuration et infrastructure
├── models/           # Modèles de données (SQLAlchemy)
├── schemas/          # Schémas de validation (Pydantic)
├── services/         # Logique métier
└── utils/            # Utilitaires
```

#### Services principaux

1. **YouTubeExtractor**
   - Extraction d'informations vidéo
   - Téléchargement audio
   - Conversion de format

2. **TranscriptionService**
   - Support multi-providers (Whisper, AssemblyAI, Deepgram)
   - Gestion des modèles IA
   - Optimisation GPU/CPU

3. **TranscriptPostProcessor**
   - Restauration de ponctuation
   - Correction grammaticale
   - Normalisation du texte
   - Suppression des mots de remplissage
   - Formatage en paragraphes

4. **TranscriptionOrchestrator**
   - Coordination du pipeline complet
   - Gestion des états
   - Gestion des erreurs
   - Callbacks de progression

### Pipeline de Transcription

```
1. Réception de l'URL YouTube
   ↓
2. Extraction de l'audio (yt-dlp)
   ↓
3. Transcription IA (Whisper)
   ↓
4. Post-traitement linguistique
   ↓
5. Stockage en base de données
   ↓
6. Notification du client
```

### Modèle de Données

#### Table `transcriptions`

```sql
CREATE TABLE transcriptions (
    id SERIAL PRIMARY KEY,
    youtube_url VARCHAR(500) NOT NULL,
    video_id VARCHAR(100) NOT NULL,
    video_title VARCHAR(500),
    video_duration FLOAT,
    channel_name VARCHAR(200),

    language VARCHAR(10),
    detected_language VARCHAR(10),

    status VARCHAR(50) NOT NULL,
    progress INTEGER DEFAULT 0,
    error_message TEXT,

    raw_transcript TEXT,
    corrected_transcript TEXT,

    transcription_service VARCHAR(50),
    model_used VARCHAR(100),
    processing_time FLOAT,
    confidence_score FLOAT,

    word_count INTEGER,
    metadata JSONB,
    audio_file_path VARCHAR(500),

    is_public BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);
```

### États de Transcription

```typescript
enum TranscriptionStatus {
    PENDING = "pending"              // En attente de traitement
    DOWNLOADING = "downloading"       // Téléchargement de l'audio
    EXTRACTING = "extracting"        // Extraction de l'audio
    TRANSCRIBING = "transcribing"    // Transcription en cours
    POST_PROCESSING = "post_processing" // Correction du texte
    COMPLETED = "completed"          // Terminé avec succès
    FAILED = "failed"                // Échec du traitement
}
```

## Frontend Architecture

### Structure des Pages

```
src/
├── components/       # Composants réutilisables
│   ├── TranscriptionForm.tsx
│   ├── TranscriptionStatus.tsx
│   └── TranscriptionResult.tsx
├── pages/           # Pages Next.js
│   ├── _app.tsx     # Configuration globale
│   └── index.tsx    # Page d'accueil
├── hooks/           # Custom hooks React
│   └── useTranscription.ts
├── lib/             # Bibliothèques et utilitaires
│   └── api.ts       # Client API
├── types/           # Définitions TypeScript
│   └── transcription.ts
└── styles/          # Styles globaux
```

### Gestion de l'État

- **SWR** pour le cache des données API
- **React State** pour l'état local des composants
- Auto-refresh pour les transcriptions en cours

### Communication API

```typescript
// Client API configuré
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  timeout: 300000, // 5 minutes
});

// Hooks personnalisés
useTranscription(id, autoRefresh)
useTranscriptionList(params)
useCreateTranscription()
```

## Infrastructure Docker

### Services

1. **db** (PostgreSQL)
   - Base de données principale
   - Volume persistant
   - Health checks

2. **redis**
   - Cache et message broker
   - Persistance activée

3. **backend** (FastAPI)
   - Multi-stage build
   - Hot reload en dev
   - Health checks

4. **frontend** (Next.js)
   - Build optimisé
   - Volume pour hot reload
   - Variables d'environnement

### Networking

```yaml
networks:
  transcription_network:
    driver: bridge
```

Tous les services communiquent via un réseau bridge Docker privé.

### Volumes

- `postgres_data` : Données PostgreSQL
- `redis_data` : Persistance Redis
- `uploads_data` : Fichiers audio téléchargés

## Scalabilité

### Horizontal Scaling

- **Backend** : Ajout de replicas FastAPI derrière un load balancer
- **Workers** : Celery workers pour le traitement asynchrone
- **Database** : PostgreSQL avec read replicas

### Optimisations

1. **Cache Redis**
   - Cache des métadonnées vidéo
   - Sessions utilisateur
   - Rate limiting

2. **Async Processing**
   - Utilisation d'asyncio pour I/O non-bloquant
   - Background tasks FastAPI
   - Celery pour tâches longues (futur)

3. **Database**
   - Index sur `video_id`, `status`, `created_at`
   - Connection pooling
   - Async queries avec asyncpg

## Sécurité

### Backend
- Validation des entrées avec Pydantic
- CORS configuré
- Rate limiting (prévu)
- Secrets via variables d'environnement

### Frontend
- Validation côté client
- HTTPS en production
- CSP headers (prévu)

## Monitoring et Logging

### Logs structurés
```python
# JSON logging pour faciliter l'analyse
logger = logging.getLogger(__name__)
logger.info("Transcription started", extra={
    "transcription_id": id,
    "video_id": video_id
})
```

### Health Checks
- `/api/v1/health` pour le backend
- Health checks Docker pour tous les services

## Extensions Futures

### Architecture modulaire pour nouveaux services

```python
# Plugin pattern pour nouveaux modules IA
class AIServicePlugin:
    def process(self, input_data):
        pass

# Exemples de futurs plugins
- SummaryService      # Résumé automatique
- TranslationService  # Traduction multilingue
- SentimentService    # Analyse de sentiment
- KeywordService      # Extraction de mots-clés
```

### Event-Driven Architecture

- Webhooks pour notifications
- Event sourcing pour l'historique
- Message queue pour orchestration

## Performance

### Métriques cibles

- **Temps de réponse API** : < 200ms (hors traitement)
- **Temps de transcription** : ~1.5x la durée vidéo (GPU)
- **Concurrent users** : 100+ utilisateurs simultanés
- **Throughput** : 1000+ requêtes/minute

### Optimisations prévues

1. CDN pour le frontend
2. Cache CloudFlare
3. Database query optimization
4. GPU acceleration pour Whisper
5. Batch processing pour multiples vidéos

---

Cette architecture est conçue pour évoluer avec les besoins de la plateforme tout en maintenant performance, fiabilité et maintenabilité.
