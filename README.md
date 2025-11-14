# 🚀 SaaS-IA - Plateforme SaaS Multi-Modules IA

[![Enterprise Grade](https://img.shields.io/badge/Enterprise%20Grade-S%2B%20(94%25)-gold?style=for-the-badge&logo=star)](./mvp/ENTERPRISE_GRADE.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![CI](https://github.com/benziane/SaaS-IA/workflows/CI/badge.svg)](https://github.com/benziane/SaaS-IA/actions)

> Plateforme SaaS modulaire et évolutive intégrant des services d'Intelligence Artificielle  
> **🏆 MVP Backend : Enterprise Grade S+ (94/100)** - Qualité exceptionnelle

## 📋 Table des matières

- [À propos](#à-propos)
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Documentation](#documentation)
- [Contribution](#contribution)
- [Licence](#licence)

## 🎯 À propos

**SaaS-IA** est une plateforme SaaS moderne conçue pour héberger plusieurs modules d'Intelligence Artificielle. Le projet suit une architecture modulaire permettant d'ajouter facilement de nouveaux services IA.

### Modules disponibles

#### 📹 v0 - Module de Transcription YouTube
- Transcription automatique de vidéos YouTube
- Support multilingue (détection automatique)
- Correction linguistique avancée
- Interface web moderne et intuitive
- API REST complète

[Voir la documentation complète du module v0](./v0/README.md)

## ✨ Fonctionnalités

### 🏗️ Architecture
- ✅ Architecture modulaire et évolutive
- ✅ Microservices avec Docker
- ✅ API REST avec FastAPI
- ✅ Frontend moderne avec React/Next.js
- ✅ Base de données PostgreSQL
- ✅ Cache Redis pour les performances

### 🔒 Sécurité
- ✅ Validation des entrées (Pydantic/Zod)
- ✅ Gestion sécurisée des secrets
- ✅ CORS configuré
- ✅ Health checks

### 📊 Observabilité
- ✅ Logging structuré
- ✅ Métriques Prometheus
- ✅ Monitoring avec Grafana
- ✅ Traces distribuées

### 🧪 Qualité
- ✅ Tests unitaires et d'intégration
- ✅ CI/CD avec GitHub Actions
- ✅ Analyse de code (CodeQL)
- ✅ Scan de sécurité (Trivy)
- ✅ Dependabot pour les dépendances

## 🏗️ Architecture

```
SaaS-IA/
├── v0/                      # Module de transcription YouTube
│   ├── backend/            # API FastAPI
│   ├── frontend/           # Application Next.js
│   ├── docs/               # Documentation technique
│   └── docker-compose.yml  # Orchestration Docker
├── startup_docs/           # Documentation de démarrage
│   ├── Analyse du projet Lab-SaaS - Claude/
│   ├── Analyse du projet Lab-SaaS - Manus/
│   └── starting/           # Guides d'architecture
├── .github/                # Configuration GitHub
│   ├── workflows/          # CI/CD
│   └── ISSUE_TEMPLATE/     # Templates d'issues
├── CONTRIBUTING.md         # Guide de contribution
├── CODE_OF_CONDUCT.md      # Code de conduite
└── LICENSE                 # Licence MIT
```

### Stack Technologique

**Backend:**
- Python 3.11+
- FastAPI 0.104+
- SQLModel (SQLAlchemy 2.0)
- PostgreSQL 15+
- Redis 7+
- Pydantic pour la validation

**Frontend:**
- React 18+
- Next.js 14+
- TypeScript 5+
- TailwindCSS 3+
- TanStack Query (React Query)

**Infrastructure:**
- Docker & Docker Compose
- GitHub Actions (CI/CD)
- Prometheus & Grafana
- Nginx (reverse proxy)

## 🚀 Installation

### Prérequis

- Docker 24+ et Docker Compose
- Git
- (Optionnel) Node.js 18+ et Python 3.11+ pour le développement local

### Installation rapide avec Docker

```bash
# 1. Cloner le repository
git clone https://github.com/benziane/SaaS-IA.git
cd SaaS-IA

# 2. Lancer le module v0
cd v0
docker-compose up -d

# 3. Accéder aux services
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Docs API: http://localhost:8000/docs
```

### Installation pour le développement

Voir les guides détaillés :
- [Installation Backend](./v0/backend/README.md)
- [Installation Frontend](./v0/frontend/README.md)

## 📖 Utilisation

### Module v0 - Transcription YouTube

#### Via l'interface web

1. Ouvrez http://localhost:3000
2. Collez une URL YouTube
3. Sélectionnez la langue (ou laissez sur "Auto")
4. Cliquez sur "Lancer la transcription"
5. Suivez la progression en temps réel

#### Via l'API

```bash
# Créer une transcription
curl -X POST "http://localhost:8000/api/v1/transcriptions/" \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "language": "auto"
  }'

# Récupérer une transcription
curl "http://localhost:8000/api/v1/transcriptions/1"
```

[Voir la documentation complète de l'API](./v0/docs/API.md)

## 📚 Documentation

### Documentation générale
- [Guide de contribution](./CONTRIBUTING.md)
- [Code de conduite](./CODE_OF_CONDUCT.md)
- [Licence](./LICENSE)

### Documentation technique
- [Architecture globale](./startup_docs/starting/ARCHITECTURE-SAAS-IA-SCALABLE-V2.md)
- [Guide d'implémentation modulaire](./startup_docs/starting/GUIDE-IMPLEMENTATION-MODULAIRE.md)
- [Templates de code](./startup_docs/starting/TEMPLATES-CODE-MODULES.md)

### Documentation des modules
- [Module v0 - Transcription YouTube](./v0/README.md)
  - [API Documentation](./v0/docs/API.md)
  - [Architecture](./v0/docs/ARCHITECTURE.md)
  - [Spécifications](./v0/docs/specification_complete_saas_ia.md)

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez consulter notre [Guide de contribution](./CONTRIBUTING.md) pour plus de détails.

### Comment contribuer

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/amazing-feature`)
3. Commitez vos changements (`git commit -m 'feat: add amazing feature'`)
4. Pushez vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request

### Contributeurs

Merci à tous les contributeurs qui ont participé à ce projet !

## 🛣️ Roadmap

### Version actuelle (v0.1.0)
- ✅ Module de transcription YouTube
- ✅ Interface web moderne
- ✅ API REST complète
- ✅ Docker Compose

### Prochaines versions

#### v0.2.0
- 🔲 Authentification utilisateur (JWT)
- 🔲 Dashboard utilisateur
- 🔲 Gestion des quotas

#### v1.0.0
- 🔲 Module de résumé automatique
- 🔲 Module d'analyse sémantique
- 🔲 Module de traduction
- 🔲 Export multi-formats (PDF, DOCX, SRT)

#### v2.0.0
- 🔲 Module de génération de contenu
- 🔲 Module d'analyse d'images
- 🔲 API webhooks
- 🔲 Intégrations tierces

[Voir la roadmap complète](https://github.com/benziane/SaaS-IA/projects)

## 📊 Statistiques

![GitHub stars](https://img.shields.io/github/stars/benziane/SaaS-IA?style=social)
![GitHub forks](https://img.shields.io/github/forks/benziane/SaaS-IA?style=social)
![GitHub issues](https://img.shields.io/github/issues/benziane/SaaS-IA)
![GitHub pull requests](https://img.shields.io/github/issues-pr/benziane/SaaS-IA)

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](./LICENSE) pour plus de détails.

## 🙏 Remerciements

- **OpenAI Whisper** pour le modèle de transcription
- **FastAPI** pour le framework backend
- **Next.js** pour le framework frontend
- **yt-dlp** pour l'extraction YouTube
- La communauté open source

## 📧 Contact & Support

- 🐛 [Signaler un bug](https://github.com/benziane/SaaS-IA/issues/new?template=bug_report.md)
- ✨ [Proposer une fonctionnalité](https://github.com/benziane/SaaS-IA/issues/new?template=feature_request.md)
- 💬 [Discussions](https://github.com/benziane/SaaS-IA/discussions)
- 📖 [Documentation](./v0/docs/)

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=benziane/SaaS-IA&type=Date)](https://star-history.com/#benziane/SaaS-IA&Date)

---

**Développé avec ❤️ pour rendre l'IA accessible à tous**

[⬆ Retour en haut](#-saas-ia---plateforme-saas-multi-modules-ia)

