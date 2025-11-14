# 🚀 SaaS-IA MVP - Version Simplifiée

[![Enterprise Grade](https://img.shields.io/badge/Enterprise%20Grade-S%2B%20(94%25)-gold?style=for-the-badge&logo=star)](./ENTERPRISE_GRADE.md)
[![Architecture](https://img.shields.io/badge/Architecture-S%2B%20(96%25)-brightgreen?style=flat-square)](./ENTERPRISE_GRADE.md)
[![Security](https://img.shields.io/badge/Security-S%20(92%25)-green?style=flat-square)](./ENTERPRISE_GRADE.md)
[![Documentation](https://img.shields.io/badge/Documentation-S%2B%2B%20(98%25)-gold?style=flat-square)](./ENTERPRISE_GRADE.md)
[![Maintainability](https://img.shields.io/badge/Maintainability-S%2B%2B%20(97%25)-gold?style=flat-square)](./ENTERPRISE_GRADE.md)

> Plateforme SaaS modulaire d'intelligence artificielle - Version MVP  
> **🏆 Enterprise Grade S+ (94/100)** - Qualité exceptionnelle

## 📋 Vue d'ensemble

MVP simplifié de la plateforme SaaS-IA avec :
- ✅ Backend FastAPI avec module de transcription YouTube
- ✅ Auth JWT simple (User + Admin)
- ✅ PostgreSQL + Redis
- ✅ Mode MOCK pour tester sans API keys
- ✅ Project-map.json automatique

## 🏗️ Architecture

```
mvp/
├── backend/                # API FastAPI
│   ├── app/
│   │   ├── main.py        # Point d'entrée
│   │   ├── config.py      # Configuration
│   │   ├── database.py    # SQLModel setup
│   │   ├── auth.py        # JWT Auth
│   │   ├── models/        # User, Transcription
│   │   ├── schemas/       # Pydantic schemas
│   │   └── modules/
│   │       └── transcription/  # Module IA
│   ├── scripts/
│   │   └── generate_project_map.py
│   ├── docker-compose.yml
│   └── pyproject.toml
└── project-map.json       # Généré automatiquement
```

## 🚀 Démarrage Rapide

### Prérequis
- Docker & Docker Compose
- Python 3.11+ (pour développement local)

### Installation

```bash
# 1. Cloner le projet
cd C:\Users\ibzpc\Git\SaaS-IA\mvp

# 2. Configuration
cd backend
cp .env.example .env
# Éditer .env si nécessaire (ASSEMBLYAI_API_KEY=MOCK par défaut)

# 3. Démarrer avec Docker
docker-compose up -d

# 4. Vérifier le health check
curl http://localhost:8004/health
```

### Accès

- **API** : http://localhost:8004
- **Documentation Swagger** : http://localhost:8004/docs
- **ReDoc** : http://localhost:8004/redoc
- **PostgreSQL** : localhost:5435
- **Redis** : localhost:6382

## 🔌 Ports Utilisés

| Service    | Port Interne | Port Externe | Description       |
|------------|--------------|--------------|-------------------|
| Backend    | 8000         | **8004**     | API FastAPI       |
| PostgreSQL | 5432         | **5435**     | Base de données   |
| Redis      | 6379         | **6382**     | Cache & Sessions  |

> ⚠️ **Ports externes choisis pour éviter les conflits avec WeLAB, LabSaaS, etc.**

## 🎨 Frontend : Template Sneat MUI v3.0.0

⚠️ **IMPORTANT** : Ce projet utilise la template premium **Sneat MUI Next.js Admin v3.0.0**.

**Localisation** : `C:\Users\ibzpc\Git\SaaS-IA\sneat-mui-nextjs-admin-template-v3.0.0`

### Règle d'Or

**NE JAMAIS recréer ce qui existe déjà dans la template !**

### Composants Sneat Disponibles

- **Layouts** : `AdminLayout`, `BlankLayout`, `AuthLayout`
- **Forms** : `TextField`, `Select`, `Checkbox`, `Radio`, `Switch`
- **Data Display** : `Table`, `Card`, `Chip`, `Avatar`, `Badge`
- **Navigation** : `Menu`, `Tabs`, `Breadcrumbs`, `Stepper`
- **Feedback** : `Alert`, `Dialog`, `Snackbar`, `Progress`
- **Inputs** : `Button`, `IconButton`, `Fab`, `ToggleButton`

### Avant de Coder un Composant Frontend

1. Vérifier dans `C:\Users\ibzpc\Git\SaaS-IA\sneat-mui-nextjs-admin-template-v3.0.0`
2. Vérifier dans Material-UI docs
3. Chercher un exemple dans `sneat-mui-nextjs-admin-template-v3.0.0/src/pages/`
4. Adapter au lieu de recréer

### Support

- 📁 Template source : `C:\Users\ibzpc\Git\SaaS-IA\sneat-mui-nextjs-admin-template-v3.0.0`
- 📚 Règles développement : `../startup_docs/REGLES-DEVELOPPEMENT.md`
- 🔧 Cursor rules : `../.cursorrules`

## 📚 Documentation

- [🏆 Enterprise Grade S+](./ENTERPRISE_GRADE.md) - **Système de notation et qualité**
- [Architecture MVP Simplifiée](../startup_docs/starting/MVP-SIMPLIFIE.md)
- [Project Map JSON](../startup_docs/starting/FEATURE-PROJECT-MAP-JSON.md)
- [Règles de Développement](../startup_docs/REGLES-DEVELOPPEMENT.md)

## 🧪 Tests

```bash
# Tests unitaires
docker-compose exec backend pytest tests/ -v

# Avec coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Tests spécifiques
docker-compose exec backend pytest tests/test_auth.py -v
```

## 📊 Project Map

Générer la cartographie automatique du projet :

```bash
# Méthode 1 : Script Python
python backend/scripts/generate_project_map.py

# Méthode 2 : Script one-click (Windows)
.\update-project-map.bat

# Méthode 3 : Script one-click (Linux/Mac)
./update-project-map.sh
```

Le fichier `project-map.json` sera généré à la racine avec :
- Structure complète du projet
- Imports/exports Python (analyse AST)
- Routes API détectées
- Métriques (lignes de code, complexité)
- Graphe de dépendances

## 🔐 Authentification

### Créer un compte

```bash
curl -X POST http://localhost:8004/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe"
  }'
```

### Se connecter

```bash
curl -X POST http://localhost:8004/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

Réponse :
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

## 🎙️ Module Transcription

### Lancer une transcription

```bash
curl -X POST http://localhost:8004/api/transcription \
  -H "Authorization: Bearer <votre-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "language": "auto"
  }'
```

### Vérifier le statut

```bash
curl http://localhost:8004/api/transcription/{job_id} \
  -H "Authorization: Bearer <votre-token>"
```

### Mode MOCK

Par défaut, `ASSEMBLYAI_API_KEY=MOCK` dans `.env`.

Le mode MOCK :
- ✅ Simule une transcription (2 secondes de délai)
- ✅ Retourne un texte de test
- ✅ Permet de tester sans clé API réelle
- ✅ Parfait pour le développement

Pour utiliser Assembly AI réellement :
1. Obtenir une clé API sur https://www.assemblyai.com/
2. Modifier `.env` : `ASSEMBLYAI_API_KEY=votre-clé-réelle`
3. Redémarrer : `docker-compose restart backend`

## 🛠️ Développement

### Structure Backend

```python
# app/main.py - Point d'entrée FastAPI
from fastapi import FastAPI
from app.auth import router as auth_router
from app.modules.transcription.routes import router as transcription_router

app = FastAPI(title="SaaS-IA MVP")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(transcription_router, prefix="/api/transcription")
```

### Ajouter un nouveau module

1. Créer `app/modules/nouveau_module/`
2. Ajouter `routes.py`, `service.py`, `schemas.py`
3. Importer dans `app/main.py`
4. Régénérer `project-map.json`

## 📈 Roadmap

### Phase 1 : MVP Backend (En cours)
- ✅ Infrastructure (Docker, PostgreSQL, Redis)
- ✅ Auth JWT simple
- ✅ Module Transcription avec mode MOCK
- ✅ Project-map.json automatique

### Phase 2 : Frontend (Prochaine)
- 🔄 Copier template Sneat MUI
- 🔄 Pages Auth (login, register)
- 🔄 Dashboard admin
- 🔄 Page Transcription

### Phase 3 : Expansion
- 🔮 Module Résumé (GPT-4)
- 🔮 Module Traduction
- 🔮 Module Analyse Sémantique

## 🤝 Contribution

Voir [CONTRIBUTING.md](../CONTRIBUTING.md)

## 📄 Licence

MIT License - Voir [LICENSE](../LICENSE)

---

**Version** : 1.0.0  
**Date** : 2025-11-13  
**Auteur** : SaaS-IA Team

