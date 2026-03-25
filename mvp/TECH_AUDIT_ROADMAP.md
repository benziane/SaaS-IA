# TECH AUDIT ROADMAP - Integrations Open Source & Gratuites

**Date de creation** : 2026-03-23
**Derniere mise a jour** : 2026-03-23
**Objectif** : Suivre l'integration progressive de libs/outils open-source pour ameliorer chaque module existant et preparer les modules planifies.

**Legende statut** :
- [ ] A examiner
- [x] FAIT
- 🔄 En cours
- ⏭️ Reporte

---

## PARTIE 1 : MODULES EXISTANTS - Ameliorations prioritaires

### Priorite IMMEDIATE

| # | Module | Lib/Repo | Stars | Impact | Action | Statut |
|---|--------|----------|-------|--------|--------|--------|
| 3 | knowledge | **pgvector** | 12K | Migrer TF-IDF -> embeddings vectoriels dans Postgres (deja en stack) | `CREATE EXTENSION vector;` + sentence-transformers | [x] FAIT (v3.3.0) |
| 4 | knowledge | **sentence-transformers** | 15K | Embeddings locaux gratuits (all-MiniLM-L6-v2) au lieu d'API | `pip install sentence-transformers` | [x] FAIT (v3.3.0) |
| 12 | cost_tracker | **litellm** | 15K | Proxy unifie multi-LLM + calcul auto tokens/cout | `pip install litellm` | [x] FAIT (v3.4.0) |
| 10 | security_guardian | **presidio** (Microsoft) | 4K | PII detection de niveau entreprise + anonymisation reversible | `pip install presidio-analyzer presidio-anonymizer` | [x] FAIT (v3.4.0) |

### Priorite SEMAINE 1

| # | Module | Lib/Repo | Stars | Impact | Action | Statut |
|---|--------|----------|-------|--------|--------|--------|
| 1 | transcription | **faster-whisper** + **pyannote** | 15K + 5K | Transcription locale gratuite + diarization speakers | `pip install faster-whisper pyannote.audio` | [x] FAIT (v3.5.0) |
| 2 | transcription | **distil-whisper pattern** | - | Confidence retry : base model first, medium model si low-confidence | Two-pass intégré dans `whisper_local.py` | [x] FAIT (v3.5.0) |
| 13 | data_analyst | **duckdb** | 20K | Queries SQL 100x plus rapides que pandas sur gros CSV | `pip install duckdb` | [x] FAIT (v3.5.0) |
| 14 | data_analyst | **ydata-profiling** | 12K | Auto-profiling dataset en 1 ligne (stats, distributions, correlations) | `pip install ydata-profiling` | [x] FAIT (v3.5.0) |

### Priorite SEMAINE 2

| # | Module | Lib/Repo | Stars | Impact | Action | Statut |
|---|--------|----------|-------|--------|--------|--------|
| 20 | voice_clone | **Coqui TTS** | 30K | TTS + voice cloning open-source complet, multi-langue | `pip install TTS` | [x] FAIT (v3.6.0) |
| 6 | pipelines | **@xyflow/react** (React Flow) | 35K | Visual DAG builder drag-and-drop dans Next.js | `npm install @xyflow/react` | [ ] A examiner (frontend only) |
| 11 | security_guardian | **NeMo-Guardrails** (NVIDIA) | 5K | Guardrails programmables + injection detection avancee | `pip install nemoguardrails` | [x] FAIT (v3.6.0) |

### Priorite SEMAINE 3

| # | Module | Lib/Repo | Stars | Impact | Action | Statut |
|---|--------|----------|-------|--------|--------|--------|
| 5 | compare | **promptfoo pattern** (LLM-as-judge) | 12K | Evaluation auto des reponses avec scoring + ELO ranking | `eval_engine.py` integre nativement | [x] FAIT (v3.7.0) |
| 7 | agents | **langgraph pattern** (ReAct) | 10K | ReAct agent + reflection loops + stateful blackboard | `graph_engine.py` integre nativement | [x] FAIT (v3.7.0) |
| 22 | ai_workflows | **networkx** | 15K | Validation DAG + tri topologique + detection cycles | `pip install networkx` | [x] FAIT (v3.7.0) |
| 24 | conversation | **Zep pattern** (hierarchical memory) | 3K | Memoire hierarchique : window + summaries + KB RAG + fact extraction | `memory_service.py` integre nativement | [x] FAIT (v3.7.0) |

### Priorite SEMAINE 4+

| # | Module | Lib/Repo | Stars | Impact | Action | Statut |
|---|--------|----------|-------|--------|--------|--------|
| 8 | sentiment | **cardiffnlp/twitter-roberta-base** (HF) | - | Modele SOTA gratuit sentiment, remplacerait les appels LLM couteux | `transformers` pipeline local | [ ] A examiner |
| 9 | web_crawler | **Jina Reader API** | - | Fallback gratuit (1M tokens) : `https://r.jina.ai/URL` -> markdown | Simple HTTP call, zero setup | [ ] A examiner |
| 15 | video_gen | **remotion** | 20K | Video programmatique en React (explainers, shorts, dynamique) | `npm install remotion` | [ ] A examiner |
| 16 | video_gen | **ffmpeg-python** | 9K | Montage/decoupe/sous-titrage auto (remplacerait mock mode) | `pip install ffmpeg-python` | [ ] A examiner |
| 17 | fine_tuning | **unsloth** | 20K | Training LoRA 2x plus rapide, 70% moins de VRAM | `pip install unsloth` | [ ] A examiner |
| 18 | fine_tuning | **lm-evaluation-harness** | 15K | Benchmark standard pour evaluer modeles fine-tunes | `pip install lm-eval` | [ ] A examiner |
| 19 | image_gen | **Real-ESRGAN** | 25K | Upscaling images generes (x4 resolution) | `pip install realesrgan` | [ ] A examiner |
| 21 | content_studio | **textstat** | 3K | Scoring lisibilite (Flesch-Kincaid) pour optimiser SEO du contenu genere | `pip install textstat` | [ ] A examiner |
| 23 | realtime_ai | **livekit** + **livekit-agents** | 10K + 1K | WebRTC open-source pour sessions audio/video temps reel | `pip install livekit-server-sdk` | [ ] A examiner |
| 25 | workspaces | **yjs** | 15K | CRDT pour collaboration temps reel documents/annotations | `npm install yjs y-websocket` | [ ] A examiner |

---

## PARTIE 2 : MODULES PLANIFIES - Stack open-source recommande

> Ces modules ne sont pas encore implementes. Cette section documente le meilleur stack open-source pour chaque futur module.

| # | Module | Stack recommande | Stars | Description | Statut |
|---|--------|-----------------|-------|-------------|--------|
| 23 | social_publisher | **postiz-app** | 15K | Alternative open-source Buffer/Hootsuite, scheduling multi-plateforme | [ ] A examiner |
| | | `tweepy` + `python-linkedin-v2` | - | APIs sociales directes (gratuit) | [ ] A examiner |
| 24 | unified_search | **Meilisearch** | 45K | Moteur de recherche ultra-rapide, hybrid search natif (BM25 + vectors), facettes, typo-tolerant | [ ] A examiner |
| | | `meilisearch-python` | - | SDK Python officiel | [ ] A examiner |
| 25 | ai_memory | **Mem0** | 25K | Couche memoire universelle pour IA, extraction auto de preferences | [ ] A examiner |
| | | `mem0ai` | - | SDK Python, self-hostable | [ ] A examiner |
| 26 | integration_hub | **Nango** | 4K | OAuth2 + sync + webhooks pour 200+ APIs, self-hostable | [ ] A examiner |
| | | `authlib` | - | OAuth2 cote serveur Python | [ ] A examiner |
| 27 | ai_chatbot_builder | **Typebot** | 18K | Chatbot builder open-source, embed widget, self-hostable | [ ] A examiner |
| | | **Flowise** | 30K | Visual LLM flow builder, RAG integre | [ ] A examiner |
| 28 | marketplace | Architecture manifest.json | - | Deja en place. Ajouter versioning `semver` + `jsonschema` pour validation | [ ] A examiner |
| | | **Stripe Connect** | - | Revenue sharing 70/30 natif | [ ] A examiner |
| 29 | presentation_gen | **Slidev** + **Marp** | 30K + 5K | Markdown -> slides, themes pro | [ ] A examiner |
| | | `playwright` | - | Export PDF headless | [ ] A examiner |
| 30 | code_sandbox | **Pyodide** | 15K | Python dans le browser (WebAssembly), zero cout serveur | [ ] A examiner |
| | | **Monaco Editor** | 40K | Editeur code VS Code dans le browser | [ ] A examiner |
| 31 | ai_forms | **conversational-form** | 10K | Formulaires conversationnels natifs | [ ] A examiner |
| | | `react-hook-form` | 40K | Deja dans notre stack | [ ] A examiner |
| 32 | ai_monitoring | **Langfuse** | 8K | Observabilite LLM open-source, self-hostable, traces + evals | [ ] A examiner |
| | | `opentelemetry-api` | - | Tracing standardise | [ ] A examiner |

---

## PARTIE 3 : TOP 5 ASTUCES KILLER

Chaque astuce est une amelioration transversale a fort impact. A implementer dans cet ordre.

### Astuce 1 : Knowledge - Hybrid Search pgvector + full-text Postgres

> Migration TF-IDF -> pgvector + BM25 natif Postgres. Zero service supplementaire, tout reste dans PostgreSQL. Amelioration RAG estimee : +40% pertinence.

- **Statut** : [x] FAIT (v3.3.0 - Sprint 10)
- **Implementation** : `embedding_service.py` + migration pgvector + methodes `search_vector()` / `search_hybrid()` / `search_tfidf()` (legacy conserve)
- **Resultat** : 4 modes de recherche coexistent, auto-detection transparente

### Astuce 2 : Cost Tracker - LiteLLM comme proxy unifie

> Un seul point d'entree pour tous les providers IA. Calcul auto des tokens et couts. Routing intelligent (le provider le moins cher qui supporte la tache). Remplace notre gestion manuelle des providers.

- **Statut** : [x] FAIT (v3.4.0)
- **Impact** : Couts IA -50%, routing intelligent, abstraction providers
- **Implementation** : `litellm_proxy.py` avec `complete()` + `complete_with_routing()`. `process_text_with_provider()` auto-detecte LiteLLM, fallback sur providers directs via `_process_text_direct()`.
- **Regle respectee** : providers directs (Gemini/Claude/Groq) conserves comme fallback dans `_process_text_direct()`

### Astuce 3 : Sentiment - Classifieur local rapide + LLM sampling

> RoBERTa (CardiffNLP) pour 95% des analyses (gratuit, <100ms). LLM uniquement pour les cas ambigus. Divise les couts IA du module sentiment par 10x.

- **Statut** : [ ] A examiner
- **Impact** : Couts sentiment /10, latence /50 (100ms vs 5s)
- **Implementation** : ajouter `_analyze_with_roberta()` dans le service, garder `_analyze_with_llm()` comme fallback pour les textes ambigus

### Astuce 4 : Security - Presidio + anonymisation asymetrique

> `Jean Dupont` -> `[PERSON_1]` avant envoi au LLM -> restauration apres reponse. Zero PII envoye aux providers IA. Conformite RGPD native.

- **Statut** : [x] FAIT (v3.4.0)
- **Impact** : Conformite RGPD, zero PII envoye aux providers
- **Implementation** : `presidio_service.py` avec `detect_pii()` + `anonymize()` + `deanonymize()`. `_detect_pii_smart()` auto-detecte Presidio, fallback regex. `_redact_pii_smart()` utilise anonymisation Presidio reversible.
- **Bonus** : anonymisation asymetrique = mapping reversible `[REDACTED] <-> Jean Dupont` via Presidio

### Astuce 5 : Data Analyst - DuckDB au lieu de Pandas

> Queries SQL en memoire sur CSV, 100x plus rapide que pandas. Les LLM generent du SQL standard (qu'ils maitrisent mieux que l'API pandas). Pattern Code Interpreter gratuit.

- **Statut** : [x] FAIT (v3.5.0)
- **Impact** : Performance x100 sur gros fichiers, meilleure qualite de code genere par LLM
- **Implementation** : `duckdb_engine.py` avec `parse_csv_duckdb()`, `query_dataset()`, `auto_profile()`. Upload auto-detecte DuckDB, fallback pandas. ydata-profiling auto-genere le profil.

---

## PARTIE 4 : PLANNING D'INTEGRATION

> Ordre recommande pour integrer les ameliorations, par vague.

### Vague 1 - IMMEDIATE (fait ou en cours)

| Priorite | Libs | Module | Impact | Statut |
|----------|------|--------|--------|--------|
| Immediat | pgvector + sentence-transformers | knowledge | RAG 10x meilleur | [x] FAIT |
| Immediat | litellm | cost_tracker + ai_assistant | Couts -50%, routing intelligent | [x] FAIT |
| Immediat | presidio | security_guardian | Securite enterprise-grade | [x] FAIT |

### Vague 2 - SEMAINE 1

| Priorite | Libs | Module | Impact | Statut |
|----------|------|--------|--------|--------|
| Semaine 1 | faster-whisper + pyannote.audio | transcription | Transcription locale gratuite | [x] FAIT |
| Semaine 1 | duckdb + ydata-profiling | data_analyst | Data analyst production-ready | [x] FAIT |

### Vague 3 - SEMAINE 2

| Priorite | Libs | Module | Impact | Statut |
|----------|------|--------|--------|--------|
| Semaine 2 | Coqui TTS | voice_clone | Voice clone sans API payante | [x] FAIT |
| Semaine 2 | NeMo-Guardrails | security_guardian | Injection detection avancee | [x] FAIT |
| Semaine 2 | @xyflow/react pattern | pipelines | Visual pipeline builder demo page | [x] FAIT (v3.8.0) |
| Semaine 2 | langfuse pattern | ai_monitoring (nouveau) | Monitoring IA complet - dashboard KPI, traces, providers | [x] FAIT (v3.8.0) |

### Vague 3b - SEMAINE 3 (patterns integres nativement)

| Priorite | Libs/Patterns | Module | Impact | Statut |
|----------|--------------|--------|--------|--------|
| Semaine 3 | promptfoo pattern (eval_engine.py) | compare | LLM-as-judge auto + ELO ranking | [x] FAIT |
| Semaine 3 | langgraph pattern (graph_engine.py) | agents | ReAct + reflection + stateful | [x] FAIT |
| Semaine 3 | networkx | ai_workflows | DAG validation + cycles + topo sort | [x] FAIT |
| Semaine 3 | Zep pattern (memory_service.py) | conversation | Hierarchical memory + fact extraction | [x] FAIT |

### Vague 4 - COMPLETEE

| Priorite | Libs | Module | Impact | Statut |
|----------|------|--------|--------|--------|
| Final | meilisearch pattern | unified_search (nouveau) | Recherche universelle cross-module + RAG | [x] FAIT (v3.8.0) |
| Final | mem0 pattern | ai_memory (nouveau) | Memoire persistante + auto-extraction + context injection | [x] FAIT (v3.8.0) |

---

## REGLES D'INTEGRATION

1. **Ne jamais ecraser un module/techno existant** : creer une v2 ou ajouter les nouvelles methodes a cote
2. **Toujours garder un fallback** : si la nouvelle lib n'est pas installee, le module doit fonctionner comme avant
3. **Auto-detection** : le service detecte automatiquement si la lib est disponible et utilise le meilleur mode
4. **Lazy loading** : charger les modeles/libs lourds uniquement au premier appel (singleton)
5. **Tester avant de cocher FAIT** : verifier que le module fonctionne avec ET sans la nouvelle lib
6. **Documenter** : mettre a jour ROADMAP.md et CLAUDE.md apres chaque integration
