# SaaS-IA -- Demarrage rapide

> **Temps estime** : 10 minutes pour un environnement fonctionnel, 5 minutes pour le premier tutoriel.

---

## Pre-requis

| Outil | Version minimale | Verification |
|-------|-----------------|--------------|
| **Docker** | 24+ | `docker --version` |
| **Docker Compose** | v2 | `docker compose version` |
| **Node.js** | 18+ | `node --version` |
| **npm** | 9+ | `npm --version` |
| **Python** (optionnel, pour dev backend local) | 3.13 | `python --version` |
| **Git** | 2.30+ | `git --version` |

**Cles API necessaires** (au moins une) :
- **Gemini** : [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey) (tier gratuit disponible)
- **Claude** : [https://console.anthropic.com/](https://console.anthropic.com/)
- **Groq** : [https://console.groq.com/](https://console.groq.com/) (tier gratuit disponible)

---

## 1. Cloner le projet

```bash
git clone https://github.com/votre-org/SaaS-IA.git
cd SaaS-IA
```

---

## 2. Configurer l'environnement

```bash
# Copier le fichier d'exemple
cp mvp/backend/.env.example mvp/backend/.env
```

Editez `mvp/backend/.env` avec vos cles :

```env
# SECURITE (OBLIGATOIRE -- generez une cle forte)
SECRET_KEY=votre-cle-secrete-aleatoire-de-64-caracteres

# Base de donnees (valeurs par defaut Docker, ne pas modifier)
DATABASE_URL=postgresql://saas_ia_user:saas_ia_dev_password@localhost:5435/saas_ia

# Redis (valeur par defaut Docker)
REDIS_URL=redis://localhost:6382

# AI Providers (renseignez au moins un)
GEMINI_API_KEY=votre_cle_gemini
CLAUDE_API_KEY=votre_cle_claude
GROQ_API_KEY=votre_cle_groq

# Transcription (MOCK pour tester sans API payante)
ASSEMBLYAI_API_KEY=MOCK

# Application
ENVIRONMENT=development
DEBUG=True
CORS_ORIGINS=http://localhost:3002,http://localhost:8004
```

> **Astuce** : Pour generer une cle secrete forte :
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(64))"
> ```

---

## 3. Lancer les services

### Option A : Docker Compose (recommande)

```bash
cd mvp
docker compose up -d
```

Cette commande lance 5 services :

| Service | Port | URL |
|---------|------|-----|
| **Backend API** | 8004 | http://localhost:8004 |
| **PostgreSQL 16** | 5435 | localhost:5435 |
| **Redis 7** | 6382 | localhost:6382 |
| **Celery Worker** | - | (arriere-plan) |
| **Flower** | 5555 | http://localhost:5555 |

Verifiez que tout fonctionne :

```bash
# Verifier les containers
docker compose ps

# Verifier la sante de l'API
curl http://localhost:8004/health
# Reponse attendue : {"status": "healthy", ...}

# Verifier les modules charges
curl http://localhost:8004/api/modules
# Reponse attendue : liste des 37 modules
```

### Option B : Backend local (pour le developpement)

```bash
cd mvp/backend

# Creer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Installer les dependances
pip install -r requirements.txt

# Appliquer les migrations
alembic upgrade head

# Lancer le serveur
uvicorn app.main:app --reload --port 8004
```

> **Note** : PostgreSQL et Redis doivent etre lances via Docker meme en mode local :
> ```bash
> docker compose up -d postgres redis
> ```

---

## 4. Lancer le frontend

```bash
cd mvp/frontend

# Installer les dependances
npm install

# Lancer le serveur de developpement
npm run dev
```

Le frontend est accessible sur **http://localhost:3002**.

---

## 5. Premier acces

### Creer un compte

1. Ouvrez http://localhost:3002 dans votre navigateur
2. Cliquez sur **S'inscrire**
3. Renseignez votre email, nom complet et mot de passe
4. Vous etes redirige vers le **Dashboard**

### Verifier via l'API

```bash
# S'inscrire via l'API
curl -X POST http://localhost:8004/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "Demo1234!", "full_name": "Demo User"}'

# Se connecter
curl -X POST http://localhost:8004/api/auth/login \
  -d "username=demo@example.com&password=Demo1234!"
# -> Copiez le access_token de la reponse
```

---

## 6. Tutoriel en 5 minutes

### Etape 1 : Transcrire une video YouTube

1. Allez sur **Transcription** (`/transcription`) dans le menu lateral
2. Collez une URL YouTube (ex: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
3. Selectionnez la langue (ou laissez en auto-detection)
4. Cliquez sur **Transcrire**
5. Attendez la fin du traitement (le statut passe de "processing" a "completed")
6. Consultez le texte transcrit, les chapitres et le resume

### Etape 2 : Generer un article de blog

1. Sur la transcription completee, cliquez sur **"Chat about this"** ou allez dans **Content Studio** (`/content-studio`)
2. Creez un nouveau projet :
   - Source : choisissez votre transcription
3. Selectionnez le format **Blog Article**
4. Cliquez sur **Generer**
5. L'IA produit un article structure a partir de la transcription
6. Editez le contenu si necessaire, puis copiez-le

### Etape 3 : Creer un pipeline

1. Allez dans **Pipelines** (`/pipelines`)
2. Creez un nouveau pipeline : "YouTube to Blog"
3. Ajoutez les steps :
   - Step 1 : `summarize` (resumer la transcription)
   - Step 2 : `content_studio` (generer un blog article)
   - Step 3 : `sentiment` (analyser le ton du contenu)
4. Executez le pipeline
5. Consultez les resultats de chaque etape

Votre premier pipeline est pret. Vous pouvez le reutiliser avec d'autres transcriptions.

---

## 7. Explorer la plateforme

Maintenant que votre environnement est en place, explorez les modules :

| Module | Page | Ce que vous pouvez tester |
|--------|------|--------------------------|
| **Chat** | `/chat` | Conversation IA avec streaming |
| **Compare** | `/compare` | Comparer Gemini vs Claude vs Groq sur un meme prompt |
| **Knowledge** | `/knowledge` | Uploader un document et poser des questions RAG |
| **Content Studio** | `/content-studio` | Generer du contenu dans 10 formats |
| **Workflows** | `/workflows` | Utiliser un template "YouTube to Blog Post" |
| **Images** | `/images` | Generer une image dans 10 styles |
| **Data** | `/data` | Uploader un CSV et poser des questions |
| **Security** | `/security` | Scanner un texte pour detecter les PII |
| **Search** | `/search` | Recherche universelle cross-module |

---

## 8. Documentation Swagger

L'API est entierement documentee et testable via Swagger UI :

- **Swagger UI** : http://localhost:8004/docs
- **ReDoc** : http://localhost:8004/redoc

Cliquez sur **Authorize** dans Swagger, entrez votre token JWT pour tester les endpoints proteges.

---

## Problemes courants et solutions

### Le backend ne demarre pas

**Symptome** : `docker compose up` echoue ou le backend crash au demarrage.

**Solutions** :
1. Verifiez que `SECRET_KEY` est defini dans `.env` (le serveur refuse de demarrer sans)
2. Verifiez que `DATABASE_URL` pointe vers le bon port (5435 par defaut Docker)
3. Consultez les logs : `docker compose logs backend`
4. Verifiez que les ports 8004, 5435, 6382 ne sont pas deja utilises

### La transcription reste en "processing"

**Symptome** : Le job ne se termine jamais.

**Solutions** :
1. Verifiez que le **Celery worker** est actif : `docker compose logs worker`
2. Verifiez la connexion Redis : `docker compose logs redis`
3. En mode MOCK, la transcription retourne un texte de test -- verifiez `ASSEMBLYAI_API_KEY=MOCK` dans `.env`
4. Consultez Flower (http://localhost:5555) pour voir les taches Celery

### Erreur 401 Unauthorized

**Symptome** : Tous les appels API retournent 401.

**Solutions** :
1. Verifiez que votre token JWT n'est pas expire (duree par defaut : 30 minutes)
2. Utilisez le refresh token pour en obtenir un nouveau : `POST /api/auth/refresh`
3. Le frontend gere le refresh automatiquement via l'intercepteur Axios

### Le frontend ne se connecte pas au backend

**Symptome** : Erreurs reseau ou CORS dans la console du navigateur.

**Solutions** :
1. Verifiez que `CORS_ORIGINS` dans `.env` inclut `http://localhost:3002`
2. Verifiez que le backend est accessible : `curl http://localhost:8004/health`
3. Verifiez que le frontend pointe vers le bon port backend (configurez `NEXT_PUBLIC_API_URL` si necessaire)

### Les migrations echouent

**Symptome** : `alembic upgrade head` affiche des erreurs.

**Solutions** :
1. Verifiez que PostgreSQL est accessible sur le port 5435
2. Verifiez les migrations en attente : `alembic current`
3. En cas de conflit, consultez [MIGRATIONS_GUIDE.md](../backend/MIGRATIONS_GUIDE.md)
4. Si pgvector n'est pas installe, la migration vector echouera mais les autres fonctionneront

### Les modules open-source ne sont pas detectes

**Symptome** : Les fallbacks sont utilises au lieu des versions optimisees.

**Explication** : Les modules open-source (pgvector, sentence-transformers, Presidio, Coqui TTS, etc.) sont **optionnels**. Ils sont auto-detectes au demarrage via le pattern `HAS_XXX`. Si la lib n'est pas installee, le fallback est utilise automatiquement.

**Pour installer les libs optionnelles** :
```bash
pip install pgvector sentence-transformers  # Recherche hybride RAG
pip install presidio-analyzer presidio-anonymizer  # PII detection
pip install faster-whisper  # Transcription locale
pip install duckdb ydata-profiling  # Data analysis optimisee
pip install TTS  # Coqui TTS local
```

---

## Prochaines etapes

- Lisez le [Guide Utilisateur complet](USER_GUIDE.md) pour decouvrir tous les modules
- Suivez les [Tutoriels pas-a-pas](TUTORIALS.md) pour des cas d'usage concrets
- Consultez la [Reference API](API_REFERENCE.md) pour l'integration programmatique
- Explorez les [templates de workflows](/workflows) pour automatiser vos taches
