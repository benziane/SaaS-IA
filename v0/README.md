# 🎥 YouTube Transcription SaaS Platform

Une plateforme SaaS moderne pour la transcription automatique de vidéos YouTube avec intelligence artificielle, correction linguistique et formatage automatique.

## 🌟 Fonctionnalités

### Transcription YouTube
- ✅ **Extraction audio automatique** depuis n'importe quelle URL YouTube
- ✅ **Transcription multilingue** (Français, Anglais, Arabe + 90 langues)
- ✅ **Détection automatique de la langue**
- ✅ **Correction linguistique IA** (ponctuation, grammaire, formatage)
- ✅ **Traitement en arrière-plan** avec suivi en temps réel
- ✅ **Interface web moderne** avec Material-UI (inspiré du template Sneat)

### Caractéristiques techniques
- 🚀 **Backend FastAPI** performant et asynchrone
- ⚛️ **Frontend Next.js** avec TypeScript et Material-UI
- 🐳 **Architecture Docker** complète et prête à déployer
- 🗄️ **Base de données PostgreSQL** pour la persistance
- 📊 **Suivi en temps réel** de la progression
- 🔄 **Architecture évolutive** pour ajouter de futurs modules IA

## 🏗️ Architecture

```
SaaS-IA/
├── backend/               # API FastAPI
│   ├── app/
│   │   ├── api/          # Endpoints REST
│   │   ├── core/         # Configuration et database
│   │   ├── models/       # Modèles SQLAlchemy
│   │   ├── schemas/      # Schémas Pydantic
│   │   ├── services/     # Logique métier
│   │   │   ├── youtube_extractor.py      # Extraction YouTube
│   │   │   ├── transcription_service.py  # Transcription IA
│   │   │   ├── post_processor.py         # Correction linguistique
│   │   │   └── transcription_orchestrator.py # Orchestration
│   │   └── main.py       # Point d'entrée
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # Application Next.js
│   ├── src/
│   │   ├── components/   # Composants React
│   │   ├── pages/        # Pages Next.js
│   │   ├── hooks/        # Custom hooks
│   │   ├── lib/          # API client
│   │   └── types/        # Types TypeScript
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml    # Orchestration des services
```

## 🚀 Installation et Démarrage

### Prérequis
- Docker et Docker Compose
- Git

### Démarrage rapide

1. **Cloner le repository**
```bash
git clone <repository-url>
cd SaaS-IA
```

2. **Configurer les variables d'environnement**
```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env
```

3. **Lancer l'application avec Docker Compose**
```bash
docker-compose up -d
```

4. **Accéder aux services**
- 🌐 **Frontend** : http://localhost:3000
- 🔌 **API Backend** : http://localhost:8000
- 📚 **Documentation API** : http://localhost:8000/docs
- 🗄️ **pgAdmin** (optionnel) : http://localhost:5050

### Installation en développement

#### Backend
```bash
cd backend

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Télécharger les modèles de langue
python -m spacy download fr_core_news_md
python -m spacy download en_core_web_md

# Lancer le serveur
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

## 📖 Utilisation

### Via l'interface web

1. Ouvrez http://localhost:3000
2. Collez une URL YouTube dans le formulaire
3. Sélectionnez la langue (ou laissez sur "Auto")
4. Cliquez sur "Lancer la transcription"
5. Suivez la progression en temps réel
6. Copiez ou téléchargez le résultat

### Via l'API

#### Créer une transcription
```bash
curl -X POST "http://localhost:8000/api/v1/transcriptions/" \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "language": "auto"
  }'
```

#### Récupérer une transcription
```bash
curl "http://localhost:8000/api/v1/transcriptions/1"
```

#### Lister les transcriptions
```bash
curl "http://localhost:8000/api/v1/transcriptions/?page=1&page_size=20"
```

## 🔧 Configuration

### Variables d'environnement Backend

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/transcription_db

# Redis
REDIS_URL=redis://redis:6379/0

# Transcription Service
TRANSCRIPTION_SERVICE=whisper  # whisper, assemblyai, deepgram
WHISPER_MODEL=base  # tiny, base, small, medium, large

# API Keys (optionnel pour services externes)
ASSEMBLYAI_API_KEY=your-key-here
DEEPGRAM_API_KEY=your-key-here

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Variables d'environnement Frontend

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 🧪 Tests

### Backend
```bash
cd backend
pytest
```

### Frontend
```bash
cd frontend
npm run test
```

## 📊 API Documentation

Documentation interactive disponible à : http://localhost:8000/docs

### Principaux endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/transcriptions/` | Créer une nouvelle transcription |
| GET | `/api/v1/transcriptions/{id}` | Obtenir une transcription |
| GET | `/api/v1/transcriptions/` | Lister les transcriptions |
| GET | `/api/v1/transcriptions/video/{video_id}` | Transcription par ID vidéo |
| POST | `/api/v1/transcriptions/preview` | Prévisualiser une vidéo |
| DELETE | `/api/v1/transcriptions/{id}` | Supprimer une transcription |
| GET | `/api/v1/transcriptions/stats/overview` | Statistiques globales |
| GET | `/api/v1/health` | Health check |

## 🔐 Sécurité

- CORS configuré pour les origines autorisées
- Validation des entrées avec Pydantic
- Gestion sécurisée des secrets avec variables d'environnement
- Health checks pour tous les services

## 🚀 Déploiement en Production

### Avec Docker Compose

```bash
# Production build
docker-compose -f docker-compose.prod.yml up -d
```

### Variables importantes pour la production

```env
# Backend
DEBUG=False
ENVIRONMENT=production
SECRET_KEY=<générer-une-clé-forte>

# Database
DATABASE_URL=<url-base-de-données-production>

# Domains
CORS_ORIGINS=https://votre-domaine.com
```

## 🛣️ Roadmap

### Version actuelle (v1.0.0)
- ✅ Transcription YouTube multilingue
- ✅ Correction linguistique automatique
- ✅ Interface web moderne
- ✅ API REST complète

### Prochaines fonctionnalités
- 🔲 Authentification utilisateur
- 🔲 Résumé automatique des transcriptions
- 🔲 Analyse sémantique du contenu
- 🔲 Export en multiple formats (PDF, DOCX, SRT)
- 🔲 Traduction automatique
- 🔲 Génération de sous-titres
- 🔲 Dashboard analytics avancé
- 🔲 API webhooks
- 🔲 Support de playlists YouTube

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/amazing-feature`)
3. Commit vos changements (`git commit -m 'Add amazing feature'`)
4. Push sur la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

## 📝 License

Ce projet est sous licence MIT.

## 🙏 Remerciements

- **OpenAI Whisper** pour le modèle de transcription
- **Template Sneat MUI** pour l'inspiration du design
- **FastAPI** pour le framework backend
- **Next.js** pour le framework frontend
- **yt-dlp** pour l'extraction YouTube

## 📧 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la documentation API : http://localhost:8000/docs

---

**Développé avec ❤️ pour rendre la transcription vidéo accessible à tous**
