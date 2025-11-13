# 🚀 Architecture Plateforme SaaS IA - Transcription YouTube

## 📋 Vue d'ensemble du projet

**Nom du projet**: AI Transcription Platform  
**Version**: 1.0.0  
**Objectif**: Plateforme SaaS modulaire pour services d'IA, démarrant avec la transcription automatique de vidéos YouTube

---

## 🏗️ Architecture Technique

### Stack Technologique

#### Backend
- **Framework**: FastAPI 0.104+
- **Langage**: Python 3.11+
- **Base de données**: PostgreSQL 15
- **Cache**: Redis 7
- **File d'attente**: Celery + Redis
- **ORM**: SQLAlchemy 2.0

#### Frontend
- **Framework**: Next.js 14 (App Router)
- **Template**: Sneat MUI Next.js Admin v3.0.0
- **UI Library**: Material-UI (MUI) v5
- **State Management**: Zustand / React Query
- **TypeScript**: 5.0+

#### Services IA
- **Transcription**: Assembly AI (Free Tier: 5h/mois gratuit)
  - Alternative: OpenAI Whisper API
- **Extraction Audio**: yt-dlp
- **Correction linguistique**: LanguageTool API / GPT-3.5-turbo

#### Infrastructure
- **Containerisation**: Docker + Docker Compose
- **Reverse Proxy**: Nginx
- **Monitoring**: Prometheus + Grafana (optionnel phase 1)

---

## 🎯 API de Transcription Recommandée : Assembly AI

### Pourquoi Assembly AI ?

1. **Free Tier Généreux**: 
   - 5 heures de transcription gratuites par mois
   - Parfait pour démarrer et tester

2. **Qualités Exceptionnelles**:
   - Support multilingue (français, anglais, arabe, etc.)
   - Ponctuation automatique
   - Détection des locuteurs
   - Timestamps précis

3. **API Simple**:
   ```python
   import assemblyai as aai
   
   aai.settings.api_key = "votre_clé"
   transcriber = aai.Transcriber()
   transcript = transcriber.transcribe("audio.mp3")
   ```

4. **Pricing après Free Tier**:
   - $0.00025 par seconde ($0.015/minute)
   - ~$0.90 pour 1h de vidéo

### Alternatives

| Service | Free Tier | Prix/heure | Multilingue | Qualité |
|---------|-----------|------------|-------------|---------|
| Assembly AI | 5h/mois | $0.90 | ✅ Excellent | ⭐⭐⭐⭐⭐ |
| OpenAI Whisper | ❌ | $0.36 | ✅ Excellent | ⭐⭐⭐⭐⭐ |
| Deepgram | $200 crédits | $0.81 | ✅ Très bon | ⭐⭐⭐⭐ |
| Google STT | 60min/mois | $1.44 | ✅ Bon | ⭐⭐⭐⭐ |

---

## 📐 Architecture Détaillée

### Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                      │
│                    Next.js + Sneat Template                  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      NGINX (Reverse Proxy)                   │
│  - Port 80/443                                               │
│  - SSL Termination                                           │
│  - Load Balancing                                            │
└───────────────┬─────────────────────┬───────────────────────┘
                │                     │
                ▼                     ▼
    ┌───────────────────┐   ┌────────────────────┐
    │   Frontend         │   │   Backend API      │
    │   Next.js:3000     │   │   FastAPI:8000     │
    │                    │   │                    │
    │   - SSR/SSG        │   │   - REST API       │
    │   - MUI Components │   │   - WebSocket      │
    │   - State Mgmt     │   │   - Auth           │
    └───────────────────┘   └──────────┬─────────┘
                                       │
                    ┏──────────────────┼──────────────────┓
                    ▼                  ▼                  ▼
          ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
          │   PostgreSQL    │  │    Redis     │  │   Celery     │
          │   Port: 5432    │  │  Port: 6379  │  │   Worker     │
          │                 │  │              │  │              │
          │  - Transcripts  │  │  - Cache     │  │  - Async     │
          │  - Users        │  │  - Sessions  │  │    Tasks     │
          │  - Jobs         │  │  - Queue     │  │              │
          └─────────────────┘  └──────────────┘  └──────┬───────┘
                                                         │
                                                         ▼
                                              ┌───────────────────┐
                                              │   External APIs   │
                                              │                   │
                                              │  - Assembly AI    │
                                              │  - YouTube (yt-dlp│
                                              │  - LanguageTool   │
                                              └───────────────────┘
```

### Flux de Traitement

```
1. USER ACTION
   └─> Soumet URL YouTube

2. FRONTEND (Next.js)
   └─> POST /api/v1/transcriptions
       └─> Payload: { "youtube_url": "..." }

3. BACKEND (FastAPI)
   ├─> Validation URL
   ├─> Création Job dans DB (status: pending)
   ├─> Ajout dans Queue Celery
   └─> Return job_id au client

4. CELERY WORKER
   ├─> Téléchargement audio (yt-dlp)
   │   └─> Stockage temporaire
   ├─> Upload vers Assembly AI
   ├─> Attente transcription (polling)
   ├─> Réception transcription brute
   ├─> Post-traitement
   │   ├─> Correction ponctuation
   │   ├─> Normalisation
   │   └─> Formatage paragraphes
   ├─> Sauvegarde en DB
   └─> Mise à jour status (completed)

5. FRONTEND (Real-time update)
   └─> WebSocket / Polling
       └─> Affichage transcription finale
```

---

## 🗂️ Structure du Projet

```
ai-transcription-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # Point d'entrée FastAPI
│   │   ├── config.py               # Configuration centralisée
│   │   ├── database.py             # Connexion DB
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── transcription.py
│   │   │   └── job.py
│   │   ├── schemas/                # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── transcription.py
│   │   │   └── user.py
│   │   ├── api/                    # Endpoints API
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── transcriptions.py
│   │   │   │   ├── users.py
│   │   │   │   └── auth.py
│   │   │   └── deps.py             # Dépendances partagées
│   │   ├── services/               # Logique métier
│   │   │   ├── __init__.py
│   │   │   ├── transcription_service.py
│   │   │   ├── youtube_service.py
│   │   │   └── correction_service.py
│   │   ├── tasks/                  # Tâches Celery
│   │   │   ├── __init__.py
│   │   │   └── transcription_tasks.py
│   │   ├── core/                   # Utilitaires
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   └── celery_app.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── alembic/                    # Migrations DB
│   │   └── versions/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── transcription/
│   │   │   │   └── page.tsx
│   │   │   └── api/                # API routes (optionnel)
│   │   ├── components/
│   │   │   ├── TranscriptionForm.tsx
│   │   │   ├── TranscriptionDisplay.tsx
│   │   │   ├── JobStatus.tsx
│   │   │   └── Layout/             # Sneat components
│   │   ├── services/
│   │   │   └── api.ts              # API client
│   │   ├── hooks/
│   │   │   └── useTranscription.ts
│   │   ├── store/                  # Zustand stores
│   │   │   └── transcriptionStore.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   └── utils/
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml
├── nginx/
│   └── nginx.conf
├── docs/
│   ├── API.md
│   └── DEPLOYMENT.md
└── README.md
```

---

## 🔧 Configuration Docker Compose

### Services

1. **PostgreSQL**: Base de données principale
2. **Redis**: Cache et broker Celery
3. **Backend**: API FastAPI
4. **Celery Worker**: Traitement asynchrone
5. **Frontend**: Application Next.js
6. **Nginx**: Reverse proxy

---

## 📊 Modèle de Données

### Table: users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Table: transcriptions
```sql
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    youtube_url TEXT NOT NULL,
    video_title VARCHAR(500),
    video_duration INTEGER,
    language VARCHAR(10),
    status VARCHAR(50) DEFAULT 'pending',
    raw_transcript TEXT,
    corrected_transcript TEXT,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT
);
```

### Table: job_logs
```sql
CREATE TABLE job_logs (
    id SERIAL PRIMARY KEY,
    transcription_id UUID REFERENCES transcriptions(id),
    step VARCHAR(100),
    status VARCHAR(50),
    message TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

---

## 🛠️ Plan d'Implémentation Étape par Étape

### Phase 1: Configuration Environnement (Jour 1)

#### Étape 1.1: Initialisation du Projet
```bash
# Créer structure de base
mkdir ai-transcription-platform
cd ai-transcription-platform
mkdir -p backend/app frontend docs nginx

# Git init
git init
echo "*.env" > .gitignore
echo "__pycache__/" >> .gitignore
echo "node_modules/" >> .gitignore
```

#### Étape 1.2: Setup Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Créer requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
celery==5.3.4
redis==5.0.1
assemblyai==0.17.0
yt-dlp==2023.11.16
requests==2.31.0
python-dotenv==1.0.0
aiofiles==23.2.1
EOF

pip install -r requirements.txt
```

#### Étape 1.3: Setup Frontend
```bash
cd ../frontend

# Télécharger Sneat template
# [Télécharger depuis https://themeselection.com/item/sneat-mui-nextjs-admin-template/]
# Extraire dans frontend/

# Installer dépendances
npm install
# ou yarn install
```

#### Étape 1.4: Configuration Docker
```bash
cd ..
# Créer docker-compose.yml (voir fichier complet)
# Créer Dockerfile pour backend et frontend
```

### Phase 2: Backend Core (Jours 2-3)

#### Étape 2.1: Configuration de Base
- Créer `backend/app/config.py`
- Définir variables d'environnement
- Configuration base de données

#### Étape 2.2: Modèles SQLAlchemy
- Créer modèles User, Transcription, JobLog
- Setup Alembic migrations
- Créer première migration

#### Étape 2.3: Schémas Pydantic
- Définir schémas de validation
- Schémas de requête/réponse API

#### Étape 2.4: API Endpoints de Base
- POST `/api/v1/transcriptions` - Créer transcription
- GET `/api/v1/transcriptions/{id}` - Récupérer transcription
- GET `/api/v1/transcriptions` - Lister transcriptions
- DELETE `/api/v1/transcriptions/{id}` - Supprimer

### Phase 3: Services IA (Jours 4-5)

#### Étape 3.1: Service YouTube
```python
# backend/app/services/youtube_service.py
class YouTubeService:
    def download_audio(youtube_url: str) -> str:
        # Utiliser yt-dlp
        pass
    
    def get_video_info(youtube_url: str) -> dict:
        pass
```

#### Étape 3.2: Service Transcription
```python
# backend/app/services/transcription_service.py
class TranscriptionService:
    def transcribe_audio(audio_path: str, language: str) -> dict:
        # Assembly AI integration
        pass
```

#### Étape 3.3: Service Correction
```python
# backend/app/services/correction_service.py
class CorrectionService:
    def correct_transcript(text: str, language: str) -> str:
        # Post-traitement linguistique
        pass
```

### Phase 4: Tâches Celery (Jour 6)

#### Étape 4.1: Configuration Celery
- Setup celery app
- Configuration Redis broker

#### Étape 4.2: Tâche de Transcription
```python
@celery_app.task
def process_transcription(transcription_id: str):
    # 1. Download audio
    # 2. Transcribe
    # 3. Correct
    # 4. Save to DB
    pass
```

### Phase 5: Frontend (Jours 7-9)

#### Étape 5.1: Intégration Sneat Template
- Adapter layout principal
- Configurer routing
- Setup composants de base

#### Étape 5.2: Page Transcription
```tsx
// src/app/transcription/page.tsx
export default function TranscriptionPage() {
    // Form + Display component
}
```

#### Étape 5.3: Composants Clés
- `TranscriptionForm`: Input URL YouTube
- `JobStatus`: Affichage progression
- `TranscriptionDisplay`: Résultat formaté

#### Étape 5.4: API Integration
- Service HTTP client (axios/fetch)
- React Query pour cache
- WebSocket pour updates temps réel

### Phase 6: Intégration & Tests (Jours 10-11)

#### Étape 6.1: Tests Backend
- Tests unitaires services
- Tests intégration API
- Tests Celery tasks

#### Étape 6.2: Tests Frontend
- Tests composants
- Tests E2E avec Playwright

#### Étape 6.3: Tests Docker
- Lancer stack complète
- Tests bout-en-bout

### Phase 7: Polish & Documentation (Jour 12)

#### Étape 7.1: UX/UI
- Animations chargement
- Messages d'erreur
- Responsive design

#### Étape 7.2: Documentation
- README complet
- Documentation API (Swagger)
- Guide déploiement

---

## 🚦 Checklist de Lancement

### Pré-requis
- [ ] Docker et Docker Compose installés
- [ ] Compte Assembly AI créé (clé API)
- [ ] Template Sneat téléchargé
- [ ] Git installé

### Backend
- [ ] Variables environnement configurées
- [ ] Base de données créée et migrée
- [ ] Tests unitaires passent
- [ ] Celery worker démarre sans erreur
- [ ] API Swagger accessible

### Frontend
- [ ] Variables environnement configurées
- [ ] Build Next.js réussit
- [ ] Template Sneat intégré
- [ ] Composants de transcription fonctionnels

### Infrastructure
- [ ] Docker Compose lance tous les services
- [ ] Nginx route correctement
- [ ] Redis connecté
- [ ] PostgreSQL accessible

### Tests Intégration
- [ ] Transcription complète fonctionne end-to-end
- [ ] WebSocket updates en temps réel
- [ ] Gestion erreurs appropriée

---

## 🔐 Sécurité

### Best Practices Implémentées

1. **Authentification JWT**
   - Tokens avec expiration
   - Refresh tokens
   - HTTPS only cookies

2. **Validation Stricte**
   - Pydantic schemas
   - URL YouTube validation
   - Rate limiting

3. **Gestion Secrets**
   - Variables environnement
   - Pas de secrets en code
   - .env.example fourni

4. **CORS Configuration**
   - Origines autorisées définies
   - Credentials appropriés

---

## 📈 Évolutivité Future

### Modules IA Prévus

1. **Résumé Intelligent**
   - API: OpenAI GPT-4 / Claude
   - Résumés courts/moyens/longs
   - Points clés automatiques

2. **Analyse Sémantique**
   - Extraction entités nommées
   - Analyse sentiments
   - Topics principaux

3. **Traduction Automatique**
   - Support multi-langues
   - API: DeepL / Google Translate

4. **Génération de Contenu**
   - Articles de blog à partir transcription
   - Scripts vidéo
   - Notes structurées

### Architecture Modulaire

```python
# Structure pour ajouter nouveaux modules
app/
  services/
    ai_modules/
      __init__.py
      base_module.py          # Classe abstraite
      transcription/
      summarization/
      translation/
      analysis/
```

---

## 💰 Estimation Coûts (Phase MVP)

### Gratuit (Développement)
- Assembly AI: 5h/mois gratuit
- Infrastructure: Docker local
- **Total: 0€/mois**

### Production (Estimé 100h transcription/mois)
- Assembly AI: 100h × $0.90 = $90/mois
- Hébergement VPS (4GB RAM): $20-40/mois
- **Total: ~$110-130/mois**

---

## 🎯 Métriques de Succès

### KPIs Phase 1
- Temps moyen transcription < 2min pour 10min vidéo
- Précision transcription > 95%
- Disponibilité système > 99%
- Temps réponse API < 200ms

---

## 📚 Ressources & Documentation

### APIs
- Assembly AI Docs: https://www.assemblyai.com/docs
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- FastAPI: https://fastapi.tiangolo.com
- Next.js: https://nextjs.org/docs

### Template
- Sneat Demo: https://demos.themeselection.com/sneat-mui-nextjs-admin-template/
- Sneat Docs: https://demos.themeselection.com/sneat-mui-nextjs-admin-template/documentation/

---

## ✅ Prochaines Étapes

1. ⚙️ **Setup environnement** (Jour 1)
2. 🏗️ **Backend skeleton** (Jours 2-3)
3. 🤖 **Intégration Assembly AI** (Jours 4-5)
4. ⚡ **Celery tasks** (Jour 6)
5. 🎨 **Frontend Sneat** (Jours 7-9)
6. 🧪 **Tests & Debug** (Jours 10-11)
7. 📝 **Documentation finale** (Jour 12)

**Timeline estimée: 12 jours pour MVP fonctionnel**

---

## 🤝 Support & Contribution

Pour questions ou améliorations, consultez la documentation complète dans `/docs`.

**Bonne construction! 🚀**
