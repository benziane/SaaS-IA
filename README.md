# SaaS-IA - Plateforme SaaS d'Orchestration IA

[![CI](https://github.com/benziane/SaaS-IA/workflows/CI/badge.svg)](https://github.com/benziane/SaaS-IA/actions)
[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![TypeScript 5.9+](https://img.shields.io/badge/TypeScript-5.9+-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Plateforme modulaire d'intelligence artificielle permettant de transcrire, analyser, comparer et orchestrer des services IA via une interface unifiee.

## Fonctionnalites

| Module | Description |
|--------|-------------|
| **Transcription** | YouTube, upload fichier, enregistrement micro (AssemblyAI + yt-dlp) |
| **Chat IA** | Chat contextuel avec historique, SSE streaming, contexte transcription |
| **Compare** | Comparaison multi-modele en parallele (Gemini, Claude, Groq) avec votes |
| **Pipelines** | Builder de pipelines IA : chainer transcription, resume, traduction, export |
| **Knowledge Base** | Upload documents, chunking, recherche semantique, RAG (question/reponse) |
| **Billing** | Plans Free/Pro/Enterprise, quotas, Stripe Checkout + webhooks |
| **Workspaces** | Collaboration : workspaces partages, membres, items partages, commentaires |
| **API Publique** | API v1 avec cles API (SHA-256), endpoints REST authentifies |

## Stack technique

**Backend** : FastAPI 0.135, Python 3.13, SQLModel, PostgreSQL 16, Redis 7, Celery, Stripe

**Frontend** : Next.js 15.5, React 18.3, TypeScript 5.9, Material-UI 6, TanStack Query 5

**Infrastructure** : Docker Compose (backend, worker, flower, PostgreSQL, Redis), GitHub Actions CI/CD

**AI Providers** : Gemini Flash, Claude Sonnet, Groq Llama 70B (AI Router avec classification + selection)

## Quick Start

```bash
# Cloner
git clone https://github.com/benziane/SaaS-IA.git
cd SaaS-IA/mvp

# Backend
cp backend/.env.example backend/.env
# Editer .env avec vos cles API
docker compose up -d

# Frontend
cd frontend
npm install
npm run dev
```

Backend : http://localhost:8004 | Frontend : http://localhost:3002 | Flower : http://localhost:5555

## Documentation

| Document | Description |
|----------|-------------|
| [ROADMAP.md](mvp/ROADMAP.md) | Roadmap complete avec statut de chaque feature |
| [ARCHITECTURE.md](mvp/docs/ARCHITECTURE.md) | Architecture globale, diagrammes, flux de donnees |
| [DEPLOYMENT.md](mvp/docs/DEPLOYMENT.md) | Guide de deploiement production |
| [API_REFERENCE.md](mvp/docs/API_REFERENCE.md) | Reference API complete (45+ endpoints) |
| [Sprint docs](mvp/docs/) | Documentation technique par sprint |

## Tests

```bash
cd mvp/backend
pytest                           # 211 tests (179 unit + 32 integration)
pytest tests/test_integration.py # Integration tests only
```

## Structure

```
mvp/
├── backend/
│   ├── app/
│   │   ├── ai_assistant/       # AI Router + Providers
│   │   ├── models/             # SQLModel (13 tables)
│   │   ├── modules/            # 7 plugin modules auto-decouverts
│   │   │   ├── transcription/
│   │   │   ├── conversation/
│   │   │   ├── billing/
│   │   │   ├── compare/
│   │   │   ├── pipelines/
│   │   │   ├── knowledge/
│   │   │   ├── api_keys/
│   │   │   └── workspaces/
│   │   ├── celery_app.py       # Celery workers
│   │   └── main.py             # FastAPI app
│   ├── alembic/                # 7 migrations
│   └── tests/                  # 211 tests
├── frontend/
│   ├── src/
│   │   ├── app/(dashboard)/    # 10 pages
│   │   ├── features/           # 8 feature modules
│   │   └── components/
│   └── package.json
└── docker-compose.yml          # 5 services
```

## Licence

MIT
