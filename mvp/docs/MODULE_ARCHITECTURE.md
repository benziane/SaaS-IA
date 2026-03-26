# SaaS-IA -- Architecture des Modules

> Document de reference permanent. Decrit COMMENT chaque module a ete construit,
> sa source d'inspiration, et son approche d'integration.
>
> Derniere mise a jour : 2026-03-26 | v4.3.0 | 40 modules

---

## Vue d'ensemble

La plateforme SaaS-IA contient **40 modules backend** auto-decouverts par le `ModuleRegistry`.
Chaque module suit un des 3 patterns d'integration :

| Pattern | Description | Nombre |
|---------|-------------|--------|
| **A. Lib Python wrappee** | On installe un package pip et on appelle son API Python dans notre service | 12 modules |
| **B. Developpe from scratch** | Code 100% maison, inspire par les concepts d'un repo/produit de reference | 26 modules |
| **C. CLI wrappee** | On appelle un outil en ligne de commande via `asyncio.create_subprocess_exec` | 2 modules |

Certains modules combinent plusieurs patterns (note A+B ou B+C dans les tableaux).

---

## Structure standard d'un module

```
mvp/backend/app/modules/<module_name>/
  __init__.py
  manifest.json    # auto-discovery par ModuleRegistry
  schemas.py       # Pydantic request/response
  service.py       # Business logic (+ pattern HAS_XXX pour libs optionnelles)
  routes.py        # FastAPI APIRouter
```

Les modeles DB sont dans `mvp/backend/app/models/<module_name>.py`.
Les migrations Alembic dans `mvp/backend/alembic/versions/`.

---

## Modules detailles par tier

### Core (12 modules)

| Module | Pattern | Source d'inspiration | Libs utilisees | Fallback | Pourquoi cette approche | Alternative possible |
|--------|---------|---------------------|----------------|----------|------------------------|---------------------|
| **transcription** | A+B | AssemblyAI API + OpenAI Whisper | `faster-whisper`, `pyannote.audio`, `yt-dlp`, `assemblyai` | AssemblyAI payant si Whisper absent | faster-whisper donne du local gratuit avec diarization pyannote | whisperx (meilleure diarization alignee) |
| **conversation** | B | ChatGPT conversation patterns | Aucune lib specifique (utilise `AIAssistantService`) | LLM direct | Logique de conversation simple, pas besoin de framework | langchain (conversation memory chains) |
| **knowledge** | A | pgvector docs + sentence-transformers | `pgvector`, `sentence-transformers`, `scikit-learn` (TF-IDF) | TF-IDF via sklearn | Hybrid search (vector + BM25/TF-IDF) donne les meilleurs resultats RAG | chromadb, qdrant, weaviate |
| **compare** | B | Chatbot Arena (lmsys.org) | Aucune | LLM direct | Comparaison side-by-side simple, pas besoin de framework d'eval | promptfoo (eval framework) |
| **pipelines** | B | Prefect / Airflow concepts | Aucune | - | Chaining sequentiel leger sans la complexite d'un orchestrateur externe | prefect, temporal |
| **agents** | B | LangGraph / ReAct pattern (Yao 2022) | Aucune | - | Implementation maison du loop plan-execute-observe pour controle total | langgraph (10K+ stars) |
| **sentiment** | A | cardiffnlp/twitter-roberta-base-sentiment | `transformers` (HuggingFace) | LLM analysis via AIAssistantService | Modele specialise sentiment donne F1 superieur aux LLM generiques | vaderSentiment, textblob |
| **web_crawler** | A+C | Crawl4AI (GitHub) + Jina Reader API | `crawl4ai`, `httpx` (pour Jina) | Jina Reader si crawl4ai absent | Deux approches complementaires : JS rendering (crawl4ai) + clean markdown (Jina) | firecrawl, spider, scrapy |
| **workspaces** | B | Notion / Slack collaboration model | Aucune | - | CRUD workspaces avec partage, pas besoin de CRDT pour le MVP | yjs (CRDT real-time collab) |
| **billing** | B | Stripe Billing documentation | `stripe` | - | Integration Stripe directe, la plus standard du marche | paddle, lemonsqueezy |
| **api_keys** | B | Stripe API keys pattern (sk_live / sk_test) | Aucune (SHA-256 stdlib `hashlib`) | - | Pattern simple et eprouve, zero dependance | - |
| **cost_tracker** | A | FinOps patterns + LiteLLM pricing | `litellm` | Pricing manuel (table de prix statique) | litellm connait les prix de 100+ modeles LLM | - |

### P0 - Content & Automation (2 modules)

| Module | Pattern | Source d'inspiration | Libs utilisees | Fallback | Pourquoi cette approche | Alternative possible |
|--------|---------|---------------------|----------------|----------|------------------------|---------------------|
| **content_studio** | A+B | Repurpose.io + Copy.ai | `textstat` | Word count basique | 10 formats de contenu generes par LLM, textstat pour la lisibilite | - |
| **ai_workflows** | A+B | n8n (40K stars) / Zapier / Temporal | `networkx` | Kahn's algorithm maison | DAG engine avec validation de cycles via networkx, 19 actions, 5 templates | temporal, inngest |

### P1 - Intelligence & Safety (4 modules)

| Module | Pattern | Source d'inspiration | Libs utilisees | Fallback | Pourquoi cette approche | Alternative possible |
|--------|---------|---------------------|----------------|----------|------------------------|---------------------|
| **multi_agent_crew** | B | CrewAI (20K+ stars) | Aucune | - | Implementation maison du pattern multi-agent (9 roles, 4 templates) pour eviter la dependance CrewAI | crewai pip package |
| **voice_clone** | A | OpenAI TTS API + Coqui TTS (GitHub) | `TTS` (Coqui), `openai` | OpenAI TTS si Coqui absent, mock si aucun | Coqui = open-source gratuit, OpenAI = qualite production | bark, fish-speech, styletts2 |
| **realtime_ai** | A+B | LiveKit (GitHub) + OpenAI Realtime API | `livekit-server-sdk` | Text-based sessions (WebSocket simple) | LiveKit gere le WebRTC, on ajoute la couche AI par-dessus | livekit-agents |
| **security_guardian** | A | Presidio (Microsoft, 3K stars) + NeMo Guardrails (NVIDIA) | `presidio-analyzer`, `nemoguardrails` | Regex patterns pour PII + injection detection | Presidio = PII detection enterprise, NeMo = guardrails IA | llm-guard, rebuff |

### P2 - Media & Intelligence (3 modules)

| Module | Pattern | Source d'inspiration | Libs utilisees | Fallback | Pourquoi cette approche | Alternative possible |
|--------|---------|---------------------|----------------|----------|------------------------|---------------------|
| **image_gen** | A+B | DALL-E / Stability AI API patterns | `realesrgan` | Pas d'upscaling (generation directe seulement) | 10 styles generes par API IA, Real-ESRGAN pour upscale local | comfyui, automatic1111 |
| **data_analyst** | A | PandasAI + Code Interpreter (OpenAI) | `duckdb`, `ydata-profiling` | Pandas parser basique | DuckDB = SQL analytique rapide en-memoire, ydata = profiling automatique | pandasai, lida (Microsoft) |
| **video_gen** | A+B | Remotion + HeyGen concepts | `ffmpeg-python` | Mock placeholders | ffmpeg = standard industrie pour le traitement video, 6 types de video | moviepy, remotion |

### P3 - Custom Models (1 module)

| Module | Pattern | Source d'inspiration | Libs utilisees | Fallback | Pourquoi cette approche | Alternative possible |
|--------|---------|---------------------|----------------|----------|------------------------|---------------------|
| **fine_tuning** | A | Unsloth (GitHub, 20K stars) + lm-evaluation-harness (EleutherAI) | `unsloth`, `lm-eval` | Mock training + mock evaluation | Unsloth = fine-tuning 2x plus rapide avec 60% moins de RAM | axolotl, llama-factory |

### Platform - Monitoring, Search, Memory (3 modules)

| Module | Pattern | Source d'inspiration | Libs utilisees | Fallback | Pourquoi cette approche | Alternative possible |
|--------|---------|---------------------|----------------|----------|------------------------|---------------------|
| **ai_monitoring** | A | Langfuse (8K+ stars) | `langfuse` | Prometheus seul | Langfuse = observabilite LLM specialisee (traces, couts, latence) | helicone, phoenix (Arize) |
| **unified_search** | A | Meilisearch (45K+ stars) | `meilisearch` | PostgreSQL ILIKE (recherche basique) | Meilisearch = recherche full-text instantanee avec typo-tolerance | typesense, elasticsearch |
| **ai_memory** | A | Mem0 (25K+ stars) | `mem0ai` | DB queries directes | Mem0 = memoire persistante avec extraction automatique de faits | zep, motorhead |

### Ecosystem (4 modules)

| Module | Pattern | Source d'inspiration | Libs utilisees | Fallback | Pourquoi cette approche | Alternative possible |
|--------|---------|---------------------|----------------|----------|------------------------|---------------------|
| **social_publisher** | B+A | Buffer / Hootsuite | `tweepy` (optionnel) | Mock publish (log seulement) | Publication multi-plateforme, scheduling, analytics | python-linkedin-v2, facebook-sdk |
| **integration_hub** | B | Zapier / Nango (4K stars) | Aucune | - | 10 connecteurs, webhooks, triggers -- hub d'integration maison | nango, pipedream |
| **ai_chatbot_builder** | B | Typebot (18K stars) / Flowise (30K stars) | Aucune | - | Builder de chatbots RAG avec widget embed et multi-channel | flowise, langflow |
| **marketplace** | B | npm registry / Shopify App Store | Aucune | - | Listings, ratings, installs -- marketplace de modules IA | - |

### Content & Dev Tools (3 modules)

| Module | Pattern | Source d'inspiration | Libs utilisees | Fallback | Pourquoi cette approche | Alternative possible |
|--------|---------|---------------------|----------------|----------|------------------------|---------------------|
| **presentation_gen** | B | Slidev (30K stars) / Marp (5K stars) | Aucune (pattern `HAS_MARP`) | HTML export basique | Generation de slides par IA, 5 templates, export multi-format | reveal.js, slidev |
| **code_sandbox** | B+A | E2B (5K stars) | `docker` (optionnel) | Subprocess restreint (sans Docker) | Execution securisee de code avec isolation | e2b pip package, pyodide |
| **ai_forms** | B | Typeform / Tally | Aucune | - | Formulaires conversationnels generes par IA avec scoring | react-hook-form (frontend) |

### Tools (1 module)

| Module | Pattern | Source d'inspiration | Libs utilisees | Fallback | Pourquoi cette approche | Alternative possible |
|--------|---------|---------------------|----------------|----------|------------------------|---------------------|
| **skill_seekers** | C | skill-seekers CLI (GitHub) | `skill-seekers` (CLI) | Mock mode (donnees simulees) | Scraping de repos GitHub + packaging IA via CLI externe | - |

### New (3 modules)

| Module | Pattern | Source d'inspiration | Libs utilisees | Fallback | Pourquoi cette approche | Alternative possible |
|--------|---------|---------------------|----------------|----------|------------------------|---------------------|
| **repo_analyzer** | B+C | CodeClimate / SonarQube concepts | `git` (CLI) | Mock data | Analyse de repos via commandes git CLI + heuristiques maison | radon, pylint |
| **pdf_processor** | A | ChatPDF / unstructured patterns | `PyMuPDF`, `pdfplumber` | pdfplumber si PyMuPDF absent | Extraction de texte/tables/images depuis PDF, deux backends pour robustesse | unstructured (8K stars) |
| **audio_studio** | A+B | Descript / Audacity concepts | `pydub`, `noisereduce` | Pydub seul si noisereduce absent | Edition audio (trim, merge, noise reduction) sans interface lourde | librosa, pedalboard |

### Enterprise (4 modules)

| Module | Pattern | Source d'inspiration | Libs utilisees | Fallback | Pourquoi cette approche | Alternative possible |
|--------|---------|---------------------|----------------|----------|------------------------|---------------------|
| **tenants** | B | Stripe multi-tenant + PostgreSQL RLS docs | Aucune | - | Isolation multi-tenant par tenant_id avec middleware contextvars | django-tenants pattern |
| **audit** | B | SOC2 audit trail patterns | Aucune (SHA-256 stdlib `hashlib`) | - | Hash chain immutable pour compliance-grade audit log, zero dependance | auditlog (django), sqlalchemy-continuum |
| **feature_flags** | B | LaunchDarkly / Unleash | `redis` | In-memory dict | Kill switches + percentage rollout avec evaluation Redis-backed | unleash-client-python, flagsmith |
| **secrets** | B | HashiCorp Vault metadata patterns | Aucune | - | Rotation tracking + expiry alerts + health score, metadata seulement (pas de stockage de secrets) | python-dotenv, vault hvac |

---

## Pattern HAS_XXX (Auto-detection + Fallback)

Toutes les libs optionnelles suivent ce pattern dans le `service.py` du module :

```python
try:
    import some_lib
    HAS_SOME_LIB = True
except ImportError:
    HAS_SOME_LIB = False

class ModuleService:
    async def process(self, data):
        if HAS_SOME_LIB:
            return await self._process_with_lib(data)
        else:
            return await self._process_fallback(data)
```

**Principes** :
- Si la lib n'est pas installee, le module fonctionne quand meme avec un fallback
- Le fallback peut etre : mock, alternative plus simple, ou fonctionnalite reduite
- Zero crash, zero dependance obligatoire (sauf FastAPI core + SQLModel)
- L'upgrade est transparent : installer la lib pip suffit, le service la detecte au prochain demarrage
- Le `manifest.json` de chaque module liste ses dependances optionnelles

**Exemples concrets** :

| Module | Variable | Lib detectee | Fallback |
|--------|----------|-------------|----------|
| knowledge | `HAS_PGVECTOR` | pgvector + sentence-transformers | TF-IDF (sklearn) |
| transcription | `HAS_FASTER_WHISPER` | faster-whisper | AssemblyAI (API payante) |
| voice_clone | `HAS_COQUI_TTS` | TTS (Coqui) | OpenAI TTS (API payante) |
| security_guardian | `HAS_PRESIDIO` | presidio-analyzer | Regex patterns maison |
| data_analyst | `HAS_DUCKDB` | duckdb | Pandas parser |
| sentiment | `HAS_TRANSFORMERS` | transformers (HuggingFace) | LLM analysis |
| ai_workflows | `HAS_NETWORKX` | networkx | Kahn's algorithm maison |
| video_gen | `HAS_FFMPEG` | ffmpeg-python | Mock placeholders |
| image_gen | `HAS_REALESRGAN` | realesrgan | Pas d'upscaling |
| fine_tuning | `HAS_UNSLOTH` | unsloth | Mock training |
| content_studio | `HAS_TEXTSTAT` | textstat | Word count basique |
| presentation_gen | `HAS_MARP` | marp-cli | HTML export |
| pdf_processor | `HAS_PYMUPDF` | PyMuPDF | pdfplumber |
| audio_studio | `HAS_NOISEREDUCE` | noisereduce | Pydub seul |
| realtime_ai | `HAS_LIVEKIT` | livekit-server-sdk | Text-based sessions |
| ai_monitoring | `HAS_LANGFUSE` | langfuse | Prometheus seul |
| unified_search | `HAS_MEILISEARCH` | meilisearch | PostgreSQL ILIKE |
| ai_memory | `HAS_MEM0` | mem0ai | DB queries |
| code_sandbox | `HAS_DOCKER` | docker | Subprocess restreint |
| compression (middleware) | `HAS_BROTLI` | brotli | Gzip seul |

---

## Enterprise Infrastructure (16 composants)

Ces composants ne sont pas des modules auto-decouverts mais des elements d'infrastructure
partages par tous les modules.

| Composant | Pattern | Fichier principal | Libs utilisees | Fallback |
|-----------|---------|-------------------|----------------|----------|
| Structured Logging | A | `app/core/logging_config.py` | `structlog` | logging stdlib |
| Request ID Tracking | B | `app/middleware/request_id.py` | `contextvars` (stdlib) | - |
| Security Headers (OWASP) | B | `app/middleware/security_headers.py` | Aucune (starlette natif) | - |
| Compression Gzip+Brotli | A | `app/middleware/compression.py` | `brotli` (optionnel) | Gzip seul |
| Rate Limiting (sliding window) | B | `app/middleware/rate_limiter.py` | `redis` | In-memory fallback |
| Circuit Breaker | B | `app/core/circuit_breaker.py` | Aucune (zero-dep, maison) | - |
| Graceful Shutdown | B | `app/core/lifecycle.py` | `asyncio` (stdlib) | - |
| Health Checks (K8s probes) | B | `app/api/health.py` | Aucune | - |
| Token Blacklist (JWT) | B | `app/core/token_blacklist.py` | `redis` | In-memory set |
| OpenTelemetry Tracing | A | `app/core/telemetry.py` | `opentelemetry-*` (7 packages) | Prometheus seul |
| Error Tracking | A | `app/core/error_tracking.py` | `sentry-sdk` | structlog seul |
| Multi-tenant Middleware | B | `app/middleware/tenant_middleware.py` | `contextvars` (stdlib) | - |
| Audit Middleware | B | `app/middleware/audit_middleware.py` | Aucune | - |
| Feature Flag Middleware | B | `app/middleware/feature_flag_middleware.py` | `redis` | In-memory dict |
| Transactional Outbox | B | `app/core/outbox.py` | Aucune | - |
| Secrets Rotation | B | `app/core/secrets_rotation.py` | Aucune | - |

---

## Interconnexions entre modules

3 systemes d'orchestration connectent les modules entre eux :

### 1. Agent Executor (~79 actions)

Le service `agents` peut appeler directement les services des autres modules.
Chaque action mappe un nom (`transcribe_audio`, `search_knowledge`, etc.) a un appel de methode service.

**Fichier** : `app/modules/agents/service.py` (methode `execute_action`)

### 2. Pipeline Steps (29 step types)

Le module `pipelines` execute des etapes en sequence. Chaque step type appelle un service module.

**Fichier** : `app/modules/pipelines/service.py`

### 3. Workflow Actions (30 types)

Le module `ai_workflows` execute un DAG (graphe acyclique dirige) avec branches paralleles.
Chaque noeud du DAG est une action typee qui appelle un service.

**Fichier** : `app/modules/ai_workflows/service.py`

---

## Resume des patterns par categorie

```
Pattern A (Lib wrappee)        : 12 modules
Pattern B (From scratch)       : 26 modules
Pattern C (CLI wrappee)        :  2 modules

Total modules                  : 40
Total libs open-source         : 30+
Total fallbacks implementes    : 20+
Enterprise components          : 16
```

---

## Philosophie d'integration

1. **Auto-detection** : chaque lib optionnelle est detectee au demarrage via `try/except ImportError`
2. **Fallback gracieux** : si la lib n'est pas la, le module fonctionne quand meme (fonctionnalite reduite ou alternative)
3. **Zero crash** : aucune lib optionnelle ne peut faire crasher le demarrage
4. **Coexistence** : quand on ajoute une v2 d'une techno, la v1 reste en fallback (exemple : TF-IDF + pgvector dans knowledge)
5. **Upgrade transparent** : installer la lib pip suffit, le service la detecte au prochain demarrage

Cette approche permet de deployer la plateforme avec un `requirements.txt` minimal (FastAPI + SQLModel)
et d'ajouter les fonctionnalites avancees progressivement en installant les libs optionnelles.
