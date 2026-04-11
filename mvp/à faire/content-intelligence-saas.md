# Content Intelligence SaaS — Implémentation Complète

> **Document de référence — De la conception à la validation finale**
> Stack : FastAPI (async) + React/TypeScript + PostgreSQL + Redis + Celery + Docker
> Auteur : Ibz | Date : Avril 2026

---

## Table des matières

1. [Vision Produit](#1-vision-produit)
2. [Architecture Globale](#2-architecture-globale)
3. [Base de données](#3-base-de-données)
4. [Backend FastAPI](#4-backend-fastapi)
5. [Workers Celery — Pipeline async](#5-workers-celery--pipeline-async)
6. [Intégrations externes](#6-intégrations-externes)
7. [Frontend React](#7-frontend-react)
8. [Infrastructure Docker](#8-infrastructure-docker)
9. [Sécurité & Multi-tenant](#9-sécurité--multi-tenant)
10. [Observabilité](#10-observabilité)
11. [Modèle économique](#11-modèle-économique)
12. [Plan de build](#12-plan-de-build)
13. [Checklist de validation finale](#13-checklist-de-validation-finale)

---

## 1. Vision Produit

### Concept

**Content Intelligence SaaS** — plateforme tout-en-un qui analyse automatiquement n'importe quel contenu vidéo (Instagram Reels, YouTube, TikTok) et génère un brief complet de repurpose adapté à l'audience cible.

### Proposition de valeur

- Input : une URL → Output : rapport complet + script prêt à tourner
- Pipeline full-auto : scraping → transcription → analyse visuelle → enrichissement → rapport → repurpose
- Multi-plateforme : Instagram, TikTok, YouTube en une seule interface

### Personas cibles

- Créateurs de contenu francophones (solopreneurs, agences)
- Community managers gérant plusieurs comptes
- Agences IA proposant de la veille concurrentielle

### Features core (MVP)

| Feature | Description |
|---------|-------------|
| URL Analyzer | Analyse multi-plateforme en 1 URL |
| Auto Transcript | Transcription Whisper API |
| Visual Report | Analyse frame par frame Claude Vision |
| Web Enrichment | Recherche automatique des sources/outils mentionnés |
| Repurpose Engine | Génération de script adapté audience cible |
| Report Export | Export Markdown / PDF du rapport |

---

## 2. Architecture Globale

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│              React + TypeScript + Tailwind                  │
│   Dashboard │ Analyzer │ Report Viewer │ Script Editor      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS / WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│                   FASTAPI (async)                           │
│         Auth │ Routes │ Schemas │ Middleware               │
└──────┬────────────────┬────────────────────┬───────────────┘
       │                │                    │
┌──────▼──────┐  ┌──────▼──────┐   ┌────────▼────────┐
│  PostgreSQL  │  │    Redis    │   │  Celery Workers  │
│  (données)   │  │  (cache +   │   │  (pipeline async)│
│              │  │  job queue) │   │                  │
└─────────────┘  └─────────────┘   └────────┬─────────┘
                                             │
              ┌──────────────────────────────┼──────────────────────────────┐
              │                             │                               │
    ┌─────────▼─────────┐      ┌────────────▼──────────┐      ┌───────────▼──────────┐
    │  Apify API         │      │  OpenAI Whisper API   │      │  Anthropic Claude    │
    │  (scraping multi-  │      │  (transcription)      │      │  (vision + rapport   │
    │   plateforme)      │      │                       │      │   + repurpose)       │
    └───────────────────┘      └───────────────────────┘      └──────────────────────┘
              │
    ┌─────────▼─────────┐      ┌────────────────────────┐
    │  Tavily / Serper   │      │  S3 / MinIO            │
    │  (web search)      │      │  (frames, audio, MP4)  │
    └───────────────────┘      └────────────────────────┘
```

### Pipeline de traitement

```
URL Input
   │
   ▼ Step 1 — SCRAPING (Apify)
   │  → Métadonnées, caption, videoUrl, engagement, hashtags
   │
   ▼ Step 2 — DOWNLOAD (yt-dlp + ffmpeg)
   │  → MP4 téléchargé → audio MP3 extrait → frames JPG extraites
   │
   ▼ Step 3 — TRANSCRIPTION (Whisper API)
   │  → Transcript texte brut (langue originale)
   │
   ▼ Step 4 — VISUAL ANALYSIS (Claude Vision)
   │  → Analyse frame par frame → tableau timestamp/description/outils
   │
   ▼ Step 5 — WEB ENRICHMENT (Tavily)
   │  → Recherche sur chaque outil/personne/concept identifié
   │  → Site officiel, GitHub, pricing, source originale du créateur
   │
   ▼ Step 6 — REPORT GENERATION (Claude Sonnet)
   │  → Rapport structuré complet en Markdown
   │
   ▼ Step 7 — REPURPOSE ENGINE (Claude Sonnet)
   │  → Script adapté à l'audience cible + format + CTA
   │
   ▼ Output → Rapport sauvegardé en DB + stockage fichier
```

---

## 3. Base de données

### Schéma PostgreSQL

```sql
-- Utilisateurs (multi-tenant)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'free',         -- free | starter | pro | agency
    analyses_used INTEGER DEFAULT 0,
    analyses_limit INTEGER DEFAULT 5,        -- selon plan
    api_keys JSONB DEFAULT '{}',             -- Apify, OpenAI (chiffrés AES)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Jobs d'analyse
CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    platform VARCHAR(50),                    -- instagram | tiktok | youtube
    status VARCHAR(50) DEFAULT 'queued',     -- queued | processing | done | failed
    current_step VARCHAR(100),               -- scraping | downloading | transcribing | ...
    progress INTEGER DEFAULT 0,              -- 0-100
    options JSONB DEFAULT '{}',              -- transcribe, visual_analysis, enrich, repurpose
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rapports générés
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Métadonnées scrappées
    creator_username VARCHAR(255),
    creator_fullname VARCHAR(255),
    post_url TEXT,
    post_date TIMESTAMPTZ,
    post_type VARCHAR(50),                   -- reel | carousel | image
    duration_seconds INTEGER,
    likes_count INTEGER,
    comments_count INTEGER,
    hashtags TEXT[],
    mentions TEXT[],
    caption TEXT,

    -- Contenu extrait
    transcript TEXT,
    frames_analysis JSONB,                   -- [{timestamp, description, tools, text_on_screen}]
    enrichment JSONB,                        -- {topic: {site, github, pricing, source}}

    -- Outputs LLM
    report_markdown TEXT,
    repurpose_script TEXT,

    -- Fichiers (S3 keys)
    video_s3_key TEXT,
    audio_s3_key TEXT,
    frames_s3_prefix TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pour performances
CREATE INDEX idx_jobs_user_status ON analysis_jobs(user_id, status);
CREATE INDEX idx_reports_user ON reports(user_id, created_at DESC);
```

### Redis — Structure des clés

```
# Status d'un job (TTL 24h)
job:{job_id}:status     → "processing"
job:{job_id}:step       → "transcribing"
job:{job_id}:progress   → "45"

# Cache résultats Apify (TTL 1h — même URL = pas de double scrape)
apify:cache:{url_hash}  → JSON scraped data

# Rate limiting par user
ratelimit:{user_id}:{date}  → count
```

---

## 4. Backend FastAPI

### Structure des fichiers

```
app/
├── main.py
├── api/
│   ├── deps.py                  # get_current_user, get_db
│   └── routes/
│       ├── auth.py              # POST /auth/register, /auth/login, /auth/refresh
│       ├── analysis.py          # POST /analyze, GET /analyze/{job_id}
│       ├── reports.py           # GET /reports, GET /reports/{id}, DELETE /reports/{id}
│       ├── repurpose.py         # POST /repurpose/{report_id}
│       ├── settings.py          # GET/PUT /settings/api-keys
│       └── webhooks.py          # POST /webhooks/stripe
├── services/
│   ├── scraper.py               # Apify multi-platform wrapper
│   ├── downloader.py            # yt-dlp + ffmpeg
│   ├── transcriber.py           # Whisper REST API
│   ├── vision.py                # Claude Vision frames
│   ├── researcher.py            # Tavily web search
│   ├── reporter.py              # Claude rapport structuré
│   ├── repurposer.py            # Claude script repurpose
│   └── storage.py               # S3 / MinIO upload/download
├── workers/
│   ├── celery_app.py            # Config Celery
│   └── tasks.py                 # Pipeline tasks
├── models/
│   ├── user.py
│   ├── job.py
│   └── report.py
├── schemas/
│   ├── analysis.py
│   ├── report.py
│   └── auth.py
└── core/
    ├── config.py                # Settings (pydantic BaseSettings)
    ├── security.py              # JWT, password hashing
    ├── crypto.py                # AES encrypt/decrypt API keys users
    └── database.py              # AsyncSession setup
```

### Endpoints principaux

```python
# POST /analyze
# Lance le pipeline complet sur une URL
Request:
{
  "url": "https://www.instagram.com/reel/XXX/",
  "options": {
    "transcribe": true,
    "visual_analysis": true,
    "enrich": true,
    "repurpose": true,
    "repurpose_audience": "créateurs de contenu francophones tech"
  }
}

Response 202 Accepted:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "estimated_seconds": 60,
  "ws_url": "wss://api.yoursaas.com/ws/jobs/550e8400..."
}

# GET /analyze/{job_id}
# Polling status (ou WebSocket pour temps réel)
Response:
{
  "job_id": "...",
  "status": "processing",
  "current_step": "transcribing",
  "progress": 45,
  "report_id": null   # null tant que pas fini
}

# GET /reports/{id}
# Rapport complet
Response:
{
  "id": "...",
  "creator_username": "chase.h.ai",
  "post_url": "...",
  "transcript": "Here's the secret trick...",
  "frames_analysis": [...],
  "report_markdown": "# 📋 RAPPORT...",
  "repurpose_script": "# 🎬 SCRIPT REPURPOSE...",
  ...
}
```

### WebSocket — Progression temps réel

```python
# app/api/routes/ws.py
@router.websocket("/ws/jobs/{job_id}")
async def job_progress_ws(
    websocket: WebSocket,
    job_id: str,
    token: str = Query(...),
    redis: Redis = Depends(get_redis)
):
    await websocket.accept()
    
    while True:
        status = await redis.get(f"job:{job_id}:status")
        step = await redis.get(f"job:{job_id}:step")
        progress = await redis.get(f"job:{job_id}:progress")
        
        await websocket.send_json({
            "status": status,
            "step": step,
            "progress": int(progress or 0)
        })
        
        if status in ["done", "failed"]:
            break
            
        await asyncio.sleep(1.5)
    
    await websocket.close()
```

---

## 5. Workers Celery — Pipeline async

### Celery config

```python
# app/workers/celery_app.py
from celery import Celery

celery_app = Celery(
    "content_intelligence",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/1",
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Paris",
    task_track_started=True,
    task_soft_time_limit=300,     # 5 min max par job
    task_time_limit=360,
    worker_prefetch_multiplier=1,  # 1 job par worker (évite surcharge mémoire)
)
```

### Pipeline principal

```python
# app/workers/tasks.py
@celery_app.task(bind=True, name="run_analysis_pipeline")
def run_analysis_pipeline(self, job_id: str, url: str, options: dict, user_keys: dict):
    """
    Pipeline complet : scraping → download → transcription → vision → research → rapport → repurpose
    """
    
    async def _run():
        db = await get_async_db()
        redis = await get_redis()
        
        async def update(step: str, progress: int):
            await redis.set(f"job:{job_id}:step", step)
            await redis.set(f"job:{job_id}:progress", str(progress))
            await db.execute(
                update(AnalysisJob).where(AnalysisJob.id == job_id)
                .values(current_step=step, progress=progress)
            )
        
        try:
            await redis.set(f"job:{job_id}:status", "processing")

            # STEP 1 — Scraping
            await update("scraping", 5)
            post_data = await scraper.scrape(url, apify_token=user_keys["apify"])

            # STEP 2 — Download + extract audio + frames
            await update("downloading", 15)
            media = await downloader.process(post_data["videoUrl"], job_id)
            # media = {video_path, audio_path, frames_dir, frames_paths}

            # STEP 3 — Transcription
            transcript = ""
            if options.get("transcribe") and media.get("audio_path"):
                await update("transcribing", 30)
                transcript = await transcriber.transcribe(
                    media["audio_path"],
                    openai_key=user_keys["openai"]
                )

            # STEP 4 — Visual analysis
            frames_analysis = []
            if options.get("visual_analysis") and media.get("frames_paths"):
                await update("analyzing_frames", 50)
                frames_analysis = await vision.analyze_frames(media["frames_paths"])

            # STEP 5 — Web enrichment
            enrichment = {}
            if options.get("enrich"):
                await update("researching", 65)
                enrichment = await researcher.enrich(transcript, frames_analysis)

            # STEP 6 — Rapport
            await update("generating_report", 80)
            report_md = await reporter.generate(
                post_data=post_data,
                transcript=transcript,
                frames_analysis=frames_analysis,
                enrichment=enrichment
            )

            # STEP 7 — Repurpose
            repurpose_script = ""
            if options.get("repurpose"):
                await update("generating_script", 92)
                repurpose_script = await repurposer.generate(
                    report_markdown=report_md,
                    audience=options.get("repurpose_audience", "")
                )

            # Upload médias vers S3
            await update("uploading", 97)
            s3_keys = await storage.upload_media(job_id, media)

            # Sauvegarder rapport en DB
            report = Report(
                job_id=job_id,
                transcript=transcript,
                frames_analysis=frames_analysis,
                enrichment=enrichment,
                report_markdown=report_md,
                repurpose_script=repurpose_script,
                **s3_keys,
                **extract_metadata(post_data)
            )
            db.add(report)
            await db.commit()

            # Finalisation
            await redis.set(f"job:{job_id}:status", "done")
            await redis.set(f"job:{job_id}:progress", "100")
            await db.execute(
                update(AnalysisJob).where(AnalysisJob.id == job_id)
                .values(status="done", progress=100, completed_at=datetime.utcnow())
            )

        except Exception as e:
            await redis.set(f"job:{job_id}:status", "failed")
            await db.execute(
                update(AnalysisJob).where(AnalysisJob.id == job_id)
                .values(status="failed", error_message=str(e))
            )
            raise

    asyncio.run(_run())
```

---

## 6. Intégrations externes

### 6.1 Scraper multi-plateforme (Apify)

```python
# app/services/scraper.py

APIFY_ACTORS = {
    "instagram": "apify~instagram-scraper",
    "tiktok": "clockworks~tiktok-scraper",
    "youtube": "bernardo~youtube-scraper"
}

def detect_platform(url: str) -> str:
    if "instagram.com" in url: return "instagram"
    if "tiktok.com" in url: return "tiktok"
    if "youtube.com" in url or "youtu.be" in url: return "youtube"
    raise ValueError(f"Plateforme non supportée : {url}")

async def scrape(url: str, apify_token: str) -> dict:
    # Vérifier cache Redis d'abord
    cache_key = f"apify:cache:{hashlib.md5(url.encode()).hexdigest()}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    platform = detect_platform(url)
    actor = APIFY_ACTORS[platform]

    payload = build_payload(platform, url)

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items",
            params={"token": apify_token},
            json=payload
        )
        response.raise_for_status()
        data = response.json()

    if not data:
        raise ValueError("Apify n'a retourné aucune donnée — post privé ou URL invalide")

    result = normalize_response(platform, data[0])

    # Cache 1h
    await redis.setex(cache_key, 3600, json.dumps(result))
    return result

def normalize_response(platform: str, raw: dict) -> dict:
    """Normalise les réponses Apify vers un format unifié"""
    if platform == "instagram":
        return {
            "url": raw.get("url"),
            "creator_username": raw.get("ownerUsername"),
            "creator_fullname": raw.get("ownerFullName"),
            "caption": raw.get("caption", ""),
            "videoUrl": raw.get("videoUrl"),
            "displayUrl": raw.get("displayUrl"),
            "likesCount": raw.get("likesCount", 0),
            "commentsCount": raw.get("commentsCount", 0),
            "timestamp": raw.get("timestamp"),
            "hashtags": raw.get("hashtags", []),
            "mentions": raw.get("mentions", []),
            "type": "reel" if raw.get("videoUrl") else "image"
        }
    # TikTok / YouTube → mappings similaires
    ...
```

### 6.2 Download + extraction (yt-dlp + ffmpeg)

```python
# app/services/downloader.py

async def process(video_url: str, job_id: str) -> dict:
    base_dir = Path(f"/tmp/jobs/{job_id}")
    base_dir.mkdir(parents=True, exist_ok=True)

    video_path = base_dir / "video.mp4"
    audio_path = base_dir / "audio.mp3"
    frames_dir = base_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    # Download vidéo
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp", "-o", str(video_path), "--quiet", video_url,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()

    if not video_path.exists():
        # Fallback : curl direct (pour les URLs Apify directes)
        proc = await asyncio.create_subprocess_exec(
            "curl", "-L", "-o", str(video_path), video_url,
            stdout=asyncio.subprocess.PIPE
        )
        await proc.communicate()

    # Extraire audio
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", str(video_path),
        "-vn", "-ar", "16000", "-ac", "1", "-b:a", "64k",
        str(audio_path), "-y",
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.communicate()

    # Extraire frames (1 frame / 3 secondes)
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", str(video_path),
        "-vf", "fps=1/3,scale=540:-1",
        str(frames_dir / "frame_%03d.jpg"), "-y",
        stderr=asyncio.subprocess.DEVNULL
    )
    await proc.communicate()

    frames_paths = sorted(frames_dir.glob("frame_*.jpg"))

    return {
        "video_path": str(video_path),
        "audio_path": str(audio_path) if audio_path.exists() else None,
        "frames_dir": str(frames_dir),
        "frames_paths": [str(p) for p in frames_paths]
    }
```

### 6.3 Transcription Whisper

```python
# app/services/transcriber.py

async def transcribe(audio_path: str, openai_key: str) -> str:
    async with aiofiles.open(audio_path, "rb") as f:
        audio_data = await f.read()

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {openai_key}"},
            files={"file": ("audio.mp3", audio_data, "audio/mpeg")},
            data={"model": "whisper-1", "response_format": "text"}
        )
        response.raise_for_status()
        return response.text.strip()
```

### 6.4 Analyse visuelle (Claude Vision)

```python
# app/services/vision.py

VISION_PROMPT = """Analyse cette frame extraite d'une vidéo. Décris de façon structurée :
1. Ce qui est visible à l'écran (UI, visage, code, présentation, demo)
2. Tous les textes lisibles (titres, sous-titres, code, URLs, noms)
3. Outils, produits ou services identifiables (logos, noms d'apps)
4. Style visuel (couleurs dominantes, split-screen, overlay, plein écran)

Réponds en JSON avec les clés : description, text_on_screen, tools_visible, visual_style"""

async def analyze_frames(frames_paths: list[str]) -> list[dict]:
    client = AsyncAnthropic()
    results = []

    for i, frame_path in enumerate(frames_paths):
        async with aiofiles.open(frame_path, "rb") as f:
            frame_data = await f.read()
        b64 = base64.b64encode(frame_data).decode()

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": b64
                    }},
                    {"type": "text", "text": VISION_PROMPT}
                ]
            }]
        )

        try:
            analysis = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            analysis = {"description": response.content[0].text}

        results.append({
            "timestamp": f"{i*3}-{i*3+3}s",
            **analysis
        })

    return results
```

### 6.5 Enrichissement web (Tavily)

```python
# app/services/researcher.py

async def enrich(transcript: str, frames_analysis: list[dict]) -> dict:
    # Extraire les sujets clés via Claude
    topics = await extract_topics(transcript, frames_analysis)

    results = {}
    async with httpx.AsyncClient(timeout=30) as client:
        for topic in topics[:8]:  # Max 8 recherches pour maîtriser les coûts
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.TAVILY_API_KEY,
                    "query": f"{topic} official site pricing github 2026",
                    "max_results": 3,
                    "include_answer": True
                }
            )
            data = response.json()
            results[topic] = {
                "answer": data.get("answer"),
                "sources": [
                    {"url": r["url"], "title": r["title"], "snippet": r["content"][:300]}
                    for r in data.get("results", [])
                ]
            }

    return results

async def extract_topics(transcript: str, frames_analysis: list[dict]) -> list[str]:
    """Utilise Claude pour identifier les sujets à rechercher"""
    client = AsyncAnthropic()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""Extrait les 5-8 sujets principaux (outils, produits, personnes, concepts) 
            mentionnés dans ce contenu. Retourne uniquement une liste JSON de strings.
            
            Transcript: {transcript[:1000]}
            Frames analysis: {json.dumps(frames_analysis[:5])}"""
        }]
    )
    try:
        return json.loads(response.content[0].text)
    except:
        return []
```

### 6.6 Génération rapport + repurpose (Claude Sonnet)

```python
# app/services/reporter.py

REPORT_SYSTEM_PROMPT = """Tu es un expert en analyse de contenu pour créateurs francophones.
Tu génères des rapports structurés, précis et actionnables en Markdown.
Le rapport est toujours en français, le transcript reste dans sa langue originale."""

REPORT_PROMPT_TEMPLATE = """
Génère un rapport complet de contenu basé sur ces données :

## Métadonnées
{metadata}

## Transcript
{transcript}

## Analyse visuelle frame par frame
{frames_analysis}

## Enrichissement web
{enrichment}

Structure du rapport attendue :
# 📋 RAPPORT DE CONTENU — @[creator_username]
## 📊 MÉTADONNÉES
## 📝 DESCRIPTION ORIGINALE
## 🎙️ TRANSCRIPT
## 🎬 ANALYSE VISUELLE
### Style du contenu
### Décomposition frame par frame (tableau markdown)
## 🔍 SUJETS & RESSOURCES IDENTIFIÉS
## 🧠 ANALYSE DU CONTENU
### Structure du script (Hook / Corps / CTA)
### Ce qui fonctionne
### Ce qui peut être amélioré
### Angle de repurpose suggéré
## 🔗 TOUTES LES URLS COLLECTÉES
"""

async def generate(post_data: dict, transcript: str, 
                   frames_analysis: list, enrichment: dict) -> str:
    client = AsyncAnthropic()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=REPORT_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": REPORT_PROMPT_TEMPLATE.format(
                metadata=json.dumps(post_data, ensure_ascii=False),
                transcript=transcript,
                frames_analysis=json.dumps(frames_analysis, ensure_ascii=False),
                enrichment=json.dumps(enrichment, ensure_ascii=False)
            )
        }]
    )
    return response.content[0].text
```

```python
# app/services/repurposer.py

REPURPOSE_PROMPT = """
Tu es un expert en création de contenu court pour réseaux sociaux.
À partir du rapport ci-dessous, génère un script adapté pour l'audience cible.

Rapport :
{report_markdown}

Audience cible : {audience}

Génère un script complet avec :
# 🎬 SCRIPT REPURPOSE

## 🎯 ANGLE CHOISI
[Quel angle tu prends et pourquoi c'est différent de l'original]

## 🪝 HOOK (0-3s)
[Phrase d'accroche percutante]

## 📖 CORPS (3-35s)
[Script mot-à-mot, naturel, en français]

## 📣 CTA (35-45s)
[Call-to-action adapté]

## 🎥 NOTES RÉALISATION
- Format recommandé : [split-screen / facecam / screencast]
- Exemple à montrer : [quoi montrer à l'écran]
- Style sous-titres : [description]
- Durée totale estimée : [Xs]
"""

async def generate(report_markdown: str, audience: str) -> str:
    client = AsyncAnthropic()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": REPURPOSE_PROMPT.format(
                report_markdown=report_markdown,
                audience=audience or "créateurs de contenu francophones"
            )
        }]
    )
    return response.content[0].text
```

---

## 7. Frontend React

### Stack

```
React 18 + TypeScript
Vite (bundler)
Tailwind CSS + shadcn/ui
React Query (TanStack) — data fetching + cache
Zustand — state global (user, jobs)
React Router v6
WebSocket natif — progression temps réel
```

### Pages & composants

```
src/
├── pages/
│   ├── Dashboard.tsx            # Liste des rapports + stats
│   ├── Analyze.tsx              # Input URL + options + lancement
│   ├── JobProgress.tsx          # Progression temps réel (WebSocket)
│   ├── ReportViewer.tsx         # Rapport complet interactif
│   ├── ScriptEditor.tsx         # Éditeur script repurpose
│   ├── Settings.tsx             # API keys + profil + plan
│   └── Auth/
│       ├── Login.tsx
│       └── Register.tsx
├── components/
│   ├── AnalyzeForm.tsx          # Formulaire URL + options
│   ├── ProgressStepper.tsx      # Steps animés (scraping → done)
│   ├── ReportCard.tsx           # Card rapport dans dashboard
│   ├── FramesTimeline.tsx       # Timeline visuelle des frames
│   ├── TranscriptBlock.tsx      # Transcript mis en forme
│   ├── EnrichmentPanel.tsx      # Outils/sources identifiés
│   └── RepurposePanel.tsx       # Script + bouton copier/exporter
├── hooks/
│   ├── useJobProgress.ts        # WebSocket hook
│   ├── useAnalysis.ts           # React Query mutations
│   └── useReport.ts             # React Query queries
└── lib/
    ├── api.ts                   # Axios instance + interceptors
    └── utils.ts
```

### Hook WebSocket progression

```typescript
// src/hooks/useJobProgress.ts
export function useJobProgress(jobId: string | null) {
  const [status, setStatus] = useState<JobStatus | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const token = localStorage.getItem("access_token");
    const ws = new WebSocket(
      `${import.meta.env.VITE_WS_URL}/ws/jobs/${jobId}?token=${token}`
    );

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data);
    };

    ws.onerror = () => ws.close();

    return () => ws.close();
  }, [jobId]);

  return status;
}
```

### UX — Progression

```
[Step 1] 🔍 Scraping Instagram...       ████░░░░░░ 15%
[Step 2] ⬇️  Téléchargement vidéo...    ████████░░ 30%
[Step 3] 🎙️  Transcription Whisper...   ████████░░ 50%
[Step 4] 🎬 Analyse des frames...       ████████░░ 65%
[Step 5] 🌐 Recherche web...            ████████░░ 80%
[Step 6] 📝 Génération du rapport...    ████████░░ 92%
[Step 7] ✅ Terminé !                   ██████████ 100%
```

---

## 8. Infrastructure Docker

### docker-compose.yml

```yaml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/content_intel
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - S3_BUCKET=${S3_BUCKET}
      - SECRET_KEY=${SECRET_KEY}
      - AES_KEY=${AES_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - /tmp/jobs:/tmp/jobs

  worker:
    build: .
    command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/content_intel
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - /tmp/jobs:/tmp/jobs

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: content_intel
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
      - VITE_WS_URL=ws://localhost:8000

  flower:
    image: mher/flower
    command: celery flower --broker=redis://redis:6379/0
    ports:
      - "5555:5555"

volumes:
  postgres_data:
  redis_data:
```

### Dockerfile (API + Worker)

```dockerfile
FROM python:3.12-slim

# Installer ffmpeg + yt-dlp
RUN apt-get update && apt-get install -y ffmpeg curl && \
    curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp \
    -o /usr/local/bin/yt-dlp && chmod +x /usr/local/bin/yt-dlp && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 9. Sécurité & Multi-tenant

### Auth JWT

```python
# Tokens : access (30min) + refresh (7j)
# Rotation automatique du refresh token
# Stockage côté client : httpOnly cookie (refresh) + memory (access)
```

### Chiffrement des API keys utilisateurs

```python
# app/core/crypto.py
# Les clés Apify/OpenAI des users sont chiffrées AES-256 en base
# La clé AES est dans les env vars — jamais en DB

from cryptography.fernet import Fernet

def encrypt_api_key(raw_key: str) -> str:
    f = Fernet(settings.AES_KEY.encode())
    return f.encrypt(raw_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    f = Fernet(settings.AES_KEY.encode())
    return f.decrypt(encrypted_key.encode()).decode()
```

### Rate limiting

```python
# Middleware FastAPI — Redis sliding window
# Par user : max 10 analyses/heure (plan free), 100/heure (pro)
# Par IP : max 50 req/min (anti-scraping)
```

### Isolation des données

- Chaque requête DB filtre systématiquement par `user_id`
- Les fichiers S3 sont stockés sous `/{user_id}/{job_id}/`
- Les URLs présignées S3 ont une TTL de 15 minutes

---

## 10. Observabilité

### Métriques Prometheus

```python
# Métriques business clés à exposer
analyses_total = Counter("analyses_total", "Analyses lancées", ["platform", "status"])
pipeline_duration = Histogram("pipeline_duration_seconds", "Durée pipeline", ["step"])
llm_tokens_used = Counter("llm_tokens_total", "Tokens LLM consommés", ["model", "service"])
api_cost_cents = Counter("api_cost_cents_total", "Coût API en centimes", ["provider"])
active_jobs = Gauge("active_jobs", "Jobs en cours")
```

### Alertes clés

| Alerte | Condition | Action |
|--------|-----------|--------|
| Pipeline timeout | Job > 5 min | Kill + status failed |
| Apify error rate | > 10% sur 5min | Alert Slack + fallback |
| Whisper failure | > 20% | Désactiver transcription auto |
| LLM cost spike | > 50€/jour | Alert + rate limit serré |
| DB connections | > 80% pool | Scale workers |

---

## 11. Modèle économique

### Coût par analyse

| Service | Coût estimé |
|---------|-------------|
| Apify scrape | ~$0.010 |
| yt-dlp download | $0.000 |
| Whisper (45s) | ~$0.005 |
| Claude Vision (13 frames) | ~$0.080 |
| Claude Rapport | ~$0.030 |
| Claude Repurpose | ~$0.020 |
| Tavily (5 searches) | ~$0.010 |
| **Total** | **~$0.155** |

### Plans tarifaires

| Plan | Prix | Analyses/mois | Coût brut max |
|------|------|---------------|---------------|
| Free | $0 | 5 | $0.78 |
| Starter | $19/mois | 50 | $7.75 |
| Pro | $49/mois | 200 | $31.00 |
| Agency | $129/mois | 1000 | $155.00 |

**Marges estimées :**
- Starter : ~$11 marge (~60%)
- Pro : ~$18 marge (~37%)
- Agency : ~$-26 (loss leader) → inclure support/onboarding premium

---

## 12. Plan de build

### Semaine 1 — Foundation

- Setup Docker + PostgreSQL + Redis + Celery
- Auth JWT (register, login, refresh)
- Scraper Apify (Instagram uniquement)
- Download + extraction audio (ffmpeg)
- `POST /analyze` → job créé + Celery task lancée
- `GET /analyze/{job_id}` → status polling

### Semaine 2 — Pipeline core

- Transcription Whisper API
- Visual analysis Claude Vision
- Web enrichment Tavily
- Génération rapport Claude Sonnet
- Stockage S3 (frames + audio + rapport)

### Semaine 3 — Frontend MVP

- Auth pages (login/register)
- Dashboard + liste rapports
- Analyze form + WebSocket progression
- Report viewer (markdown rendu)

### Semaine 4 — Repurpose + exports

- Repurpose engine (Claude Sonnet)
- Script editor React (éditable)
- Export rapport Markdown + PDF
- Settings API keys (chiffrement AES)

### Semaine 5 — Multi-platform + billing

- TikTok + YouTube support (Apify)
- Stripe integration (plans + usage billing)
- Rate limiting par plan
- Quota enforcement (analyses_limit)

### Semaine 6 — Production readiness

- Prometheus + Grafana dashboards
- Alertes (Slack webhooks)
- Tests E2E Playwright
- Review sécurité (OWASP top 10)
- CI/CD GitHub Actions → Railway / Render / VPS

---

## 13. Checklist de validation finale

### Backend

- [ ] `POST /analyze` retourne 202 + job_id en < 200ms
- [ ] WebSocket pousse les updates toutes les 1.5s
- [ ] Pipeline complet termine en < 90s pour un Reel 60s
- [ ] Scraping Instagram fonctionne sur posts publics
- [ ] Scraping TikTok fonctionne sur posts publics
- [ ] Scraping YouTube fonctionne sur vidéos publiques
- [ ] Transcription Whisper retourne du texte cohérent
- [ ] Vision Claude analyse correctement les frames
- [ ] Enrichissement Tavily retourne des sources valides
- [ ] Rapport structuré généré sans hallucinations majeures
- [ ] Script repurpose cohérent avec l'audience cible
- [ ] Fichiers uploadés sur S3 avec URLs présignées valides
- [ ] Rapport sauvegardé en DB et récupérable
- [ ] API keys users chiffrées en AES en base
- [ ] Rate limiting actif par user_id
- [ ] Isolation données inter-users vérifiée
- [ ] Timeout Celery actif (5 min max)
- [ ] Gestion erreur : Apify fail → job failed proprement
- [ ] Gestion erreur : Whisper fail → rapport sans transcript
- [ ] Gestion erreur : Vision fail → rapport sans frames

### Frontend

- [ ] Login / Register fonctionnels
- [ ] Analyze form accepte toutes les plateformes
- [ ] Progression WebSocket s'affiche en temps réel
- [ ] Rapport s'affiche correctement (markdown rendu)
- [ ] Timeline frames navigable
- [ ] Script repurpose éditable et copiable
- [ ] Export PDF fonctionnel
- [ ] Settings API keys save/update
- [ ] Dashboard liste les rapports avec filtres
- [ ] Mobile responsive (iOS + Android)

### Infrastructure

- [ ] Docker Compose démarre sans erreur
- [ ] Migrations DB appliquées automatiquement
- [ ] Celery Flower accessible (monitoring jobs)
- [ ] Prometheus scrape les métriques
- [ ] Grafana dashboard opérationnel
- [ ] Alertes Slack configurées
- [ ] Backup PostgreSQL automatique (daily)
- [ ] `.env` jamais committé (`.gitignore`)
- [ ] HTTPS forcé en prod
- [ ] CORS configuré (whitelist frontend domain)

### Business

- [ ] Stripe webhooks fonctionnels (checkout, cancel, renewal)
- [ ] Quota enforcement actif (analyses_limit respectée)
- [ ] Plan upgrade/downgrade fonctionnel
- [ ] Email de bienvenue envoyé à l'inscription
- [ ] Coût par analyse réel mesuré et conforme aux estimations

---

*Document généré pour le projet Content Intelligence SaaS — Ibz, Avril 2026*
