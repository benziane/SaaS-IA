# Module `instagram_intelligence` — Documentation technique

> Créé le 2026-04-10  
> Version 1.0.0  
> Prefix API : `/api/instagram`

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture et fichiers](#2-architecture-et-fichiers)
3. [Pipeline complet](#3-pipeline-complet)
4. [Providers et priorité d'authentification](#4-providers-et-priorité-dauthentification)
5. [API Endpoints](#5-api-endpoints)
6. [Schémas Pydantic](#6-schémas-pydantic)
7. [Modèle base de données](#7-modèle-base-de-données)
8. [Migration Alembic](#8-migration-alembic)
9. [Dépendances et compatibilité](#9-dépendances-et-compatibilité)
10. [Variables d'environnement](#10-variables-denvironnement)
11. [Problèmes rencontrés et solutions](#11-problèmes-rencontrés-et-solutions)
12. [Limitations connues](#12-limitations-connues)

---

## 1. Vue d'ensemble

Le module `instagram_intelligence` permet d'analyser des profils et Reels Instagram publics :

- **Extraction** des métadonnées (likes, vues, caption, thumbnail)
- **Téléchargement** de la vidéo via yt-dlp (gère le streaming DASH d'Instagram)
- **Transcription** audio avec faster-whisper (modèle `tiny`, CPU, quantification int8)
- **Analyse de sentiment** via RoBERTa (`cardiffnlp/twitter-roberta-base-sentiment-latest`)
- **Persistance** en base de données PostgreSQL

### Résultat validé en prod (NatGeo, reel `DWllQsJCPX_`)

```
Provider    : playwright
Likes       : 37 000
Thumbnail   : https://scontent-mrs2-3.cdninstagram.com/...
Language    : en
Transcript  : "To witness something, you've never seen before, it completely
               immerses your senses. Whoa! This is amazing! It's not just noise.
               It has been here. It's nice. And it's most, well, mesmerizing."
Sentiment   : positive (score: 0.977)
```

---

## 2. Architecture et fichiers

```
mvp/backend/app/modules/instagram_intelligence/
├── __init__.py
├── manifest.json          # auto-discovery ModuleRegistry
├── schemas.py             # Pydantic request/response models
├── service.py             # Business logic (799 lignes)
└── routes.py              # FastAPI APIRouter (247 lignes)

mvp/backend/app/models/
└── instagram_intelligence.py   # SQLModel DB table

mvp/backend/alembic/versions/
└── 20260410_0019_add_instagram_reels_table.py
```

### manifest.json

```json
{
  "name": "instagram_intelligence",
  "version": "1.0.0",
  "description": "Instagram content intelligence — download public Reels, transcribe with Whisper, score with RoBERTa sentiment, store vectors for semantic search",
  "prefix": "/api/instagram",
  "tags": ["instagram"],
  "enabled": true,
  "dependencies": ["transcription", "sentiment"]
}
```

---

## 3. Pipeline complet

### 3.1 Analyse d'un Reel (`analyze_reel`)

```
URL Instagram
     │
     ▼
┌─────────────────────────────────────┐
│  1. FETCH METADATA                  │
│     Meta API → Playwright → mock    │
│     (CDN video URL interceptée)     │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  2. DOWNLOAD VIDEO (yt-dlp)         │
│     Gère DASH streams Instagram     │
│     → fichier .mp4 temporaire       │
│     (~11 MB pour 60s)               │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  3. TRANSCRIPTION (faster-whisper)  │
│     Modèle: tiny, CPU, int8         │
│     Auto-détection langue           │
│     → texte + langue détectée       │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  4. SENTIMENT (RoBERTa)             │
│     cardiffnlp/twitter-roberta-base │
│     → label + score [0,1]           │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│  5. PERSIST DB                      │
│     Table instagram_reels           │
│     Lié à user_id                   │
└─────────────────────────────────────┘
```

### 3.2 Pourquoi yt-dlp et pas httpx direct ?

Instagram utilise le streaming **DASH** (Dynamic Adaptive Streaming over HTTP). Les URLs CDN interceptées par Playwright (`cdninstagram.com/*.mp4`) ne sont que des **headers MP4** (moov atom, ~824 bytes). La vidéo complète est découpée en segments. yt-dlp connaît ce protocole et recolle les segments automatiquement.

```
URL CDN interceptée → 824 bytes (header seulement) ❌
yt-dlp sur URL du reel → 11.8 MB (vidéo complète)  ✓
```

### 3.3 Transcription : générateur à matérialiser

```python
# INCORRECT — le générateur reste lazy, tuple index out of range
segments, info = model.transcribe(path)
text = " ".join(seg.text for seg in segments)

# CORRECT — on force l'évaluation complète avant de joindre
segments_gen, info = model.transcribe(path, beam_size=2)
segments = list(segments_gen)  # matérialise le générateur
text = " ".join(seg.text.strip() for seg in segments)
```

### 3.4 Mapping résultat SentimentService

```python
# SentimentService.analyze_text() retourne :
{
    "overall_sentiment": "positive",   # pas "label"
    "overall_score": 0.977,            # pas "score"
    ...
}

# Mapping dans _score_sentiment() :
reel["sentiment_label"] = result.get("overall_sentiment") or result.get("label")
reel["sentiment_score"] = result.get("overall_score") or result.get("score")
```

---

## 4. Providers et priorité d'authentification

```
Priority 1 ── Meta Basic Display API
               INSTAGRAM_ACCESS_TOKEN configuré
               → _fetch_profile_meta_api() / _fetch_reel_meta_api()

Priority 2 ── Playwright (Chromium headless)
               HAS_PLAYWRIGHT = True (playwright installé)
               → _fetch_profile_playwright() / _fetch_reel_playwright()
               Intercept CDN via page.on("response", ...)

Priority 3 ── instagrapi
               HAS_INSTAGRAPI = True (instagrapi installé)
               INSTAGRAM_USERNAME + INSTAGRAM_PASSWORD
               → _fetch_reel_instagrapi()

Priority 4 ── instaloader
               HAS_INSTALOADER = True (instaloader installé)
               → _fetch_reel_instaloader()
               ⚠ Instagram a bloqué l'API GraphQL — fonctionnel sur peu de profils

Priority 5 ── Mock mode
               Aucune lib disponible
               → _mock_profile() / _mock_reel()
               Retourne données structurées vides
```

### Pattern HAS_XXX (auto-detection + fallback)

```python
HAS_PLAYWRIGHT = False
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    pass
```

---

## 5. API Endpoints

Base URL : `/api/instagram`

### POST `/validate`

Vérifie qu'un profil Instagram existe et est public.

```
Rate limit : 30/minute
Auth       : JWT requis
```

**Request body:**
```json
{ "username": "natgeo" }
```

**Response:**
```json
{
  "valid": true,
  "username": "natgeo",
  "exists": true,
  "is_private": false,
  "error": null
}
```

---

### POST `/analyze-profile`

Analyse un profil public : métadonnées + Reels (transcription + sentiment).

```
Rate limit : 5/minute
Auth       : JWT requis + session DB
max_reels  : cappé à 20
```

**Request body:**
```json
{
  "username": "natgeo",
  "max_reels": 5,
  "transcribe": true,
  "language": "auto"
}
```

**Response :** `ProfileReport` (voir §6)

---

### POST `/analyze-reel`

Analyse un Reel par URL.

```
Rate limit : 10/minute
Auth       : JWT requis + session DB
```

**Request body:**
```json
{
  "reel_url": "https://www.instagram.com/natgeo/reel/DWllQsJCPX_/",
  "transcribe": true,
  "language": "auto"
}
```

**Response :** `ReelResult` (voir §6)

---

### GET `/download-video`

Télécharge la vidéo d'un Reel et la stream au client (MP4).

```
Rate limit : 5/minute
Auth       : JWT requis
```

**Query params:**
```
reel_url=https://www.instagram.com/natgeo/reel/DWllQsJCPX_/
```

**Response :** `StreamingResponse` (video/mp4, Content-Disposition: attachment)

**Implémentation :**
- yt-dlp télécharge dans un dossier temporaire (`tempfile.mkdtemp()`)
- Lecture par chunks de 64 KB via générateur Python
- Dossier supprimé après la dernière itération du générateur (finally dans `iter_file`)

---

### GET `/download-thumbnail`

Télécharge la thumbnail/cover image d'un Reel.

```
Rate limit : 20/minute
Auth       : JWT requis
```

**Query params:**
```
reel_url=https://www.instagram.com/natgeo/reel/DWllQsJCPX_/
```

**Response :** `StreamingResponse` (image/jpeg, Content-Disposition: attachment)

**Implémentation :**
- yt-dlp extrait les métadonnées sans télécharger (`skip_download: true`)
- httpx proxifie l'image CDN depuis le serveur backend
- Evite les restrictions CORS/Referer du CDN Instagram

---

## 6. Schémas Pydantic

### `ProfileAnalyzeRequest`
| Champ | Type | Défaut | Description |
|-------|------|--------|-------------|
| username | str | — | Nom d'utilisateur Instagram |
| max_reels | int | 10 | Nombre de Reels à analyser (max 20 en route) |
| transcribe | bool | True | Activer la transcription Whisper |
| language | str | "auto" | Langue cible ("auto", "fr", "en", ...) |

### `ReelDownloadRequest`
| Champ | Type | Défaut | Description |
|-------|------|--------|-------------|
| reel_url | str | — | URL du Reel Instagram |
| transcribe | bool | True | Activer la transcription |
| language | str | "auto" | Langue cible |

### `ReelResult`
| Champ | Type | Description |
|-------|------|-------------|
| reel_id | str | Shortcode Instagram |
| username | str | Compte source |
| caption | str | Légende du post |
| likes | int | Nombre de likes |
| comments | int | Nombre de commentaires |
| views | int | Nombre de vues |
| duration_seconds | float | Durée de la vidéo |
| thumbnail_url | str? | URL CDN de la miniature |
| reel_url | str | URL canonique du Reel |
| transcript | str? | Texte transcrit par Whisper |
| transcript_language | str? | Langue détectée ("en", "fr", ...) |
| sentiment_label | str? | "positive" / "negative" / "neutral" |
| sentiment_score | float? | Score RoBERTa [0.0, 1.0] |
| provider | str | Source des données ("playwright", "meta_api", "mock", ...) |

### `ProfileReport`
| Champ | Type | Description |
|-------|------|-------------|
| username | str | Nom d'utilisateur |
| full_name | str | Nom complet |
| bio | str | Biographie |
| followers | int | Nombre d'abonnés |
| following | int | Nombre d'abonnements |
| post_count | int | Nombre de posts |
| reels_analyzed | int | Nombre de Reels analysés |
| reels | list[ReelResult] | Détail de chaque Reel |
| avg_sentiment_score | float? | Score moyen sur tous les Reels |
| top_topics | list[str] | Top 10 hashtags/mots-clés |

### `ValidateProfileResult`
| Champ | Type | Description |
|-------|------|-------------|
| valid | bool | True si le profil est accessible |
| username | str | Nom normalisé |
| exists | bool | True si le compte existe |
| is_private | bool | True si le compte est privé |
| error | str? | Message d'erreur si échec |

---

## 7. Modèle base de données

**Table :** `instagram_reels`

```python
class InstagramReel(SQLModel, table=True):
    __tablename__ = "instagram_reels"

    id              : UUID      # PK, default uuid4
    user_id         : UUID      # FK vers users, indexed
    username        : str(100)  # indexed
    reel_id         : str(100)  # shortcode Instagram, indexed
    reel_url        : str(500)
    caption         : str(2200)
    likes           : int = 0
    comments        : int = 0
    views           : int = 0
    duration_seconds: float = 0.0
    thumbnail_url   : str(500)?
    transcript      : Text?
    transcript_language: str(10)?
    sentiment_label : str(20)?
    sentiment_score : float?
    provider        : str(50) = "mock"
    created_at      : datetime
```

**Index :**
- `ix_instagram_reels_user_id`
- `ix_instagram_reels_username`
- `ix_instagram_reels_reel_id`

---

## 8. Migration Alembic

**Fichier :** `alembic/versions/20260410_0019_add_instagram_reels_table.py`

```
Revision ID : instagram_reels_019
Revises     : email_verified_018
Created     : 2026-04-10
```

**Appliquer :**
```bash
cd mvp/backend
PYTHONPATH=/app alembic upgrade head
# ou depuis Docker :
docker compose exec saas-ia-backend alembic upgrade head
```

**Annuler :**
```bash
alembic downgrade email_verified_018
```

---

## 9. Dépendances et compatibilité

### Python 3.14 — problèmes résolus

| Problème | Cause | Solution |
|----------|-------|----------|
| `passlib` cassé | `ValueError: password cannot be longer than 72 bytes` dans `detect_wrap_bug` | Remplacé par `bcrypt` direct dans `app/auth.py` |
| `lxml 5.x` pas de wheel Py3.14 | `streamlink` et `crawl4ai` pinent `lxml<6` | `uv pip install --override lxml>=6.0.0` dans Dockerfile |
| `datetime` timezone-aware/naive | asyncpg rejette les datetimes timezone-aware | `.replace(tzinfo=None)` sur les `default_factory` des modèles SQLModel |
| `playwright` non installé pour Py3.14 | Installé dans le site-packages Py3.13 uniquement | `python -m pip install playwright && python -m playwright install chromium` |
| `transformers` / `faster-whisper` manquants | Idem, site-packages Py3.13 | `python -m pip install transformers faster-whisper torch --index-url .../cpu` |

### Libs utilisées

| Lib | Usage | Fallback |
|-----|-------|----------|
| `playwright` 1.58 | Scraping headless, interception CDN | mock mode |
| `yt-dlp` 2026.03 | Téléchargement vidéo DASH Instagram | — |
| `faster-whisper` 1.2 | Transcription audio (tiny/CPU/int8) | "" vide |
| `transformers` 5.5 | RoBERTa sentiment (via SentimentService) | SentimentService fallback LLM |
| `instaloader` | Profils publics (API GraphQL morte) | Playwright |
| `httpx` | Download thumbnail proxy | — |

### Dockerfile (extrait clé)

```dockerfile
# lxml 6.x override — crawl4ai et streamlink pinent lxml<6, pas de wheel Py3.14
RUN echo "lxml>=6.0.0" > /tmp/lxml_override.txt
RUN uv pip install --no-cache \
        --override /tmp/lxml_override.txt \
        -r /tmp/requirements.txt

# Playwright Chromium
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install chromium --with-deps

# Runtime : libs X11 pour Chromium headless
RUN apt-get install -y libxcomposite1 libxdamage1 libxrandr2 libxfixes3 \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libatspi2.0-0
```

---

## 10. Variables d'environnement

Ajoutées dans `app/config.py` et `docker-compose.yml` (`x-backend-env`) :

```env
# Option 1 : Playwright login (headless browser)
INSTAGRAM_USERNAME=benziane.dev@gmail.com
INSTAGRAM_PASSWORD=...

# Option 2 : Meta Basic Display API
INSTAGRAM_APP_ID=
INSTAGRAM_APP_SECRET=
INSTAGRAM_ACCESS_TOKEN=
```

> **Note :** Le login Playwright headless est bloqué par la protection anti-bot d'Instagram. Les téléchargements anonymes (yt-dlp sans session) fonctionnent pour les profils publics.

---

## 11. Problèmes rencontrés et solutions

### 11.1 instaloader mort

Instagram a bloqué l'API GraphQL non officielle en 2024. `instaloader` retourne des erreurs `401` / profils vides pour la quasi-totalité des comptes.

**Solution :** Playwright headless pour intercepter les requêtes réseau.

### 11.2 URLs CDN Instagram expirées

Les URLs `cdninstagram.com/*.mp4` interceptées par Playwright expirent en **~1 heure**. Un download httpx sur une URL stockée retourne 818 bytes (page d'erreur).

**Solution :** Toujours refaire un fetch Playwright frais + utiliser yt-dlp sur l'URL **du reel** (pas l'URL CDN).

### 11.3 DASH streaming — vidéo tronquée

Même avec une URL CDN valide, httpx ne télécharge que le **header MP4** (~824 bytes — le moov atom DASH). Le reste est streamé par segments.

```
httpx GET cdninstagram.com/...mp4 → 824 bytes (invalide pour Whisper)
yt-dlp sur instagram.com/reel/... → 11.8 MB (vidéo complète)
```

**Solution :** yt-dlp avec `format: "best"` sur l'URL du reel (pas besoin de ffmpeg si format unique).

### 11.4 Login Instagram headless bloqué

Playwright headless est détecté comme bot par Instagram (`"The login information you entered is incorrect"` alors que les credentials sont corrects).

**Solution :** Utiliser yt-dlp sans session pour les profils publics. Pour les profils privés, exporter les cookies via extension navigateur (`Get cookies.txt LOCALLY`) et les passer à yt-dlp via `--cookies`.

### 11.5 Playwright non disponible en Py3.14

```bash
# playwright était installé dans Python 3.13 user site-packages
# Py3.14 ne le trouvait pas → HAS_PLAYWRIGHT = False

python -m pip install playwright playwright-stealth
python -m playwright install chromium
```

### 11.6 `tuple index out of range` dans faster-whisper

faster-whisper retourne un **générateur lazy** pour les segments. Si l'audio est invalide (fichier tronqué), l'itération échoue avec `tuple index out of range` au niveau PyAV.

**Solution :** `segments = list(segments_gen)` pour matérialiser avant de traiter.

---

## 12. Limitations connues

| Limitation | Statut |
|------------|--------|
| Login headless bloqué par Instagram | Workaround : cookies manuels ou profils publics anonymes |
| Profils privés inaccessibles | Par design Instagram — nécessite session authentifiée |
| Carousel (posts multi-images) | Non supporté — yt-dlp nécessite session pour `/p/` URLs |
| Whisper `tiny` CPU ~7s pour 60s vidéo | Acceptable en dev, utiliser `small`/`medium` en prod |
| CDN URLs expirées après ~1h | Toujours refetch via Playwright avant téléchargement |
| `shortcode` None dans les résultats Playwright | Extraction JS non implémentée, non bloquant |
| `views` toujours 0 depuis Playwright | Non exposé dans les meta OG d'Instagram |

---

## 13. Analyse comparative des libs testées

Résumé des tests effectués (2026-04-10) sur les principales libs du domaine :

| Lib | Stars | Reels publics | Posts `/p/` | Carousel | Login headless | Statut |
|-----|-------|---------------|-------------|----------|----------------|--------|
| **yt-dlp** | ~100k | ✅ anonyme | ❌ session requise | ❌ session requise | N/A | **Utilisé** |
| **gallery-dl** | ~17k | ❌ redirige login | ❌ session requise | ❌ session requise | ❌ bloqué | Testé, écarté |
| **instaloader** | ~9k | ❌ API GraphQL morte | ❌ API GraphQL morte | ❌ | ❌ bloqué | Dans le code (fallback mort) |
| **instagrapi** | ~6k | Partiel | ✅ avec session | ✅ avec session | ❌ IP blacklistée | Testé, écarté |
| **Playwright** | — | ✅ métadonnées | ❌ pas de download | ❌ | ❌ bot détecté | **Utilisé** pour métadonnées |

### Ce qui fonctionne vraiment (sans session)

```
Reels publics (/reel/) :
  yt-dlp           → vidéo complète ✅ (11.8 MB, DASH segments recolés)
  Playwright       → métadonnées + thumbnail ✅ (CDN URL interceptée)

Posts photos (/p/) :
  Tous les outils  → session Instagram requise ❌
```

### Débloquer les carousels (roadmap)

Pour supporter les posts multi-images, deux options :

**Option A — Cookies manuels** (recommandée)
```bash
# 1. Exporter cookies depuis Chrome connecté à Instagram
#    Extension : "Get cookies.txt LOCALLY"
# 2. Sauvegarder dans mvp/backend/instagram_cookies.txt
# 3. yt-dlp l'utilisera automatiquement si configuré :
yt-dlp --cookies instagram_cookies.txt https://www.instagram.com/p/xxx/
```

**Option B — Session instagrapi** (si IP non blacklistée)
```python
from instagrapi import Client
cl = Client()
cl.login(username, password)
media = cl.media_pk_from_url(url)
info = cl.media_info(media)
resources = info.resources  # liste des images/vidéos du carousel
```
