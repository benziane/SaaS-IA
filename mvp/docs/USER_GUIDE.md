# SaaS-IA -- Guide Utilisateur

> **Version** : 4.0.0 | **Date** : Mars 2026
> Plateforme SaaS modulaire d'intelligence artificielle -- 37 modules, ~280 endpoints API, 41 pages frontend.

---

## Introduction

Bienvenue sur **SaaS-IA**, votre plateforme d'intelligence artificielle modulaire. SaaS-IA permet de transcrire, analyser, generer, automatiser et deployer des services IA depuis une interface unifiee.

La plateforme est concue autour de **modules independants** qui communiquent entre eux via trois systemes d'orchestration (Agents, Pipelines, Workflows). Chaque module peut etre utilise seul ou chaine avec d'autres pour creer des automatisations puissantes.

### Ce que vous pouvez faire avec SaaS-IA

- **Transcrire** des videos YouTube, fichiers audio/video, ou enregistrements en direct
- **Generer du contenu** dans 10 formats (blog, tweets, LinkedIn, newsletter, etc.)
- **Analyser des donnees** en langage naturel (upload CSV/JSON, questions, charts)
- **Automatiser** des workflows IA complets sans ecrire de code
- **Deployer des chatbots** RAG sur votre site web
- **Creer des presentations**, des images, des videos avec l'IA
- **Cloner des voix** et generer du text-to-speech multilingue
- **Securiser** vos donnees avec detection PII et protection prompt injection
- **Fine-tuner** des modeles IA avec vos propres donnees

---

## Premiers pas

### 1. Creer un compte

1. Rendez-vous sur l'interface SaaS-IA (par defaut `http://localhost:3002`)
2. Cliquez sur **S'inscrire**
3. Renseignez votre email, nom complet et mot de passe
4. Vous etes redirige vers le **Dashboard**

> **Note** : En mode developpement, un compte admin est disponible. Consultez le fichier `.env` pour les identifiants.

### 2. Choisir un plan

SaaS-IA propose trois plans de souscription :

| Plan | Transcriptions/mois | Minutes audio | Appels IA | Prix |
|------|---------------------|---------------|-----------|------|
| **Free** | 10 | 60 | 50 | 0 EUR |
| **Pro** | 100 | 600 | 500 | 19 EUR/mois |
| **Enterprise** | Illimite | Illimite | Illimite | Sur devis |

Pour changer de plan :
1. Allez dans **Billing** (`/billing`) depuis le menu lateral
2. Consultez votre consommation actuelle (barre de progression)
3. Cliquez sur **Upgrade** pour passer au plan superieur
4. Le paiement est gere via **Stripe** (carte bancaire)

Vous recevez une notification a **80%** et **100%** de votre quota.

### 3. Interface du dashboard

Le dashboard (`/dashboard`) affiche :
- **Statistiques globales** : nombre total de transcriptions, completees, echouees, duree totale
- **Transcriptions recentes** : les dernieres operations avec leur statut
- **Acces rapide** a tous les modules via le menu lateral

Le menu lateral donne acces a toutes les sections :
- Transcription, Chat, Compare, Pipelines, Knowledge Base
- Content Studio, Workflows, Crews, Voice, Realtime
- Images, Data Analyst, Video Studio, Fine-Tuning
- Security, Monitoring, Search, Memory
- Chatbot Builder, Code Sandbox, AI Forms, Presentations
- Social Publisher, Marketplace, Integrations
- Workspaces, Billing, API Keys, Profil

---

## Modules par cas d'usage

### Creer du contenu

#### Content Studio (`/content-studio`)

Transformez n'importe quelle source en contenu publiable dans **10 formats** :

| Format | Description |
|--------|-------------|
| Blog Article | Article structure avec H1/H2, introduction, sections, conclusion (800-1500 mots) |
| Twitter Thread | Thread viral de 8-15 tweets avec hook et hashtags |
| LinkedIn Post | Post professionnel avec emojis, paragraphes courts, question d'engagement |
| Newsletter | Email avec subject line, preview text et CTA |
| Instagram Carousel | Carrousel 8-10 slides avec caption et hashtags |
| YouTube Description | Description SEO-optimisee avec timestamps et tags |
| SEO Meta | Metadata en JSON (title, description, keywords, Open Graph) |
| Press Release | Communique de presse avec dateline et boilerplate |
| Email Campaign | 3 variations (awareness, value, conversion) |
| Podcast Notes | Notes avec timestamps, citations, ressources |

**Sources supportees** : texte libre, transcription existante, document Knowledge Base, URL (scraping automatique).

**Comment l'utiliser** :
1. Creez un **projet** en choisissant votre source
2. Selectionnez les **formats** de sortie souhaites (un ou plusieurs)
3. Cliquez sur **Generer** -- l'IA produit chaque format
4. Editez, copiez ou regenerez chaque contenu individuellement
5. Raccourci : utilisez **From URL** pour generer en un clic depuis une page web

#### Presentation Gen (`/presentations`)

Generez des presentations IA depuis un sujet ou une transcription.

- **5 templates** disponibles (business, technique, educatif, pitch, rapport)
- Edition slide par slide (ajout, modification, suppression)
- Export en **HTML**, **Markdown** ou **PDF**
- Generation depuis une transcription existante (`POST /from-transcript`)

#### Image Gen (`/images`)

Generez des images IA avec **10 styles** artistiques :

- Photorealiste, Illustration, Anime, Minimaliste, Aquarelle, Pixel Art, etc.
- **Thumbnails YouTube** automatiques depuis une transcription
- **Generation en lot** (bulk) pour plusieurs images simultanees
- **Upscaling Real-ESRGAN** pour ameliorer la resolution
- Organisez vos images en **projets**

#### Video Gen (`/video-studio`)

Creez des videos avec l'IA :

| Type | Description |
|------|-------------|
| Text-to-Video | Generer une video depuis un prompt texte |
| Clips Highlights | Extraire les meilleurs moments d'une transcription |
| Avatar Parlant | Video avec un avatar anime qui parle votre texte |
| Explainer | Video explicative animee |
| Shorts | Format court pour reseaux sociaux |
| From Source | Video depuis une transcription ou un document |

#### Audio Studio (`/audio-studio`)

Studio de production audio et podcast :

- Edition audio assistee par IA
- Generation automatique de chapitres
- Notes de show et resume
- Generation de flux RSS pour distribution podcast

---

### Analyser et comprendre

#### Transcription (`/transcription`)

Transcrivez de l'audio et de la video en texte, avec chapitrage et resume automatique.

**3 sources d'entree** :
1. **YouTube / URL** : collez un lien YouTube ou une URL de video
2. **Upload** : glissez-deposez un fichier audio/video (MP3, WAV, MP4, M4A, OGG, WEBM, FLAC -- max 500 MB)
3. **Enregistrement** : enregistrez directement depuis votre microphone

**Fonctionnalites** :
- Selection de la **langue** de transcription
- **Diarization** : identification des locuteurs (qui parle quand)
- **Auto-chapitrage** avec resume par chapitre
- **Smart Transcribe** : routage intelligent vers le meilleur provider
- Export en **TXT** ou **SRT** (sous-titres)
- Copie vers le presse-papier
- Analyse de **playlists YouTube** entieres
- Analyse de **streams en direct**
- Analyse de **frames video** avec Vision AI

**Providers** (auto-detection avec fallback) :
1. Sous-titres YouTube (gratuit, instantane)
2. faster-whisper (local, gratuit)
3. Legacy Whisper
4. AssemblyAI (premium, payant)

#### Sentiment (`/sentiment`)

Analysez les emotions et le sentiment d'un texte ou d'une transcription.

- **RoBERTa** (modele cardiffnlp) pour la detection fine des emotions
- Fallback vers analyse **LLM** si le modele n'est pas disponible
- Analyse directe de texte ou depuis une transcription existante
- Resultats : sentiment global (positif/negatif/neutre), emotions detectees, score de confiance

#### Data Analyst (`/data`)

Transformez vos donnees en insights avec l'IA :

1. **Uploadez** un dataset (CSV, JSON, Excel)
2. **Auto-analyse** : profiling automatique des colonnes, statistiques, distributions
3. **Questions en langage naturel** : "Quelle est la tendance des ventes par trimestre ?"
4. **Charts** generes automatiquement
5. **Rapport complet** exportable

**Moteurs** : DuckDB (SQL in-memory, 100x plus rapide que pandas) + ydata-profiling (auto-statistiques).

#### PDF Processor (`/pdf`)

Traitez vos documents PDF avec l'IA :

- **Upload** et parsing automatique du contenu
- **Resume** IA du document complet
- **Requetes RAG** : posez des questions sur le contenu du PDF
- **Extraction de tables** et donnees structurees
- **Export Markdown** du contenu extrait

#### Repo Analyzer (`/repo-analyzer`)

Analysez un depot GitHub avec l'IA :

- Detection automatique de la **stack technique**
- **Score de qualite** du code
- Generation de **documentation** automatique
- **Audit de securite** du depot

---

### Automatiser

#### Pipelines (`/pipelines`)

Chainez des operations IA de maniere sequentielle :

1. Creez un pipeline avec un nom et une description
2. Ajoutez des **steps** (etapes) dans l'ordre souhaite
3. Executez le pipeline -- chaque etape passe son resultat a la suivante
4. Consultez l'historique des executions et les resultats par etape

**20 types de steps disponibles** :
- `summarize` : resumer du texte
- `translate` : traduire dans une langue
- `transcription` : transcrire audio/video
- `web_crawl` : scraper une page web
- `sentiment` : analyser le sentiment
- `search_knowledge` : rechercher dans la Knowledge Base
- `ask_knowledge` : question RAG sur la Knowledge Base
- `compare` : comparer les modeles IA
- `content_studio` : generer du contenu multi-format
- `generate_image` : generer une image
- `generate_video` : generer une video
- `text_to_speech` : synthese vocale
- `security_scan` : scanner pour PII/injection
- `crawl_and_index` : scraper et indexer dans la KB
- `export` : formater la sortie

**Exemple** : YouTube URL -> Transcription -> Resume -> Traduction EN -> Export PDF

#### AI Workflows (`/workflows`)

Automatisations no-code avec graphe DAG (branches paralleles possibles) :

- **23 types d'actions** couvrant tous les modules de la plateforme
- **5 templates pre-construits** pour demarrer rapidement :
  - YouTube to Blog Post (3 noeuds)
  - Social Media Pack (4 noeuds, parallele)
  - Competitive Intelligence (4 noeuds)
  - Knowledge Enrichment (3 noeuds)
  - Multilingual Content (4 noeuds)
- Validation DAG automatique (detection de cycles, connectivite)
- Historique des executions avec resultats par noeud
- Support **webhook externe** pour declencher depuis des outils tiers

**Difference avec les Pipelines** : les Workflows supportent les branches paralleles (DAG) tandis que les Pipelines sont strictement sequentiels.

#### Agents (`/agents`)

Agents IA autonomes avec planification et execution :

- **Agent autonome** : donnez une instruction en langage naturel, l'agent planifie et execute les actions necessaires
- **Agent ReAct** : boucle iterative Think-Act-Observe-Reflect pour les taches complexes
- Acces a **~68 actions** couvrant tous les modules de la plateforme
- Historique des runs avec detail de chaque etape
- Possibilite d'**annuler** un agent en cours d'execution

**Exemple** : "Transcris cette video YouTube, resume-la, genere un article de blog et des tweets, puis scanne le contenu pour les donnees personnelles."

#### Multi-Agent Crew (`/crews`)

Equipes d'agents collaboratifs inspires de CrewAI :

**9 roles specialises** :
| Role | Specialite |
|------|------------|
| Researcher | Recherche d'information (web + KB) |
| Writer | Redaction de contenu |
| Reviewer | Relecture et amelioration qualite |
| Analyst | Analyse de donnees et insights |
| Coder | Generation de code |
| Translator | Traduction et localisation |
| Summarizer | Synthese et resume |
| Creative | Ideation et direction creative |
| Custom | Role personnalise par l'utilisateur |

**4 templates d'equipes** :
- Research & Writing Team (Researcher -> Writer -> Reviewer)
- Market Analysis Team (Researcher -> Analyst -> Strategy Advisor)
- Multilingual Content Team (Writer -> Translator -> Quality Checker)
- Social Media Team (Trend Scout -> Creative Director -> Engagement Optimizer)

Chaque agent passe son resultat au suivant, avec communication inter-agents et utilisation automatique des outils de la plateforme.

---

### Communiquer

#### Conversation (`/chat`)

Chat IA contextuel avec historique :

- Conversations liees a une **transcription** (contexte automatique)
- Streaming SSE (affichage token par token, style ChatGPT)
- Historique complet des conversations et messages
- Bouton **"Chat about this"** sur les transcriptions completees
- Memoire hierarchique : fenetre glissante + resumes IA + RAG Knowledge Base

#### Voice Clone (`/voice`)

Synthese vocale et clonage de voix :

- **Text-to-Speech** : texte libre vers audio (MP3/WAV/OGG)
- **TTS depuis source** : generez l'audio d'une transcription ou d'un document
- **Doublage multilingue** : transcription -> traduction -> synthese vocale
- **Clonage vocal** : uploadez un echantillon audio (5-30 secondes) pour creer un profil vocal reutilisable
- **10 voix integrees** (6 OpenAI + 4 ElevenLabs)
- Vitesse configurable (0.5x a 2x)

**Providers** : OpenAI TTS, Coqui TTS (local, gratuit, multi-langue), ElevenLabs (clonage), avec fallback automatique.

#### Realtime AI (`/realtime`)

Sessions IA en temps reel :

| Mode | Description |
|------|-------------|
| Voice | Conversation vocale avec l'IA |
| Vision | Analyse visuelle (ecran/camera) |
| Voice + Vision | Voix avec contexte visuel |
| Meeting | Assistant de reunion temps reel |

- RAG automatique (recherche Knowledge Base a chaque message)
- Transcript et resume generes automatiquement en fin de session
- 3 providers : Gemini Flash, Groq (ultra-rapide), Claude
- Multi-langue : auto, EN, FR, ES, DE, JA, ZH

#### Social Publisher (`/social-publisher`)

Publiez votre contenu sur les reseaux sociaux :

- **4 plateformes** : Twitter/X, LinkedIn, Instagram, TikTok
- Connectez vos comptes via OAuth
- Creez des posts en **brouillon** ou **planifies**
- **Publication immediate** ou **programmee**
- **Analytics** par post (vues, engagements, clics)
- **Recyclage** automatique de contenu depuis Content Studio

---

### Construire

#### AI Chatbot Builder (`/chatbot-builder`)

Creez et deployez des chatbots RAG sur votre site :

1. **Creez** un chatbot avec un nom et un system prompt
2. **Configurez** les documents sources (Knowledge Base)
3. **Publiez** le chatbot pour obtenir un token d'acces
4. **Recuperez le code embed** (HTML/JS snippet)
5. **Collez** le snippet sur votre site web

- Chat public via widget embeddable (aucune authentification requise pour les visiteurs)
- Historique des conversations par session
- **Analytics** : nombre de conversations, questions populaires, taux de satisfaction
- Multi-canal : web, API, integrations tierces

#### Code Sandbox (`/code-sandbox`)

Environnement d'execution de code securise :

- Creez des **sandboxes** avec des cellules de code (style notebook)
- **Execution securisee** de code Python
- **Generation de code** depuis un prompt en langage naturel
- **Explication** de code par l'IA
- **Debug** assiste par IA (envoyez une erreur, l'IA propose un correctif)

#### AI Forms (`/ai-forms`)

Formulaires intelligents avec IA :

- Creez des formulaires **conversationnels** (style typeform)
- **Generation IA** : decrivez votre formulaire en langage naturel, l'IA cree les questions
- **Publication** avec token de partage (acces public sans authentification)
- **Scoring IA** des reponses (evaluation automatique)
- **Analytics IA** : analyse globale des reponses collectees
- Fermeture des reponses quand souhaite

#### Marketplace (`/marketplace`)

Place de marche pour modules, templates et prompts :

- **8 categories** de listings
- Parcourez et installez des modules communautaires
- Publiez vos propres creations (modules, templates de workflow, prompts)
- Systeme de **notes et avis**
- Listings **featured** mis en avant
- Gestion de vos publications et installations

---

### Gerer

#### Workspaces (`/workspaces`)

Collaboration en equipe :

- Creez des **espaces de travail** partages
- **Invitez des membres** par email
- 3 roles : Owner, Editor, Viewer
- **Partagez** des transcriptions, documents, contenus generes
- **Commentaires** sur les elements partages
- Notifications en temps reel

#### Billing (`/billing`)

Gestion des plans et de la facturation :

- Visualisation du **plan actuel** et des quotas
- Barres de progression de **consommation** (transcriptions, minutes, appels IA)
- **Upgrade/Downgrade** de plan via Stripe Checkout
- Acces au **portail Stripe** pour gerer les paiements
- Alertes automatiques a 80% et 100% du quota

#### API Keys (`/api-docs`)

Acces API externe pour les developpeurs :

- Generez des **cles API** (`sk-...`) depuis l'interface
- La cle est affichee **une seule fois** en clair (copiez-la immediatement)
- Utilisez la cle via le header `X-API-Key` sur les endpoints `/v1/*`
- **Revoquez** une cle a tout moment
- Endpoints publics disponibles :
  - `POST /v1/transcribe` : transcription directe
  - `POST /v1/process` : traitement IA generique
  - `GET /v1/jobs/{id}` : statut d'un job

#### Knowledge Base (`/knowledge`)

Base de connaissances avec recherche RAG hybride :

- **Upload** de documents (TXT, MD, CSV -- max 10 MB)
- Indexation automatique avec chunking intelligent
- **Recherche hybride** (auto-detectee) :
  - **TF-IDF** : cosine similarity sur frequence des termes (toujours disponible)
  - **Vector** : recherche semantique via embeddings pgvector (384 dimensions)
  - **Hybrid** : Reciprocal Rank Fusion (70% vector + 30% TF-IDF)
- **RAG** : posez une question, l'IA synthetise une reponse depuis vos documents
- Les transcriptions sont automatiquement indexees
- Reindexation des embeddings a la demande

#### Cost Tracker (`/costs`)

Suivi des couts IA :

- **Dashboard** avec ventilation des couts par provider, par module, par periode
- **Alertes budget** : recevez des avertissements si vos depenses depassent un seuil
- **Export CSV** des logs d'utilisation pour comptabilite

#### Integration Hub (`/integrations`)

Connectez SaaS-IA a vos outils externes :

- **10 providers** supportes (webhooks, OAuth2, API key)
- Creez des **connecteurs** vers vos services (Zapier, Make, n8n, etc.)
- Testez la connectivite avant de deployer
- **Triggers** automatiques : declenchez des actions SaaS-IA sur evenement externe
- Reception de **webhooks** entrants

#### Tenants (`/tenants`)

Gestion multi-tenant pour les deployments enterprise :

- Isolation des donnees par tenant (Row-Level Security)
- Branding white-label par tenant
- Gestion centralisee des tenants

---

## Fonctionnalites transversales

### Recherche universelle (`/search`)

La recherche universelle (Unified Search) permet de chercher a travers **tous les modules** simultanement :

- Transcriptions, documents Knowledge Base, contenus generes, conversations
- Indexation via **Meilisearch** (ultra-rapide) avec fallback PostgreSQL ILIKE
- **"Ask AI"** : posez une question, l'IA synthetise une reponse depuis tous vos contenus (cross-module RAG)
- Reindexation par module a la demande

### Memoire IA persistante (`/memory`)

La memoire IA (style Mem0) retient vos preferences et le contexte entre les sessions :

- **4 types de memoire** : preferences, faits, contexte, instructions
- **Auto-extraction** : l'IA detecte et memorise automatiquement les informations pertinentes de vos conversations
- **Context injection** : la memoire est automatiquement injectee dans les appels IA pour des reponses personnalisees
- **Rappel semantique** : retrouvez des souvenirs par similarite semantique
- **RGPD Forget** : supprimez toutes vos memoires en un clic (droit a l'oubli)

### Monitoring IA (`/monitoring`)

Dashboard d'observabilite LLM (style Langfuse) :

- **KPI dashboard** : latence moyenne, cout total, tokens consommes, taux d'erreur
- **Comparaison providers** : Gemini vs Claude vs Groq (latence, cout, qualite)
- **Traces** : detail de chaque appel IA (provider, modele, tokens, duree, cout)
- **Cost analytics** : evolution des couts dans le temps
- Integration **Langfuse** optionnelle pour traces avancees
- Integration **OpenTelemetry** pour tracing distribue

### Securite (`/security`)

Couche de securite transversale pour toute la plateforme :

- **Detection PII** : email, telephone, numero de securite sociale, carte bancaire, IBAN, IP, numero INSEE (30+ types avec Presidio)
- **Detection prompt injection** : 20 patterns (jailbreak, DAN mode, bypass, ignore instructions, etc.) via NeMo Guardrails + regex
- **Auto-redaction** : remplacement automatique des PII detectees (`[EMAIL_REDACTED]`, `[PHONE_REDACTED]`, etc.)
- **Content safety** : verification IA du contenu dangereux ou illegal
- **Guardrail rules** : regles de securite configurables (block_pattern, pii_redact, content_filter, rate_limit)
- **Audit trail** : journal complet de toutes les interactions IA (action, module, provider, tokens, cout, IP)
- **Dashboard securite** : stats agregees, distribution des risques, top modules concernes

### Notifications temps reel

Les notifications WebSocket informent en temps reel de :
- Fin de transcription
- Quotas a 80% / 100%
- Fin d'execution de pipeline ou workflow
- Evenements d'integration (webhooks recus)

---

## API Reference

### Documentation interactive

- **Swagger UI** : `http://localhost:8004/docs` -- interface interactive pour tester tous les endpoints
- **ReDoc** : `http://localhost:8004/redoc` -- documentation lisible avec schemas detailles
- **Reference complete** : voir [API_REFERENCE.md](API_REFERENCE.md) pour la liste exhaustive de tous les endpoints

### Authentification

| Methode | Header | Utilisation |
|---------|--------|-------------|
| JWT Bearer | `Authorization: Bearer <access_token>` | Tous les endpoints `/api/*` |
| API Key | `X-API-Key: sk-...` | API publique `/v1/*` |

### Obtenir un token JWT

```bash
# 1. Login
curl -X POST http://localhost:8004/api/auth/login \
  -d "username=votre@email.com&password=votre_mot_de_passe"

# Reponse : { "access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer" }

# 2. Utiliser le token
curl -H "Authorization: Bearer eyJ..." http://localhost:8004/api/auth/me

# 3. Rafraichir le token (quand expire)
curl -X POST http://localhost:8004/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJ..."}'
```

### Health Checks

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check basique |
| `GET /health/live` | Kubernetes liveness probe |
| `GET /health/ready` | Readiness probe (PostgreSQL + Redis) |
| `GET /health/startup` | Startup probe (modules charges) |
| `GET /metrics` | Metriques Prometheus |

---

## FAQ

### 1. Quels formats audio/video sont supportes pour la transcription ?

MP3, WAV, MP4, M4A, OGG, WEBM et FLAC. La taille maximale est de 500 MB par fichier.

### 2. Puis-je utiliser SaaS-IA sans cle API payante ?

Oui. Le mode `ASSEMBLYAI_API_KEY=MOCK` permet de tester la transcription sans API payante. Pour l'IA, au moins une cle (Gemini, Claude ou Groq) est necessaire -- Gemini offre un tier gratuit genereux. La transcription locale via faster-whisper est entierement gratuite.

### 3. Comment fonctionne la recherche hybride dans la Knowledge Base ?

La recherche auto-detecte le meilleur mode disponible :
- Si pgvector + sentence-transformers sont installes : **Hybrid** (70% recherche semantique + 30% TF-IDF)
- Sinon : **TF-IDF** classique (toujours disponible comme fallback)

La recherche semantique comprend le sens des mots (synonymes, paraphrases), tandis que TF-IDF se base sur les termes exacts.

### 4. Quelle est la difference entre Pipelines, Workflows et Agents ?

- **Pipelines** : etapes sequentielles (A -> B -> C). Simple et previsible.
- **Workflows** : graphe DAG avec branches paralleles. Plus flexible, supporte les conditions.
- **Agents** : autonomes. Donnez une instruction en langage naturel, l'agent planifie et execute. Plus puissant mais moins previsible.

### 5. Comment deployer un chatbot sur mon site web ?

1. Creez un chatbot dans **Chatbot Builder**
2. Ajoutez des documents sources depuis la Knowledge Base
3. Publiez le chatbot (bouton **Publish**)
4. Copiez le **code embed** (snippet HTML/JS)
5. Collez-le dans votre site web -- le widget de chat apparait automatiquement

### 6. Mes donnees sont-elles securisees ?

Oui. SaaS-IA integre :
- Detection PII automatique (Presidio, 30+ types)
- Detection prompt injection (NeMo Guardrails, 20 patterns)
- Audit trail complet de toutes les operations IA
- Headers de securite OWASP (HSTS, CSP, X-Frame-Options, etc.)
- Chiffrement JWT avec rotation de tokens
- Isolation multi-tenant (Row-Level Security)

### 7. Puis-je utiliser mes propres modeles IA ?

Oui, via le module **Fine-Tuning**. Vous pouvez creer des datasets depuis vos transcriptions, conversations et documents, puis entrainer des modeles LoRA sur Llama, Mistral ou Gemma.

### 8. Comment suivre mes couts IA ?

Le module **Cost Tracker** (`/costs`) affiche un dashboard avec ventilation par provider et par module. Le module **AI Monitoring** (`/monitoring`) offre des traces detaillees de chaque appel IA avec tokens et couts exacts (via LiteLLM).

### 9. Comment connecter SaaS-IA a mes outils existants (Zapier, Make, n8n) ?

Utilisez le module **Integration Hub** (`/integrations`) :
1. Creez un connecteur avec le type webhooks
2. Configurez l'URL de webhook dans votre outil tiers
3. Creez un trigger pour declencher des actions SaaS-IA sur evenement
4. Vous pouvez aussi utiliser l'**API publique** (`/v1/*`) avec une cle API

### 10. Quels providers IA sont supportes ?

SaaS-IA supporte 3 providers LLM via un proxy unifie (LiteLLM) :
- **Gemini 2.0 Flash** (Google) : rapide et economique
- **Claude Sonnet** (Anthropic) : excellent pour la redaction et l'analyse
- **Groq Llama 3.3 70B** : ultra-rapide (inference acceleree)

Le systeme AI Router selectionne automatiquement le meilleur provider selon le type de tache. Vous pouvez aussi comparer les providers cote a cote via le module **Compare** (`/compare`).

---

## Support et documentation complementaire

- **Architecture technique** : [ARCHITECTURE.md](ARCHITECTURE.md)
- **Guide de deploiement** : [DEPLOYMENT.md](DEPLOYMENT.md)
- **Reference API complete** : [API_REFERENCE.md](API_REFERENCE.md)
- **Demarrage rapide** : [GETTING_STARTED.md](GETTING_STARTED.md)
- **Tutoriels** : [TUTORIALS.md](TUTORIALS.md)
- **Roadmap et changelog** : [../ROADMAP.md](../ROADMAP.md)
- **Audit technique** : [../TECH_AUDIT_ROADMAP.md](../TECH_AUDIT_ROADMAP.md)
- **Swagger UI** : `http://localhost:8004/docs`
