# 🚀 AI Transcription Platform

Plateforme SaaS modulaire pour services d'intelligence artificielle, démarrant avec la transcription automatique de vidéos YouTube.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![Next.js](https://img.shields.io/badge/Next.js-14-black)

## 📋 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [Contribution](#contribution)

## 🎯 Vue d'ensemble

Cette plateforme offre une transcription automatique de vidéos YouTube avec :
- ✅ Extraction audio automatique
- ✅ Transcription multilingue (FR, EN, AR, ES, DE, IT, PT)
- ✅ Correction linguistique et formatage IA
- ✅ Interface moderne et intuitive
- ✅ Architecture évolutive pour futurs modules IA

### 🎬 Demo

```
URL YouTube → Transcription complète en quelques minutes
```

## 🌟 Fonctionnalités

### MVP v1.0
- 📺 **Transcription YouTube** : Collez une URL, obtenez une transcription propre
- 🌍 **Multilingue** : Support de 7 langues avec auto-détection
- 🤖 **IA avancée** : Assembly AI pour précision maximale (95%+)
- ✨ **Post-traitement** : Correction automatique de ponctuation, capitalisation, formatage
- ⚡ **Traitement asynchrone** : Jobs Celery pour performances optimales
- 📊 **Suivi temps réel** : Voir la progression étape par étape
- 💾 **Historique** : Accédez à toutes vos transcriptions

### Futures fonctionnalités (Roadmap)
- 📝 Résumé intelligent
- 🔍 Analyse sémantique
- 🌐 Traduction automatique
- ✍️ Génération de contenu

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (Next.js)              │
│    Sneat MUI Template + TypeScript      │
└──────────────┬──────────────────────────┘
               │ REST API
┌──────────────▼──────────────────────────┐
│         Backend (FastAPI)               │
│    Python 3.11 + SQLAlchemy + Celery   │
└──────┬───────────────┬──────────────────┘
       │               │
┌──────▼─────┐  ┌──────▼──────┐
│ PostgreSQL │  │    Redis    │
│   + Alembic│  │   + Celery  │
└────────────┘  └─────────────┘
       │
┌──────▼─────────────────┐
│   Services Externes    │
│  • Assembly AI         │
│  • YouTube (yt-dlp)    │
└────────────────────────┘
```

### Stack technique

**Backend:**
- FastAPI 0.104+
- Python 3.11+
- SQLAlchemy 2.0 + AsyncPG
- Celery 5.3 + Redis
- Assembly AI SDK

**Frontend:**
- Next.js 14 (App Router)
- Material-UI v5
- Sneat Template v3.0
- TypeScript 5
- Axios + React Query

**Infrastructure:**
- Docker + Docker Compose
- PostgreSQL 15
- Redis 7
- Nginx (production)

## 📋 Prérequis

- Docker & Docker Compose
- Node.js 18+ (pour développement frontend local)
- Python 3.11+ (pour développement backend local)
- Compte Assembly AI (clé API gratuite : 5h/mois)

## 🚀 Installation

### 1. Cloner le repository

```bash
git clone https://github.com/votre-username/ai-transcription-platform.git
cd ai-transcription-platform
```

### 2. Configuration des variables d'environnement

#### Backend
```bash
cd backend
cp .env.example .env
# Éditez .env et ajoutez votre clé Assembly AI
```

**Important :** Obtenez votre clé Assembly AI gratuite sur https://www.assemblyai.com/

#### Frontend
```bash
cd frontend
cp .env.example .env.local
# Configurez l'URL du backend si nécessaire
```

### 3. Lancement avec Docker Compose

```bash
# À la racine du projet
docker-compose up -d
```

Cette commande lance :
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ Backend FastAPI (port 8000)
- ✅ Frontend Next.js (port 3000)
- ✅ Celery Worker
- ✅ Celery Beat

### 4. Vérification

- Frontend : http://localhost:3000
- Backend API : http://localhost:8000
- Documentation API : http://localhost:8000/docs
- Flower (monitoring Celery) : http://localhost:5555 (si lancé)

## ⚙️ Configuration

### Assembly AI

1. Créez un compte gratuit sur https://www.assemblyai.com/
2. Obtenez votre clé API (Dashboard → API Keys)
3. Ajoutez-la dans `backend/.env` :

```env
ASSEMBLYAI_API_KEY=votre_cle_api_ici
```

**Free Tier :** 5 heures de transcription/mois gratuites !

### Base de données

Les migrations sont automatiquement appliquées au démarrage.

Pour créer une nouvelle migration :

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 📖 Utilisation

### Interface Web

1. Accédez à http://localhost:3000
2. Collez une URL YouTube dans le formulaire
3. Sélectionnez la langue (ou laissez en auto-détection)
4. Cliquez sur "Lancer la transcription"
5. Suivez la progression en temps réel
6. Téléchargez ou copiez la transcription finale

### API REST

#### Créer une transcription

```bash
curl -X POST http://localhost:8000/api/v1/transcriptions/ \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "language": "fr"
  }'
```

#### Récupérer une transcription

```bash
curl http://localhost:8000/api/v1/transcriptions/{id}
```

#### Lister les transcriptions

```bash
curl http://localhost:8000/api/v1/transcriptions/?page=1&page_size=10
```

Documentation complète : http://localhost:8000/docs

## 📚 Documentation

### Structure du projet

```
ai-transcription-platform/
├── backend/                    # API FastAPI
│   ├── app/
│   │   ├── api/               # Endpoints REST
│   │   ├── core/              # Configuration Celery
│   │   ├── models/            # Modèles SQLAlchemy
│   │   ├── schemas/           # Schémas Pydantic
│   │   ├── services/          # Logique métier
│   │   ├── tasks/             # Tâches Celery
│   │   └── main.py            # Point d'entrée
│   ├── alembic/               # Migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                   # Application Next.js
│   ├── src/
│   │   ├── app/               # Pages (App Router)
│   │   ├── components/        # Composants React
│   │   ├── services/          # Client API
│   │   └── types/             # Types TypeScript
│   ├── package.json
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml
├── ARCHITECTURE_ET_IMPLEMENTATION.md
├── presentation.html
└── README.md
```

### Documentation détaillée

- 📘 [Architecture et implémentation](./ARCHITECTURE_ET_IMPLEMENTATION.md)
- 🎨 [Présentation visuelle](./presentation.html)
- 📚 [API Documentation](http://localhost:8000/docs) (après lancement)

## 🗺️ Roadmap

### Phase 1 - MVP ✅ (Actuel)
- [x] Transcription YouTube
- [x] Interface Sneat
- [x] API REST complète
- [x] Traitement asynchrone

### Phase 2 - Enrichissement IA (Q1 2025)
- [ ] Résumé automatique (GPT-4)
- [ ] Extraction de mots-clés
- [ ] Détection de sujets

### Phase 3 - Analyse avancée (Q2 2025)
- [ ] Analyse de sentiments
- [ ] Entités nommées
- [ ] Topics modeling

### Phase 4 - Multimédia (Q3 2025)
- [ ] Support fichiers audio directs
- [ ] Traduction multilingue
- [ ] Génération de sous-titres

## 💰 Coûts

### Développement (Gratuit)
- Assembly AI : 5h/mois gratuit
- Infrastructure locale : Docker gratuit
- **Total : 0€/mois**

### Production (100h transcription/mois)
- Assembly AI : ~90€/mois
- VPS 4GB RAM : 20-40€/mois
- **Total : ~110-130€/mois**

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👥 Auteurs

- **Votre Nom** - Développement initial

## 🙏 Remerciements

- [Assembly AI](https://www.assemblyai.com/) pour leur excellente API
- [FastAPI](https://fastapi.tiangolo.com/) pour le framework
- [Next.js](https://nextjs.org/) pour le frontend
- [Sneat Template](https://themeselection.com/) pour l'UI

## 📞 Support

Pour toute question ou problème :
- 📧 Email : support@example.com
- 🐛 Issues : https://github.com/votre-username/ai-transcription-platform/issues
- 💬 Discussions : https://github.com/votre-username/ai-transcription-platform/discussions

---

⭐ Si ce projet vous aide, n'hésitez pas à lui donner une étoile !
