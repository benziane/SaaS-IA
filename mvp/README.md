# SaaS-IA MVP

Plateforme SaaS modulaire d'intelligence artificielle - Version MVP complete.

## Services Docker

| Service | Port | Description |
|---------|------|-------------|
| backend | 8004 | FastAPI API |
| worker | - | Celery worker (transcriptions async) |
| flower | 5555 | Monitoring Celery |
| postgres | 5435 | PostgreSQL 16 |
| redis | 6382 | Redis 7 (cache, broker) |

## Demarrage rapide

```bash
# 1. Configurer l'environnement
cp backend/.env.example backend/.env
# Editer backend/.env avec vos cles

# 2. Lancer les services
docker compose up -d

# 3. Frontend (developpement)
cd frontend && npm install && npm run dev
```

## Variables d'environnement requises

```env
# Obligatoire
SECRET_KEY=votre-cle-secrete-forte
DATABASE_URL=postgresql://user:pass@localhost:5435/saas_ia

# AI Providers (au moins un)
GEMINI_API_KEY=...
CLAUDE_API_KEY=...
GROQ_API_KEY=...

# Transcription (ou MOCK pour test)
ASSEMBLYAI_API_KEY=MOCK

# Stripe (optionnel, pour les paiements)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO_MONTHLY=price_...
```

## Pages frontend

| Route | Description | Phase |
|-------|-------------|-------|
| /dashboard | Tableau de bord avec stats | Core |
| /transcription | Transcription multi-source | Core |
| /chat | Chat IA contextuel | Core |
| /compare | Comparaison multi-modele | Core |
| /pipelines | Pipeline builder IA | Core |
| /knowledge | Knowledge base + RAG | Core |
| /billing | Plans, quotas, Stripe | Core |
| /workspaces | Collaboration | Core |
| /api-docs | Gestion cles API + documentation | Core |
| /modules | Vue admin des modules | Core |
| /profile | Profil utilisateur | Core |
| /content-studio | Studio de contenu multi-format (blog, Twitter, LinkedIn, newsletter...) | P0 |
| /workflows | Automatisations IA no-code avec triggers, actions et templates | P0 |
| /crews | Equipes d'agents IA collaboratifs avec roles specialises | P1 |
| /voice | Clonage vocal, TTS, doublage automatique | P1 |
| /realtime | Conversations IA en temps reel (voix, vision, meeting) | P1 |
| /security | Securite IA : PII detection, guardrails, audit trail, compliance | P1 |
| /images | Studio d'images IA : generation, thumbnails, 10 styles, galerie | P2 |
| /data | Analyste de donnees IA : upload CSV/JSON, questions NL, charts, insights | P2 |
| /video-studio | Studio video IA : text-to-video, clips, avatars parlants, explainers | P2 |
| /fine-tuning | Fine-tuning studio : datasets depuis la plateforme, training, evaluation | P3 |
| /pipeline-builder | Visual DAG builder : canvas nodes/edges, validation, save as workflow | Final |
| /monitoring | LLM observability : KPI dashboard, provider perf, traces, cost analytics | Final |
| /search | Recherche universelle cross-module + "Ask AI" (cross-module RAG) | Final |
| /memory | Memoire IA persistante : preferences, facts, auto-extraction, RGPD forget | Final |

## Modules backend (auto-decouverts)

42 modules auto-decouverts via `manifest.json` + `ModuleRegistry` :

### Modules Core

| Module | Prefix | Endpoints |
|--------|--------|-----------|
| transcription | /api/transcription | 7 |
| conversation | /api/conversations | 5 |
| billing | /api/billing | 5 |
| compare | /api/compare | 3 |
| pipelines | /api/pipelines | 8 |
| knowledge | /api/knowledge | 8 | Hybrid search (pgvector + TF-IDF), RAG, reindex embeddings |
| api_keys | /api/keys | 3 |
| workspaces | /api/workspaces | 12 |
| agents | /api/agents | 4 |
| sentiment | /api/sentiment | 2 |
| web_crawler | /api/crawler | 4 |
| cost_tracker | /api/costs | 3 |
| youtube_transcription | /api/youtube | 13 | YouTube transcript extraction, multi-language, chapter detection, summary |
| Public API v1 | /v1 | 3 |

### Modules P0 - Content & Automation (Sprint 7)

| Module | Prefix | Endpoints | Description |
|--------|--------|-----------|-------------|
| content_studio | /api/content-studio | 8 | Generation multi-format : blog, Twitter thread, LinkedIn, newsletter, Instagram carousel, YouTube description, SEO meta, press release, email campaign, podcast notes |
| ai_workflows | /api/workflows | 9 | Automatisations no-code : trigger/action graph engine, 5 templates pre-construits, 13 types d'actions, webhook externe |

### Modules P1 - Intelligence & Safety (Sprint 7)

| Module | Prefix | Endpoints | Description |
|--------|--------|-----------|-------------|
| multi_agent_crew | /api/crews | 9 | Equipes d'agents collaboratifs (Researcher, Writer, Reviewer, Analyst...), 4 templates, execution sequentielle avec inter-agent communication |
| voice_clone | /api/voice | 8 | Clonage vocal, TTS (OpenAI + ElevenLabs), doublage multilingue automatique, 10 voix built-in |
| realtime_ai | /api/realtime | 7 | Sessions IA temps reel (voice, vision, meeting), RAG integre, transcript + resume auto |
| security_guardian | /api/security | 8 | PII detection (email, phone, SSN, IBAN...), prompt injection detection, content safety IA, auto-redaction, audit trail, guardrail rules configurable |

### Modules P2 - Media & Intelligence (Sprint 8)

| Module | Prefix | Endpoints | Description |
|--------|--------|-----------|-------------|
| image_gen | /api/images | 9 | Generation d'images IA (10 styles), thumbnails YouTube auto, bulk generation, projets |
| data_analyst | /api/data | 8 | Upload CSV/JSON/Excel, questions en langage naturel, auto-analyse, charts, insights, rapports |
| video_gen | /api/videos | 9 | Text-to-video, clips highlights, avatars parlants, explainers, shorts, projets video |

### Module P3 - Custom Models (Sprint 9)

| Module | Prefix | Endpoints | Description |
|--------|--------|-----------|-------------|
| fine_tuning | /api/fine-tuning | 13 | Datasets depuis transcriptions/conversations/documents, training LoRA (Llama/Mistral/Gemma), evaluation, deploiement |

### Modules Plateforme - Monitoring, Search, Memory (Sprint 10-Final)

| Module | Prefix | Endpoints | Description |
|--------|--------|-----------|-------------|
| ai_monitoring | /api/monitoring | 3 | Dashboard LLM observability (Langfuse-style) : KPI, provider comparison, traces, cost analytics |
| unified_search | /api/search | 2 | Recherche universelle cross-module (transcriptions, KB, content, conversations) + RAG answer synthesis |
| ai_memory | /api/memory | 5 | Memoire persistante Mem0-style : preferences, facts, context injection, auto-extraction IA, RGPD forget |

### Modules Enterprise

| Module | Prefix | Endpoints | Description |
|--------|--------|-----------|-------------|
| tenants | /api/tenants | 5 | Multi-tenant isolation, PostgreSQL RLS, contextvars middleware |
| audit | /api/audit | 4 | Immutable hash chain, compliance-grade audit trail |
| feature_flags | /api/feature-flags | 5 | Kill switches, % rollout, Redis-backed |
| secrets | /api/secrets | 4 | Rotation tracking, alerts, health score |
| auth_guards | /api/auth-guards | 3 | Auth guards, policy enforcement, access control |

### Integrations open-source (18 libs integrees)

| Lib | Module | Impact |
|-----|--------|--------|
| pgvector + sentence-transformers | knowledge | Recherche hybride RAG (vector + TF-IDF) |
| litellm | ai_assistant | Proxy unifie multi-LLM, token/cost exact |
| presidio | security_guardian | PII detection enterprise (30+ types) |
| faster-whisper + pyannote | transcription | Transcription locale gratuite + diarization |
| duckdb + ydata-profiling | data_analyst | Analytics SQL 100x + auto-profiling |
| Coqui TTS | voice_clone | TTS open-source multi-langue + voice cloning |
| NeMo-Guardrails | security_guardian | Injection detection NLP avancee (10 patterns) |
| networkx | ai_workflows | Validation DAG (cycles, topo sort, connectivity) |
| Eval engine (promptfoo pattern) | compare | LLM-as-judge auto + ELO ranking |
| ReAct engine (langgraph pattern) | agents | Agent iteratif Think-Act-Observe-Reflect |
| Memory service (Zep pattern) | conversation | Memoire hierarchique + fact extraction |

### Connectivite inter-modules

| Systeme | Modules connectes | Description |
|---------|-------------------|-------------|
| **Agent Executor** | ~84 actions | Les agents autonomes appellent n'importe quel module |
| **Pipeline Steps** | 34 step types | Les pipelines chainent les operations sequentiellement |
| **Workflow Actions** | 35 types | Les workflows orchestrent les modules via DAG parallele |

### Moteur de recherche Knowledge Base

| Mode | Dependance | Description |
|------|-----------|-------------|
| TF-IDF | Aucune (built-in) | Cosine similarity sur term frequency (legacy, toujours disponible) |
| Vector | pgvector + sentence-transformers | Recherche semantique via embeddings 384 dim + index HNSW |
| Hybrid | pgvector + sentence-transformers | Reciprocal Rank Fusion (70% vector + 30% TF-IDF) |
| Auto | Auto-detecte | `search()` utilise hybrid si dispo, sinon TF-IDF |

## Tests

```bash
cd backend
pytest                    # 211 tests
pytest -k integration     # 32 tests d'integration
pytest -k billing         # Tests module billing
```

## Documentation

- [../CLAUDE.md](../CLAUDE.md) - Gouvernance projet et regles critiques
- [ROADMAP.md](ROADMAP.md) - Roadmap complete, changelog, endpoints API, connectivite inter-modules
- [TECH_AUDIT_ROADMAP.md](TECH_AUDIT_ROADMAP.md) - Audit open-source : libs a integrer par module, priorites, statut de suivi
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Architecture technique
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Guide deploiement
- [docs/API_REFERENCE.md](docs/API_REFERENCE.md) - Reference API
- [docs/SPRINT*.md](docs/) - Documentation par sprint
