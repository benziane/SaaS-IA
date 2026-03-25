# SaaS-IA -- Tutoriels pas-a-pas

> 5 tutoriels pratiques pour maitriser les fonctionnalites cles de la plateforme.
> Chaque tutoriel est autonome et peut etre suivi independamment.

---

## Tutoriel 1 : Transcrire et resumer une video YouTube

> **Duree** : 10 minutes
> **Modules utilises** : Transcription, AI Assistant
> **Pre-requis** : Compte SaaS-IA, au moins une cle API IA configuree

### Objectif

Transcrire une video YouTube, obtenir le chapitrage automatique, generer un resume et exporter le tout en Markdown.

### Etape 1 : Lancer la transcription

**Via l'interface** :
1. Allez sur **Transcription** (`/transcription`)
2. Dans l'onglet **YouTube / URL**, collez l'URL de la video
3. Selectionnez la langue (ou laissez `auto`)
4. Cliquez sur **Transcrire**

**Via l'API** :
```bash
# Remplacez $TOKEN par votre access_token JWT
curl -X POST http://localhost:8004/api/transcription/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VOTRE_VIDEO_ID",
    "language": "fr"
  }'
```

**Reponse** :
```json
{
  "id": "abc123-...",
  "status": "processing",
  "source_type": "youtube",
  "language": "fr"
}
```

### Etape 2 : Attendre la fin du traitement

La transcription est asynchrone (traitee par Celery). Verifiez le statut :

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/transcription/abc123-...
```

Attendez que `status` passe de `processing` a `completed`. Dans l'interface, le statut se met a jour automatiquement.

**Ordre de tentative des providers** (auto-detection) :
1. Sous-titres YouTube (gratuit, instantane si disponibles)
2. faster-whisper (local, gratuit, necessite le module installe)
3. Legacy Whisper
4. AssemblyAI (payant, haute qualite)

### Etape 3 : Obtenir le chapitrage automatique

```bash
curl -X POST http://localhost:8004/api/transcription/auto-chapter \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transcription_id": "abc123-..."
  }'
```

**Reponse** : une liste de chapitres avec timestamps et resume par chapitre :
```json
{
  "chapters": [
    {
      "start_time": "00:00",
      "end_time": "02:30",
      "title": "Introduction et contexte",
      "summary": "Presentation du sujet..."
    },
    {
      "start_time": "02:30",
      "end_time": "08:15",
      "title": "Les enjeux principaux",
      "summary": "Discussion sur..."
    }
  ]
}
```

### Etape 4 : Identifier les locuteurs

Si la video contient plusieurs locuteurs :

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/transcription/abc123-.../speakers
```

La diarization (pyannote) identifie qui parle quand, avec des segments par locuteur.

### Etape 5 : Generer un resume IA

Utilisez le bouton **"Improve with AI"** sur la transcription, ou appelez l'AI Assistant :

```bash
curl -X POST http://localhost:8004/api/ai-assistant/process-text \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Voici le texte de la transcription...",
    "task": "summarize",
    "language": "fr"
  }'
```

### Etape 6 : Exporter

Dans l'interface, cliquez sur **Export** pour telecharger en :
- **TXT** : texte brut
- **SRT** : format sous-titres avec timecodes

Vous pouvez aussi copier le texte via le bouton **Copier** (presse-papier).

### Resultat final

Vous avez maintenant :
- Le texte integral de la video
- Un chapitrage avec resume par section
- L'identification des locuteurs
- Un resume global genere par IA
- Le tout exportable en TXT ou SRT

---

## Tutoriel 2 : Creer un pipeline de content marketing

> **Duree** : 15 minutes
> **Modules utilises** : Transcription, Content Studio, Pipelines, Social Publisher
> **Pre-requis** : Une transcription completee (voir Tutoriel 1)

### Objectif

Partir d'une transcription et generer automatiquement un article de blog, des tweets, un post LinkedIn, puis planifier la publication sur les reseaux sociaux.

### Etape 1 : Creer un projet Content Studio

```bash
curl -X POST http://localhost:8004/api/content-studio/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Marketing Q1 2026",
    "source_type": "transcription",
    "source_id": "abc123-...",
    "description": "Contenu marketing depuis la keynote Q1"
  }'
```

**Reponse** : `{ "id": "proj-456-...", "name": "Marketing Q1 2026", ... }`

### Etape 2 : Generer du contenu dans plusieurs formats

```bash
curl -X POST http://localhost:8004/api/content-studio/projects/proj-456-.../generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "formats": ["blog_article", "twitter_thread", "linkedin_post", "newsletter"],
    "tone": "professional",
    "audience": "decision makers tech",
    "keywords": ["IA", "innovation", "2026"]
  }'
```

L'IA genere chaque format avec des prompts optimises :
- **Blog Article** : 800-1500 mots, structure H1/H2, introduction, sections, conclusion, CTA
- **Twitter Thread** : 8-15 tweets, hook percutant, hashtags, CTA final
- **LinkedIn Post** : paragraphes courts, emojis, question d'engagement
- **Newsletter** : subject line, preview text, corps, CTA button

### Etape 3 : Consulter et editer les contenus

```bash
# Lister les contenus generes
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/content-studio/projects/proj-456-.../contents
```

Dans l'interface `/content-studio`, chaque contenu est affichable avec :
- Bouton **Copier** pour le presse-papier
- Bouton **Editer** pour modifier manuellement
- Bouton **Regenerer** avec des instructions supplementaires

### Etape 4 : Regenerer avec des instructions

Si un contenu ne vous convient pas :

```bash
curl -X POST http://localhost:8004/api/content-studio/contents/content-789-.../regenerate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instructions": "Plus court, ton plus decontracte, ajouter des donnees chiffrees"
  }'
```

### Etape 5 : Creer un pipeline reutilisable

Automatisez ce processus pour de futures transcriptions :

```bash
curl -X POST http://localhost:8004/api/pipelines/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Transcription to Marketing Pack",
    "description": "Genere un pack marketing complet depuis une transcription",
    "steps": [
      {
        "type": "summarize",
        "config": {"language": "fr", "max_length": 500}
      },
      {
        "type": "content_studio",
        "config": {"formats": ["blog_article", "twitter_thread", "linkedin_post"]}
      },
      {
        "type": "security_scan",
        "config": {"auto_redact": true}
      }
    ]
  }'
```

### Etape 6 : Publier sur les reseaux sociaux

1. Connectez vos comptes dans **Social Publisher** (`/social-publisher`)
2. Creez un post depuis le contenu genere :

```bash
# Creer un post planifie
curl -X POST http://localhost:8004/api/social-publisher/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "compte-linkedin-...",
    "content": "Votre post LinkedIn genere...",
    "status": "scheduled",
    "scheduled_at": "2026-04-01T09:00:00Z"
  }'
```

Ou utilisez le **recyclage automatique** depuis Content Studio :

```bash
curl -X POST http://localhost:8004/api/social-publisher/recycle \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_id": "content-789-...",
    "platforms": ["twitter", "linkedin"]
  }'
```

### Resultat final

Vous avez :
- Un article de blog complet depuis votre transcription
- Un thread Twitter pret a publier
- Un post LinkedIn engage
- Une newsletter formatee
- Un pipeline reutilisable pour les prochaines fois
- Des publications planifiees sur les reseaux sociaux

---

## Tutoriel 3 : Deployer un chatbot RAG sur votre site

> **Duree** : 15 minutes
> **Modules utilises** : Knowledge Base, AI Chatbot Builder
> **Pre-requis** : Documents a indexer (TXT, MD, CSV ou PDF)

### Objectif

Creer un chatbot qui repond aux questions des visiteurs de votre site en se basant sur votre documentation, et l'integrer via un widget embeddable.

### Etape 1 : Alimenter la Knowledge Base

Uploadez vos documents de reference :

```bash
# Upload d'un document texte
curl -X POST http://localhost:8004/api/knowledge/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@documentation.md" \
  -F "title=Documentation produit"
```

Repetez pour chaque document (FAQ, guides, specifications, etc.). Chaque document est automatiquement :
- Decoupe en **chunks** intelligents (respect des paragraphes, overlap)
- Indexe en **TF-IDF** (toujours)
- Indexe en **embeddings vectoriels** si pgvector est disponible (384 dimensions)

### Etape 2 : Verifier l'indexation

```bash
# Verifier les modes de recherche disponibles
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/knowledge/search/status

# Reponse : { "tfidf": true, "vector": true, "hybrid": true }

# Tester une recherche
curl -X POST http://localhost:8004/api/knowledge/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "comment configurer le produit", "limit": 5}'
```

### Etape 3 : Tester le RAG

Avant de creer le chatbot, verifiez que le RAG fonctionne bien :

```bash
curl -X POST http://localhost:8004/api/knowledge/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Comment installer le produit sur Windows ?"}'
```

L'IA synthetise une reponse en se basant sur les chunks les plus pertinents de vos documents.

### Etape 4 : Creer le chatbot

```bash
curl -X POST http://localhost:8004/api/chatbots \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Support Bot",
    "description": "Assistant support produit",
    "system_prompt": "Tu es un assistant support pour notre produit. Reponds de maniere concise et precise en te basant uniquement sur la documentation fournie. Si tu ne connais pas la reponse, dis-le clairement.",
    "knowledge_base_ids": ["doc-001", "doc-002", "doc-003"],
    "settings": {
      "welcome_message": "Bonjour ! Comment puis-je vous aider ?",
      "theme_color": "#1976D2",
      "language": "fr"
    }
  }'
```

### Etape 5 : Configurer le chatbot

Ajustez les parametres dans l'interface `/chatbot-builder` :
- **System prompt** : personnalisez le ton et les limites du chatbot
- **Documents sources** : selectionnez les documents de la Knowledge Base
- **Message d'accueil** : le premier message affiche aux visiteurs
- **Couleur du theme** : assortie a votre charte graphique
- **Langue** : francais, anglais, etc.

### Etape 6 : Publier le chatbot

```bash
# Publier et obtenir le token
curl -X POST http://localhost:8004/api/chatbots/chatbot-id-.../publish \
  -H "Authorization: Bearer $TOKEN"

# Reponse : { "embed_token": "tok_abc123...", "status": "published" }
```

### Etape 7 : Recuperer le code embed

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/chatbots/chatbot-id-.../embed-code

# Reponse : snippet HTML/JS a coller sur votre site
```

Le snippet ressemble a :
```html
<script src="https://votre-domaine.com/widget.js"
  data-chatbot-token="tok_abc123..."
  data-theme-color="#1976D2"
  data-language="fr">
</script>
```

### Etape 8 : Integrer sur votre site

1. Copiez le snippet HTML/JS
2. Collez-le juste avant la balise `</body>` de votre site
3. Le widget de chat apparait en bas a droite de la page
4. Les visiteurs peuvent poser des questions sans authentification

### Etape 9 : Suivre les analytics

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/chatbots/chatbot-id-.../analytics
```

Le dashboard affiche :
- Nombre total de conversations
- Questions les plus frequentes
- Taux de satisfaction
- Temps de reponse moyen

### Resultat final

Vous avez :
- Une Knowledge Base alimentee avec vos documents
- Un chatbot RAG configure avec un prompt personnalise
- Un widget embeddable sur votre site
- Un suivi analytics des conversations

Pour mettre a jour les reponses du chatbot, il suffit d'ajouter ou modifier des documents dans la Knowledge Base.

---

## Tutoriel 4 : Analyser un dataset avec l'IA

> **Duree** : 10 minutes
> **Modules utilises** : Data Analyst
> **Pre-requis** : Un fichier CSV, JSON ou Excel avec des donnees

### Objectif

Uploader un dataset, obtenir un profiling automatique, poser des questions en langage naturel et generer un rapport complet.

### Etape 1 : Uploader le dataset

```bash
curl -X POST http://localhost:8004/api/data/datasets \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@ventes_2025.csv" \
  -F "name=Ventes 2025" \
  -F "description=Donnees de ventes annuelles par region"
```

Formats supportes : **CSV**, **JSON**, **Excel** (.xlsx, .xls).

Le dataset est charge dans **DuckDB** (moteur SQL in-memory, 100x plus rapide que pandas) et un apercu est genere automatiquement.

### Etape 2 : Obtenir l'auto-analyse

```bash
curl -X POST http://localhost:8004/api/data/datasets/dataset-id-.../auto-analyze \
  -H "Authorization: Bearer $TOKEN"
```

L'auto-analyse fournit (via ydata-profiling) :
- **Statistiques par colonne** : type, valeurs uniques, min/max, moyenne, mediane, ecart-type
- **Distributions** : histogrammes des valeurs numeriques
- **Valeurs manquantes** : pourcentage et localisation
- **Correlations** : matrice de correlation entre les colonnes numeriques
- **Alertes** : colonnes constantes, haute cardinalite, valeurs aberrantes

### Etape 3 : Poser des questions en langage naturel

C'est la fonctionnalite la plus puissante du module. Posez vos questions comme vous les formuleriez a un analyste :

```bash
# Question 1 : Tendances
curl -X POST http://localhost:8004/api/data/datasets/dataset-id-.../ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle est la tendance des ventes par trimestre ?"}'

# Question 2 : Comparaison
curl -X POST http://localhost:8004/api/data/datasets/dataset-id-.../ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Quelle region a le meilleur taux de croissance ?"}'

# Question 3 : Anomalies
curl -X POST http://localhost:8004/api/data/datasets/dataset-id-.../ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Y a-t-il des valeurs aberrantes dans les montants de vente ?"}'
```

L'IA traduit votre question en requete SQL (via DuckDB), execute la requete, et formule une reponse en langage naturel avec les donnees.

### Etape 4 : Generer un rapport complet

```bash
curl -X POST http://localhost:8004/api/data/datasets/dataset-id-.../report \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sections": ["overview", "trends", "anomalies", "recommendations"],
    "language": "fr"
  }'
```

Le rapport comprend :
- **Vue d'ensemble** : taille du dataset, colonnes, periodes couvertes
- **Tendances** : evolutions cles identifiees par l'IA
- **Anomalies** : valeurs aberrantes et irregularites
- **Recommandations** : actions suggerees par l'IA

### Etape 5 : Consulter l'historique des analyses

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/data/datasets/dataset-id-.../analyses
```

Toutes les analyses (questions, auto-analyse, rapports) sont sauvegardees et consultables.

### Resultat final

Vous avez :
- Un dataset indexe et accessible a tout moment
- Un profiling automatique complet de vos donnees
- Des reponses en langage naturel a vos questions business
- Un rapport d'analyse exportable
- Un historique de toutes les analyses effectuees

---

## Tutoriel 5 : Creer un workflow d'automatisation

> **Duree** : 15 minutes
> **Modules utilises** : AI Workflows, Web Crawler, AI Assistant, Social Publisher
> **Pre-requis** : Compte SaaS-IA

### Objectif

Creer un workflow automatise qui scrape une page web, resume le contenu, le traduit en plusieurs langues, genere des posts sociaux et envoie une notification -- le tout en un seul declenchement.

### Etape 1 : Comprendre la structure d'un workflow

Un workflow est un graphe DAG (Directed Acyclic Graph) compose de :
- **Noeuds** : actions a executer (chacun a un type, une config et des connexions)
- **Edges** : liens entre les noeuds (definissent l'ordre d'execution)
- **Trigger** : ce qui declenche le workflow (manuel, schedule, webhook)

Contrairement aux pipelines (lineaires), les workflows supportent les **branches paralleles** :

```
                    ┌─ Traduire EN ─ Blog EN ─┐
Scraper URL ─ Resumer ─┤                         ├─ Notifier
                    └─ Traduire ES ─ Blog ES ─┘
```

### Etape 2 : Utiliser un template (methode rapide)

Listez les templates disponibles :

```bash
curl http://localhost:8004/api/workflows/templates

# Reponse : 5 templates (YouTube to Blog, Social Media Pack, etc.)
```

Creez un workflow depuis le template "Knowledge Enrichment" :

```bash
curl -X POST http://localhost:8004/api/workflows/from-template/knowledge-enrichment \
  -H "Authorization: Bearer $TOKEN"
```

### Etape 3 : Creer un workflow personnalise

Pour un workflow sur mesure, definissez les noeuds et les edges :

```bash
curl -X POST http://localhost:8004/api/workflows/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Veille concurrentielle automatisee",
    "description": "Scrape, resume, traduit et publie",
    "trigger_type": "manual",
    "nodes": [
      {
        "id": "scrape",
        "type": "crawl",
        "config": {"url": "{{input.url}}"}
      },
      {
        "id": "summarize",
        "type": "summarize",
        "config": {"language": "fr", "max_length": 500}
      },
      {
        "id": "translate_en",
        "type": "translate",
        "config": {"target_language": "en"}
      },
      {
        "id": "translate_es",
        "type": "translate",
        "config": {"target_language": "es"}
      },
      {
        "id": "generate_blog",
        "type": "content_studio",
        "config": {"formats": ["blog_article"]}
      },
      {
        "id": "security_check",
        "type": "security_scan",
        "config": {"auto_redact": true}
      },
      {
        "id": "notify",
        "type": "notify",
        "config": {"message": "Veille terminee : {{summarize.output}}"}
      }
    ],
    "edges": [
      {"from": "scrape", "to": "summarize"},
      {"from": "summarize", "to": "translate_en"},
      {"from": "summarize", "to": "translate_es"},
      {"from": "summarize", "to": "generate_blog"},
      {"from": "translate_en", "to": "security_check"},
      {"from": "translate_es", "to": "security_check"},
      {"from": "generate_blog", "to": "security_check"},
      {"from": "security_check", "to": "notify"}
    ]
  }'
```

**Points cles** :
- Les noeuds `translate_en`, `translate_es` et `generate_blog` s'executent en **parallele** (tous dependant de `summarize`)
- `security_check` attend que les 3 branches soient terminees avant de s'executer
- `{{input.url}}` est remplace par la valeur fournie au declenchement

### Etape 4 : Valider le workflow

Avant d'executer, validez que le DAG est correct (pas de cycles, tous les noeuds connectes) :

```bash
curl -X POST http://localhost:8004/api/workflows/validate \
  -H "Content-Type: application/json" \
  -d '{
    "nodes": [...],
    "edges": [...]
  }'

# Reponse : { "valid": true, "node_count": 7, "edge_count": 8 }
```

La validation utilise **networkx** pour detecter les cycles et verifier la connectivite du graphe.

### Etape 5 : Executer le workflow

```bash
curl -X POST http://localhost:8004/api/workflows/workflow-id-.../run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "url": "https://blog.concurrent.com/article-important"
    }
  }'

# Reponse : { "run_id": "run-xyz-...", "status": "running" }
```

### Etape 6 : Suivre l'execution

```bash
# Verifier le statut global
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/workflows/runs/run-xyz-...

# Reponse : statut par noeud
# {
#   "status": "completed",
#   "node_results": {
#     "scrape": {"status": "completed", "output": "..."},
#     "summarize": {"status": "completed", "output": "..."},
#     "translate_en": {"status": "completed", "output": "..."},
#     "translate_es": {"status": "completed", "output": "..."},
#     "generate_blog": {"status": "completed", "output": "..."},
#     "security_check": {"status": "completed", "output": "..."},
#     "notify": {"status": "completed", "output": "..."}
#   }
# }
```

Dans l'interface `/workflows`, un **Stepper** visuel affiche la progression noeud par noeud avec les resultats.

### Etape 7 : Consulter l'historique des runs

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/workflows/workflow-id-.../runs
```

Chaque run est sauvegarde avec :
- Date de declenchement
- Duree totale
- Statut par noeud (completed, failed, skipped)
- Resultats complets

### Etape 8 : Connecter un webhook externe (optionnel)

Pour declencher le workflow depuis un outil externe (Zapier, Make, n8n) :

1. Creez un connecteur dans **Integration Hub** (`/integrations`)
2. Configurez le trigger pour pointer vers votre workflow
3. L'outil externe envoie un POST vers le webhook SaaS-IA
4. Le workflow se declenche automatiquement avec les donnees recues

```bash
# Creer un connecteur webhook
curl -X POST http://localhost:8004/api/integrations/connectors \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Zapier Trigger",
    "type": "webhook",
    "config": {}
  }'

# Creer un trigger lie au workflow
curl -X POST http://localhost:8004/api/integrations/triggers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "connector_id": "connector-id-...",
    "event_type": "webhook.received",
    "action": "run_workflow",
    "action_config": {
      "workflow_id": "workflow-id-..."
    }
  }'
```

### Resultat final

Vous avez :
- Un workflow DAG avec branches paralleles
- Scraping automatique d'une page web
- Resume et traduction en 2 langues en parallele
- Generation d'un article de blog
- Verification de securite automatique (PII, injection)
- Notification de fin d'execution
- Historique complet des executions
- (Optionnel) Declenchement automatique via webhook externe

---

## Aller plus loin

### Combiner les modules via les Agents

Pour des taches complexes qui necessitent de la planification, utilisez les **Agents** :

```bash
curl -X POST http://localhost:8004/api/agents/react \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "Transcris la video YouTube https://youtube.com/watch?v=XXX, resume-la, genere un article de blog et un thread Twitter, verifie qu il n y a pas de donnees personnelles, puis ajoute le tout a la knowledge base."
  }'
```

L'agent ReAct planifie et execute automatiquement les etapes necessaires via la boucle Think-Act-Observe-Reflect.

### Utiliser les Multi-Agent Crews

Pour des taches collaboratives (recherche + redaction + relecture) :

```bash
# Utiliser le template "Research & Writing Team"
curl -X POST http://localhost:8004/api/crews/from-template/research-writing \
  -H "Authorization: Bearer $TOKEN"

# Lancer la crew
curl -X POST http://localhost:8004/api/crews/crew-id-.../run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "Faire une analyse complete des tendances IA 2026 et rediger un rapport de 2000 mots"
  }'
```

3 agents collaborent sequentiellement : le Researcher cherche, le Writer redige, le Reviewer ameliore.

### Surveiller les performances

Utilisez le **AI Monitoring** (`/monitoring`) pour suivre :
- Quel provider est le plus rapide pour vos taches
- Combien coutent vos appels IA
- Les traces detaillees de chaque appel

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8004/api/monitoring/dashboard
```

### Documentation complementaire

- [Guide utilisateur complet](USER_GUIDE.md)
- [Demarrage rapide](GETTING_STARTED.md)
- [Reference API](API_REFERENCE.md)
- [Architecture technique](ARCHITECTURE.md)
- [Guide de deploiement](DEPLOYMENT.md)
