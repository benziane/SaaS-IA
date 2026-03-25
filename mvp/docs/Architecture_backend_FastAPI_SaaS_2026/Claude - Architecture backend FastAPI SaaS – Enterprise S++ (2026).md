# Enterprise S+++ FastAPI Architecture Guide

> **Stack** : FastAPI 0.135 · Python 3.13 · PostgreSQL 16 · Redis 7 · Celery · Docker Compose / Kubernetes  
> **Objectif** : Passer une plateforme SaaS IA (25 modules, ~160 endpoints) au niveau enterprise-grade.  
> **Principe** : Chaque amélioration = 1 fichier indépendant, zéro breaking change, zéro dépendance payante.

---

## Table des matières

1. [Security Headers Middleware](#1-security-headers-middleware)
2. [Request ID / Correlation ID Middleware](#2-request-id--correlation-id-middleware)
3. [Gzip/Brotli Compression Middleware](#3-gzipbrotli-compression-middleware)
4. [Graceful Shutdown](#4-graceful-shutdown)
5. [Health Checks avancés (K8s-ready)](#5-health-checks-avancés-kubernetes-ready)
6. [Database Connection Pooling](#6-database-connection-pooling)
7. [Structured Logging Enterprise](#7-structured-logging-enterprise)
8. [Circuit Breaker pour AI Providers](#8-circuit-breaker-pour-ai-providers)
9. [API Rate Limiting avancé](#9-api-rate-limiting-avancé)
10. [Dockerfile Multi-Stage Optimisé](#10-dockerfile-multi-stage-optimisé)
11. [OpenTelemetry Integration](#11-opentelemetry-integration)
12. [Error Tracking (Sentry-like)](#12-error-tracking-sentry-like)

---

## 1. Security Headers Middleware

**Fichier** : `app/middleware/security_headers.py`

```python
"""
Enterprise security headers middleware.
Ajoute OWASP-recommended headers sur chaque réponse HTTP.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injecte les headers de sécurité recommandés par OWASP sur toutes les réponses.
    Compatible avec les réponses streaming (SSE).
    """

    def __init__(self, app, csp_policy: str | None = None):
        super().__init__(app)
        # CSP par défaut strict — personnalisable à l'instanciation
        self.csp = csp_policy or (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        # Headers statiques — calculés une seule fois
        self._static_headers: dict[str, str] = {
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
            "Content-Security-Policy": self.csp,
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), magnetometer=()"
            ),
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # Injecter tous les headers statiques
        for header, value in self._static_headers.items():
            response.headers[header] = value

        # Cache-Control spécifique aux endpoints API (pas les assets statiques)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Supprimer le header Server (information disclosure)
        response.headers.pop("Server", None)

        return response
```

**Registration dans `main.py`** :

```python
from app.middleware.security_headers import SecurityHeadersMiddleware

# Ajouter APRÈS CORSMiddleware (ordre inverse d'exécution dans Starlette)
app.add_middleware(SecurityHeadersMiddleware)
```

**Repo GitHub de référence** : [secure-headers (Helmet.js concept, OWASP)](https://github.com/helmetjs/helmet) — 10k+ stars. L'équivalent Python le plus direct est d'implémenter les mêmes headers manuellement comme ci-dessus.

**Erreurs courantes à éviter** :
- **CSP trop lax** (`unsafe-eval`, `*`) annule toute la protection. Commencer strict, ouvrir au cas par cas.
- **HSTS sans `includeSubDomains`** : les sous-domaines restent vulnérables au MITM.
- **Oublier de supprimer le header `Server`** : révèle la stack technique (Uvicorn/version).
- **Appliquer `no-store` sur les assets statiques** : casse le cache navigateur et dégrade les performances.

**Astuce non-évidente** : L'ordre des middleware Starlette est **inverse** — le dernier `add_middleware()` est le premier exécuté. Mettre `SecurityHeadersMiddleware` après `CORSMiddleware` pour que les headers CORS ne soient pas écrasés.

---

## 2. Request ID / Correlation ID Middleware

**Fichier** : `app/middleware/request_id.py`

```python
"""
Request ID middleware avec propagation contextvars + structlog + Celery.
"""
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ContextVar accessible partout dans le lifecycle de la requête
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
current_user_id_ctx: ContextVar[str] = ContextVar("current_user_id", default="anonymous")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    - Lit X-Request-ID entrant ou génère un UUID4.
    - Stocke dans contextvars pour usage par structlog, Celery, etc.
    - Renvoie X-Request-ID dans la réponse.
    """

    HEADER_NAME = "X-Request-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        # Réutiliser l'ID entrant (propagation inter-services) ou en générer un
        rid = request.headers.get(self.HEADER_NAME) or uuid.uuid4().hex
        request_id_ctx.set(rid)

        # Stocker dans request.state pour accès synchrone dans les dépendances
        request.state.request_id = rid

        response: Response = await call_next(request)
        response.headers[self.HEADER_NAME] = rid
        return response


def get_request_id() -> str:
    """Helper pour accéder au request_id depuis n'importe où."""
    return request_id_ctx.get()
```

**Fichier** : `app/middleware/request_id_structlog.py` — Processeur structlog

```python
"""
Processeur structlog qui injecte automatiquement request_id et user_id.
"""
from app.middleware.request_id import request_id_ctx, current_user_id_ctx


def inject_context_vars(logger, method, event_dict):
    """Processeur structlog : ajoute request_id et user_id à chaque log."""
    rid = request_id_ctx.get()
    if rid:
        event_dict["request_id"] = rid
    uid = current_user_id_ctx.get()
    if uid and uid != "anonymous":
        event_dict["user_id"] = uid
    return event_dict
```

**Fichier** : `app/middleware/request_id_celery.py` — Propagation Celery

```python
"""
Signaux Celery pour propager le request_id via les headers de task.
"""
from celery import signals
from app.middleware.request_id import request_id_ctx


@signals.before_task_publish.connect
def propagate_request_id_to_task(headers: dict, **kwargs):
    """Injecte le request_id dans les headers Celery avant publication."""
    rid = request_id_ctx.get()
    if rid:
        headers["x_request_id"] = rid


@signals.task_prerun.connect
def restore_request_id_in_worker(task, **kwargs):
    """Restaure le request_id depuis les headers Celery dans le worker."""
    rid = getattr(task.request, "x_request_id", None)
    if rid:
        request_id_ctx.set(rid)


@signals.task_postrun.connect
def clear_request_id_after_task(**kwargs):
    """Nettoie le contexte après exécution de la task."""
    request_id_ctx.set("")
```

**Utilisation dans un endpoint ou service** :

```python
import structlog
from app.middleware.request_id import get_request_id

logger = structlog.get_logger()

async def some_service():
    # Le request_id est automatiquement dans chaque log
    logger.info("processing_payment", amount=42.0)
    # Output: {"event": "processing_payment", "amount": 42.0, "request_id": "a1b2c3..."}

    # Accès direct si nécessaire
    rid = get_request_id()
```

**Registration dans `main.py`** :

```python
from app.middleware.request_id import RequestIDMiddleware

app.add_middleware(RequestIDMiddleware)

# Dans la config Celery (celery_app.py), importer les signaux :
import app.middleware.request_id_celery  # noqa: F401 — les signaux s'auto-enregistrent
```

**Repo GitHub de référence** : [asgi-correlation-id](https://github.com/snok/asgi-correlation-id) — ~500 stars mais pattern de référence. Pour un projet plus large : [starlette-context](https://github.com/tomwojcik/starlette-context).

**Erreurs courantes à éviter** :
- **Ne pas valider le X-Request-ID entrant** : un attaquant peut injecter du contenu dans vos logs (log injection). En production, valider le format UUID ou tronquer à 64 caractères.
- **Oublier la propagation Celery** : les tasks perdent la traçabilité et deviennent impossibles à corréler avec la requête HTTP d'origine.
- **Utiliser `threading.local()` au lieu de `contextvars`** : ne fonctionne pas avec asyncio.

**Astuce non-évidente** : En production avec plusieurs workers Uvicorn, le `contextvars.ContextVar` est thread-safe ET coroutine-safe (chaque task asyncio a son propre contexte). C'est le seul mécanisme fiable pour FastAPI async.

---

## 3. Gzip/Brotli Compression Middleware

**Fichier** : `app/middleware/compression.py`

```python
"""
Compression middleware avec Gzip + Brotli, exclusion SSE et /metrics.
"""
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False


class SelectiveCompressionMiddleware(BaseHTTPMiddleware):
    """
    Applique Gzip (ou Brotli si disponible) sauf sur :
    - Endpoints SSE (text/event-stream)
    - /metrics (Prometheus gère sa propre compression)
    - Réponses < 500 bytes
    """

    EXCLUDED_PATHS: set[str] = {"/metrics", "/health/live", "/health/ready"}
    MIN_SIZE: int = 500

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Wrapping interne avec GZipMiddleware de Starlette
        self._gzip = GZipMiddleware(app, minimum_size=self.MIN_SIZE)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip compression pour les chemins exclus
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Skip si le client demande text/event-stream (SSE)
        accept = request.headers.get("accept", "")
        if "text/event-stream" in accept:
            return await call_next(request)

        response: Response = await call_next(request)

        # Skip si la réponse est déjà un stream SSE
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            return response

        # Skip si trop petit
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) < self.MIN_SIZE:
            return response

        # Brotli si disponible ET demandé par le client
        accept_encoding = request.headers.get("accept-encoding", "")
        if BROTLI_AVAILABLE and "br" in accept_encoding and hasattr(response, "body"):
            compressed = brotli.compress(response.body, quality=4)
            if len(compressed) < len(response.body):
                return Response(
                    content=compressed,
                    status_code=response.status_code,
                    headers={
                        **dict(response.headers),
                        "Content-Encoding": "br",
                        "Content-Length": str(len(compressed)),
                        "Vary": "Accept-Encoding",
                    },
                    media_type=response.media_type,
                )

        return response
```

**Approche alternative simplifiée (recommandée)** — utiliser directement `GZipMiddleware` de Starlette avec un wrapper de routing :

```python
# main.py — approche pragmatique
from starlette.middleware.gzip import GZipMiddleware

# GZipMiddleware natif avec seuil 500 bytes
app.add_middleware(GZipMiddleware, minimum_size=500)
```

**Registration dans `main.py`** :

```python
from app.middleware.compression import SelectiveCompressionMiddleware

# Ajouter EN PREMIER (exécuté en dernier, après que la réponse est prête)
app.add_middleware(SelectiveCompressionMiddleware)
```

**Repo GitHub de référence** : [starlette (GZipMiddleware intégré)](https://github.com/encode/starlette) — 10k+ stars

**Erreurs courantes à éviter** :
- **Compresser les endpoints SSE** : casse le streaming temps réel car le client attend des chunks non-compressés.
- **Brotli quality > 6 en temps réel** : quality 11 est optimal pour les assets statiques mais bloque le thread pendant ~500ms pour une réponse API. Utiliser quality 4 max pour les réponses dynamiques.
- **Double compression** : si un reverse proxy (nginx) compresse déjà, la compression côté app est inutile. Vérifier la chaîne complète.

**Astuce non-évidente** : `GZipMiddleware` de Starlette est un middleware ASGI pur (pas `BaseHTTPMiddleware`), donc plus performant et compatible streaming natif. Pour la plupart des cas, c'est suffisant sans le wrapper custom.

---

## 4. Graceful Shutdown

**Fichier** : `app/core/lifecycle.py`

```python
"""
Lifespan manager avec graceful shutdown pour FastAPI + asyncpg + Redis.
"""
import asyncio
import signal
import structlog
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import engine, async_session_factory
from app.core.redis import redis_pool

logger = structlog.get_logger()

# Flag global pour signaler l'arrêt en cours
_shutting_down = asyncio.Event()

# Compteur de requêtes en cours
_active_requests: int = 0
_active_lock = asyncio.Lock()


async def _increment_active():
    global _active_requests
    async with _active_lock:
        _active_requests += 1


async def _decrement_active():
    global _active_requests
    async with _active_lock:
        _active_requests -= 1


def is_shutting_down() -> bool:
    return _shutting_down.is_set()


async def _wait_for_drain(timeout: float = 30.0):
    """Attend que toutes les requêtes en cours finissent (max timeout secondes)."""
    logger.info("graceful_shutdown_draining", active_requests=_active_requests, timeout=timeout)
    start = asyncio.get_event_loop().time()
    while _active_requests > 0:
        elapsed = asyncio.get_event_loop().time() - start
        if elapsed >= timeout:
            logger.warning(
                "graceful_shutdown_timeout",
                remaining_requests=_active_requests,
                elapsed=elapsed,
            )
            break
        await asyncio.sleep(0.5)
    logger.info("graceful_shutdown_drained", remaining_requests=_active_requests)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan manager FastAPI :
    - Startup : initialise les pools de connexion
    - Shutdown : drain + fermeture propre de tout
    """
    # ── STARTUP ──
    logger.info("app_startup", environment=settings.ENVIRONMENT)

    # Vérifier la connectivité DB
    async with engine.begin() as conn:
        await conn.execute("SELECT 1")
    logger.info("database_connected")

    # Vérifier Redis
    await redis_pool.ping()
    logger.info("redis_connected")

    yield  # ← L'application tourne ici

    # ── SHUTDOWN ──
    logger.info("app_shutdown_initiated")
    _shutting_down.set()

    # 1. Drainer les requêtes HTTP en cours (max 30s)
    await _wait_for_drain(timeout=30.0)

    # 2. Fermer le pool asyncpg/SQLAlchemy
    await engine.dispose()
    logger.info("database_pool_closed")

    # 3. Fermer Redis
    await redis_pool.aclose()
    logger.info("redis_pool_closed")

    logger.info("app_shutdown_complete")
```

**Fichier** : `app/middleware/shutdown_guard.py`

```python
"""
Middleware qui refuse les nouvelles requêtes pendant le shutdown
et track les requêtes actives.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.lifecycle import (
    is_shutting_down,
    _increment_active,
    _decrement_active,
)


class ShutdownGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if is_shutting_down():
            return JSONResponse(
                status_code=503,
                content={"detail": "Server is shutting down"},
                headers={"Connection": "close", "Retry-After": "30"},
            )

        await _increment_active()
        try:
            return await call_next(request)
        finally:
            await _decrement_active()
```

**Fichier** : `celery_config.py` — Celery warm shutdown

```python
"""
Configuration Celery pour warm shutdown.
"""
from celery import Celery
from celery.signals import worker_shutting_down

app = Celery("telecomlabsaas")

# Warm shutdown : finir la task en cours, ne pas en prendre de nouvelles
app.conf.update(
    worker_prefetch_multiplier=1,       # 1 seule task à la fois dans le buffer
    worker_max_tasks_per_child=1000,    # Recycle le worker après 1000 tasks (fuite mémoire)
    worker_cancel_long_running_tasks_on_connection_loss=True,
    task_acks_late=True,                # ACK après exécution (pas avant)
    task_reject_on_worker_lost=True,    # Re-queue si le worker crash
)


@worker_shutting_down.connect
def on_worker_shutting_down(sig, how, exitcode, **kwargs):
    """Log le début du warm shutdown."""
    import structlog
    logger = structlog.get_logger()
    logger.info("celery_worker_shutting_down", signal=sig, how=how)
```

**Docker Compose** :

```yaml
# docker-compose.yml
services:
  api:
    build: .
    stop_signal: SIGTERM
    stop_grace_period: 45s   # 30s drain + 15s marge
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  celery_worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    stop_signal: SIGTERM
    stop_grace_period: 120s  # Laisser le temps aux tasks longues (AI inference)
```

**Registration dans `main.py`** :

```python
from app.core.lifecycle import lifespan
from app.middleware.shutdown_guard import ShutdownGuardMiddleware

app = FastAPI(lifespan=lifespan)
app.add_middleware(ShutdownGuardMiddleware)
```

**Repo GitHub de référence** : [granian (ASGI server avec graceful shutdown natif)](https://github.com/emmett-framework/granian) — 3k+ stars. Aussi : [uvicorn](https://github.com/encode/uvicorn) — 8k+ stars (gère SIGTERM nativement).

**Erreurs courantes à éviter** :
- **`stop_grace_period` trop court** : Docker envoie SIGKILL après le timeout → perte de données, tasks Celery orphelines.
- **`task_acks_late=False` (défaut Celery)** : si le worker crash, la task est perdue. Avec `True`, elle est re-queued.
- **Oublier `worker_prefetch_multiplier=1`** : avec la valeur par défaut (4), Celery pré-fetche 4 tasks → 3 sont perdues au shutdown.

**Astuce non-évidente** : Uvicorn gère déjà SIGTERM en interne (arrête d'accepter de nouvelles connexions). Le `lifespan` shutdown handler est exécuté **après** que Uvicorn a fini de drainer. Le `ShutdownGuardMiddleware` est une couche supplémentaire pour les requêtes qui arrivent pendant la fenêtre entre SIGTERM et le drain complet.

---

## 5. Health Checks avancés (Kubernetes-ready)

**Fichier** : `app/api/health.py`

```python
"""
Health check endpoints Kubernetes-ready :
- /health/live   → liveness  (app alive ?)
- /health/ready  → readiness (dépendances OK ?)
- /health/startup → startup  (initialisation terminée ?)
"""
import time
import asyncio
import structlog
from fastapi import APIRouter, Response
from pydantic import BaseModel

from app.core.database import engine
from app.core.redis import redis_pool

logger = structlog.get_logger()
router = APIRouter(prefix="/health", tags=["health"])

# Flag set par le lifespan startup
_startup_complete = False
_startup_time: float = 0.0
_modules_loaded: list[str] = []


def mark_startup_complete(modules: list[str]):
    global _startup_complete, _startup_time, _modules_loaded
    _startup_complete = True
    _startup_time = time.time()
    _modules_loaded = modules


class HealthStatus(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    checks: dict[str, dict]
    timestamp: float


async def _check_postgres() -> dict:
    """Vérifie la connectivité PostgreSQL avec un timeout."""
    try:
        async with engine.connect() as conn:
            result = await asyncio.wait_for(
                conn.execute("SELECT 1"), timeout=5.0
            )
            return {"status": "ok", "latency_ms": 0}  # Enrichi ci-dessous
    except asyncio.TimeoutError:
        return {"status": "timeout", "error": "PostgreSQL query timeout (5s)"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:200]}


async def _check_redis() -> dict:
    """Vérifie la connectivité Redis avec un timeout."""
    try:
        start = time.monotonic()
        pong = await asyncio.wait_for(redis_pool.ping(), timeout=3.0)
        latency = (time.monotonic() - start) * 1000
        return {"status": "ok" if pong else "error", "latency_ms": round(latency, 2)}
    except asyncio.TimeoutError:
        return {"status": "timeout", "error": "Redis ping timeout (3s)"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:200]}


@router.get("/live", status_code=200)
async def liveness():
    """
    Liveness probe : l'application est-elle vivante ?
    Retourne 200 tant que le process Python tourne.
    Kubernetes redémarre le pod si cette probe échoue.
    """
    return {"status": "alive", "timestamp": time.time()}


@router.get("/ready")
async def readiness(response: Response):
    """
    Readiness probe : l'application peut-elle servir du trafic ?
    Vérifie PostgreSQL + Redis.
    Kubernetes retire le pod du load balancer si cette probe échoue.
    """
    pg_check, redis_check = await asyncio.gather(
        _check_postgres(),
        _check_redis(),
    )

    all_ok = pg_check["status"] == "ok" and redis_check["status"] == "ok"
    status = "healthy" if all_ok else "unhealthy"

    if not all_ok:
        response.status_code = 503
        logger.warning("readiness_check_failed", postgres=pg_check, redis=redis_check)

    return HealthStatus(
        status=status,
        checks={"postgres": pg_check, "redis": redis_check},
        timestamp=time.time(),
    )


@router.get("/startup")
async def startup_probe(response: Response):
    """
    Startup probe : l'initialisation est-elle terminée ?
    Vérifie que le lifespan a fini, que les modules sont chargés.
    Kubernetes attend avant d'envoyer les probes liveness/readiness.
    """
    if not _startup_complete:
        response.status_code = 503
        return {
            "status": "starting",
            "modules_loaded": _modules_loaded,
            "timestamp": time.time(),
        }

    return {
        "status": "started",
        "uptime_seconds": round(time.time() - _startup_time, 1),
        "modules_loaded": len(_modules_loaded),
        "modules": _modules_loaded,
        "timestamp": time.time(),
    }
```

**Config Kubernetes** :

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: api
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          startupProbe:
            httpGet:
              path: /health/startup
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 5
            failureThreshold: 30  # 30 * 5s = 150s max pour démarrer
```

**Registration dans `main.py`** :

```python
from app.api.health import router as health_router, mark_startup_complete

app.include_router(health_router)

# Dans le lifespan, après le chargement des modules :
# mark_startup_complete(list_of_loaded_modules)
```

**Repo GitHub de référence** : [py-healthcheck](https://github.com/Runscope/pyhealth) et [fastapi-health](https://github.com/Kludex/fastapi-health) — pattern de base. Pour le pattern K8s complet : [kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/).

**Erreurs courantes à éviter** :
- **Liveness probe qui check la DB** : si la DB est down, Kubernetes redémarre le pod au lieu de le retirer du LB (readiness). La DB ne revient pas plus vite parce qu'on redémarre les pods.
- **`initialDelaySeconds` trop court** : le pod est killé avant de finir son startup (migrations, imports).
- **Timeout > period** : les probes s'empilent et le pod est considéré mort.

**Astuce non-évidente** : Utiliser `startupProbe` avec un `failureThreshold` élevé (30) et un `periodSeconds` court (5s) pour les cold starts lents (chargement de modèles ML, migrations). Pendant le startup, les liveness/readiness probes sont suspendues.

---

## 6. Database Connection Pooling

**Fichier** : `app/core/database.py`

```python
"""
Configuration optimale du pool asyncpg pour PostgreSQL 16.
SQLAlchemy 2.x async avec health checks, retry, et metrics.
"""
import time
import asyncio
import structlog
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy import event, text
from sqlmodel import SQLModel

from app.core.config import settings

logger = structlog.get_logger()

# ── Engine avec pool optimisé ──
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,  # postgresql+asyncpg://user:pass@host/db
    # Pool sizing
    pool_size=20,                # Connexions permanentes (= nb workers * 2 typiquement)
    max_overflow=10,             # Connexions supplémentaires en pic (temporaires)
    pool_timeout=30,             # Timeout d'attente pour obtenir une connexion (secondes)
    pool_recycle=3600,           # Recycler les connexions après 1h (évite les stale connections)
    pool_pre_ping=True,          # Vérifie la connexion avant chaque utilisation (SELECT 1)
    # Performance
    echo=settings.SQL_ECHO,      # True en dev pour voir les queries
    echo_pool=False,             # Pas de log du pool en prod
    # Paramètres asyncpg
    connect_args={
        "server_settings": {
            "application_name": "telecomlabsaas",
            "jit": "off",                    # Désactiver JIT pour les requêtes courtes
            "statement_timeout": "30000",     # 30s max par query
        },
        "command_timeout": 30,
    },
    pool_class=AsyncAdaptedQueuePool,
)

# ── Session factory ──
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Évite les lazy loads accidentels après commit
)


# ── Pool metrics ──
class PoolMetrics:
    """Expose les métriques du pool pour Prometheus."""

    @staticmethod
    def get_stats() -> dict:
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalidated(),
        }


# ── Event listeners pour le monitoring ──
@event.listens_for(engine.sync_engine, "checkout")
def _on_checkout(dbapi_conn, connection_record, connection_proxy):
    """Track le temps d'attente pour obtenir une connexion."""
    connection_record.info["checkout_time"] = time.monotonic()


@event.listens_for(engine.sync_engine, "checkin")
def _on_checkin(dbapi_conn, connection_record):
    """Log les connexions utilisées trop longtemps."""
    checkout_time = connection_record.info.get("checkout_time")
    if checkout_time:
        duration = time.monotonic() - checkout_time
        if duration > 5.0:
            logger.warning(
                "slow_db_connection_usage",
                duration_seconds=round(duration, 2),
            )


# ── Dependency FastAPI ──
async def get_db() -> AsyncSession:
    """Dependency FastAPI pour injecter une session DB."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Retry connect avec backoff ──
async def wait_for_db(max_retries: int = 5, base_delay: float = 1.0):
    """
    Attend que PostgreSQL soit disponible avec exponential backoff.
    À appeler dans le lifespan startup.
    """
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("database_connected", attempt=attempt)
            return
        except Exception as e:
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "database_connection_retry",
                attempt=attempt,
                max_retries=max_retries,
                delay=delay,
                error=str(e)[:100],
            )
            if attempt == max_retries:
                raise
            await asyncio.sleep(delay)
```

**Registration dans `main.py`** :

```python
from app.core.database import engine, wait_for_db, PoolMetrics

# Dans le lifespan startup :
await wait_for_db(max_retries=5)

# Endpoint métriques optionnel :
@app.get("/debug/db-pool")
async def db_pool_stats():
    return PoolMetrics.get_stats()
```

**Repo GitHub de référence** : [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) — 9k+ stars. La doc officielle sur le pool est excellente : `docs.sqlalchemy.org/en/20/core/pooling.html`.

**Erreurs courantes à éviter** :
- **`pool_size` trop grand** : chaque connexion asyncpg consomme ~10MB de RAM côté PostgreSQL. Avec 4 workers × pool_size=20 = 80 connexions permanentes → vérifier `max_connections` PostgreSQL (défaut: 100).
- **Oublier `pool_pre_ping=True`** : les connexions stale après un restart PostgreSQL causent des erreurs "connection reset" en rafale.
- **`expire_on_commit=True` (défaut)** : cause des lazy loads accidentels qui bloquent l'event loop asyncio.

**Astuce non-évidente** : `jit: "off"` dans `server_settings` désactive le JIT PostgreSQL. Le JIT est conçu pour les queries analytiques longues (OLAP). Pour les queries OLTP courtes (<100ms), le coût de compilation JIT est supérieur au gain d'exécution. Gain typique : -20% latence P95 sur les queries simples.

---

## 7. Structured Logging Enterprise

**Fichier** : `app/core/logging_config.py`

```python
"""
Configuration structlog enterprise-grade :
- JSON en production, console colorée en dev
- Request ID + User ID automatiques
- Filtrage des données sensibles
- Timing des requêtes
"""
import logging
import re
import sys
import time
import structlog
from structlog.types import EventDict

from app.core.config import settings


# ── Processeurs custom ──

# Patterns de données sensibles à masquer
_SENSITIVE_PATTERNS = re.compile(
    r"(password|passwd|secret|token|api_key|authorization|cookie|session_id|"
    r"credit_card|ssn|social_security)"
    r"\s*[=:]\s*\S+",
    re.IGNORECASE,
)

_SENSITIVE_KEYS = frozenset({
    "password", "passwd", "secret", "token", "api_key", "authorization",
    "cookie", "session_id", "credit_card", "ssn", "access_token",
    "refresh_token", "private_key",
})


def filter_sensitive_data(logger, method, event_dict: EventDict) -> EventDict:
    """Masque les valeurs sensibles dans les logs."""
    for key in list(event_dict.keys()):
        if key.lower() in _SENSITIVE_KEYS:
            event_dict[key] = "***REDACTED***"
        elif isinstance(event_dict[key], str):
            event_dict[key] = _SENSITIVE_PATTERNS.sub(
                lambda m: m.group().split("=")[0] + "=***REDACTED***"
                if "=" in m.group()
                else m.group().split(":")[0] + ": ***REDACTED***",
                event_dict[key],
            )
    return event_dict


def add_environment(logger, method, event_dict: EventDict) -> EventDict:
    """Ajoute l'environnement et le service name."""
    event_dict["service"] = "telecomlabsaas"
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict


def add_caller_info(logger, method, event_dict: EventDict) -> EventDict:
    """Ajoute le module et la fonction appelante."""
    record = event_dict.get("_record")
    if record:
        event_dict["module"] = record.module
        event_dict["func"] = record.funcName
        event_dict["lineno"] = record.lineno
    return event_dict


# ── Configuration principale ──

def configure_logging():
    """
    Configure structlog + stdlib logging.
    Appeler UNE SEULE FOIS au démarrage de l'application.
    """
    is_production = settings.ENVIRONMENT == "production"

    # Processeurs partagés
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_environment,
        filter_sensitive_data,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if is_production:
        # Production : JSON pour ingestion par ELK/Loki/Datadog
        renderer = structlog.processors.JSONRenderer()
    else:
        # Dev : console colorée lisible
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
        )

    structlog.configure(
        processors=[
            *shared_processors,
            # Injection request_id depuis contextvars (voir middleware/request_id.py)
            # Ce processeur est ajouté dans request_id_structlog.py
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configuration stdlib logging (pour les libs tierces)
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Niveaux par module (certains plus verbeux)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.SQL_ECHO else logging.WARNING
    )
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
```

**Fichier** : `app/middleware/logging_middleware.py`

```python
"""
Middleware de logging qui time chaque requête et injecte le user_id.
"""
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.request_id import current_user_id_ctx

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log chaque requête HTTP avec :
    - Durée (ms)
    - Status code
    - Méthode + path
    - User ID (si authentifié)
    """

    SKIP_PATHS: set[str] = {"/health/live", "/health/ready", "/metrics"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()

        # Extraire user_id du JWT si présent (après auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            current_user_id_ctx.set(str(user_id))

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        log_method = logger.info if response.status_code < 400 else logger.warning
        if response.status_code >= 500:
            log_method = logger.error

        log_method(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=request.client.host if request.client else None,
        )

        # Header custom pour le frontend/debug
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response
```

**Registration dans `main.py`** :

```python
from app.core.logging_config import configure_logging
from app.middleware.logging_middleware import RequestLoggingMiddleware

# AVANT tout autre import qui utilise structlog
configure_logging()

app.add_middleware(RequestLoggingMiddleware)
```

**Repo GitHub de référence** : [structlog](https://github.com/hynek/structlog) — 3.5k+ stars

**Erreurs courantes à éviter** :
- **Configurer structlog APRÈS les imports** : les loggers sont cachés à la première utilisation. Configurer dans le module principal, avant tout.
- **Logger les request bodies** : viole le RGPD et peut logger des mots de passe en clair.
- **`time.time()` au lieu de `time.perf_counter()`** : `time.time()` a une résolution de ~15ms sur Windows et est sensible aux ajustements NTP.

**Astuce non-évidente** : `structlog.contextvars.merge_contextvars` combiné avec `structlog.contextvars.bind_contextvars()` permet d'ajouter du contexte à **tous** les logs d'une requête sans les passer explicitement. Ex: `structlog.contextvars.bind_contextvars(tenant_id="acme")` au début d'une requête multi-tenant.

---

## 8. Circuit Breaker pour AI Providers

**Fichier** : `app/core/circuit_breaker.py`

```python
"""
Circuit breaker zéro-dépendance pour les appels aux providers IA.
3 états : CLOSED → OPEN → HALF_OPEN → CLOSED
"""
import time
import asyncio
import enum
import structlog
from collections import deque
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

logger = structlog.get_logger()


class CircuitState(enum.Enum):
    CLOSED = "closed"        # Normal : tout passe
    OPEN = "open"            # Failing : tout est bloqué, fallback
    HALF_OPEN = "half_open"  # Test : 1 requête passe pour vérifier la recovery


@dataclass
class CircuitStats:
    """Statistiques du circuit pour les métriques Prometheus."""
    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: float | None
    last_state_change: float
    consecutive_successes_in_half_open: int


@dataclass
class CircuitBreaker:
    """
    Circuit breaker configurable.

    Exemple :
        cb = CircuitBreaker(name="claude_api", failure_threshold=5, recovery_timeout=60)
        result = await cb.call(httpx_client.post, url, json=payload)
    """

    name: str
    failure_threshold: int = 5          # Nb failures avant ouverture
    recovery_timeout: float = 60.0      # Secondes avant de tester la recovery
    half_open_max_calls: int = 3        # Succès consécutifs pour refermer
    window_size: float = 60.0           # Fenêtre de comptage des failures

    # État interne
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failures: deque = field(default_factory=deque, init=False)
    _last_failure_time: float | None = field(default=None, init=False)
    _last_state_change: float = field(default_factory=time.monotonic, init=False)
    _half_open_successes: int = field(default=0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _total_successes: int = field(default=0, init=False)
    _total_failures: int = field(default=0, init=False)

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def stats(self) -> CircuitStats:
        return CircuitStats(
            state=self._state,
            failure_count=self._total_failures,
            success_count=self._total_successes,
            last_failure_time=self._last_failure_time,
            last_state_change=self._last_state_change,
            consecutive_successes_in_half_open=self._half_open_successes,
        )

    def _clean_old_failures(self):
        """Retire les failures hors de la fenêtre de temps."""
        now = time.monotonic()
        while self._failures and (now - self._failures[0]) > self.window_size:
            self._failures.popleft()

    def _transition(self, new_state: CircuitState):
        old = self._state
        self._state = new_state
        self._last_state_change = time.monotonic()
        logger.info(
            "circuit_breaker_transition",
            name=self.name,
            from_state=old.value,
            to_state=new_state.value,
        )

    async def _record_success(self):
        async with self._lock:
            self._total_successes += 1
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_successes += 1
                if self._half_open_successes >= self.half_open_max_calls:
                    self._transition(CircuitState.CLOSED)
                    self._failures.clear()
                    self._half_open_successes = 0

    async def _record_failure(self, error: Exception):
        async with self._lock:
            now = time.monotonic()
            self._failures.append(now)
            self._last_failure_time = now
            self._total_failures += 1
            self._clean_old_failures()

            if self._state == CircuitState.HALF_OPEN:
                self._transition(CircuitState.OPEN)
                self._half_open_successes = 0
            elif self._state == CircuitState.CLOSED:
                if len(self._failures) >= self.failure_threshold:
                    self._transition(CircuitState.OPEN)

            logger.warning(
                "circuit_breaker_failure",
                name=self.name,
                error=str(error)[:200],
                failure_count=len(self._failures),
                state=self._state.value,
            )

    def _should_allow_request(self) -> bool:
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._last_state_change
            if elapsed >= self.recovery_timeout:
                self._transition(CircuitState.HALF_OPEN)
                self._half_open_successes = 0
                return True
            return False
        # HALF_OPEN : laisser passer
        return True

    async def call(self, func, *args, **kwargs) -> Any:
        """
        Exécute func à travers le circuit breaker.
        Raise CircuitOpenError si le circuit est ouvert.
        """
        if not self._should_allow_request():
            raise CircuitOpenError(
                f"Circuit '{self.name}' is OPEN. "
                f"Recovery in {self.recovery_timeout - (time.monotonic() - self._last_state_change):.1f}s"
            )
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            await self._record_success()
            return result
        except Exception as e:
            await self._record_failure(e)
            raise


class CircuitOpenError(Exception):
    """Levée quand le circuit est ouvert et la requête est bloquée."""
    pass


# ── Provider Manager avec fallback automatique ──

class AIProviderManager:
    """
    Gère plusieurs providers IA avec circuit breakers et fallback automatique.

    Exemple :
        manager = AIProviderManager()
        manager.add_provider("claude", call_claude, priority=1)
        manager.add_provider("gemini", call_gemini, priority=2)
        manager.add_provider("groq", call_groq, priority=3)

        result = await manager.call(prompt="Hello")
    """

    def __init__(self):
        self._providers: list[tuple[int, str, Any, CircuitBreaker]] = []

    def add_provider(
        self,
        name: str,
        call_func,
        priority: int = 1,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        cb = CircuitBreaker(
            name=f"ai_provider_{name}",
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        self._providers.append((priority, name, call_func, cb))
        self._providers.sort(key=lambda x: x[0])

    async def call(self, **kwargs) -> Any:
        """Essaie chaque provider par priorité avec fallback automatique."""
        last_error = None
        for priority, name, func, cb in self._providers:
            try:
                result = await cb.call(func, **kwargs)
                logger.info("ai_provider_success", provider=name)
                return result
            except CircuitOpenError:
                logger.info("ai_provider_circuit_open", provider=name)
                continue
            except Exception as e:
                last_error = e
                logger.warning(
                    "ai_provider_failed",
                    provider=name,
                    error=str(e)[:200],
                )
                continue

        raise RuntimeError(
            f"All AI providers failed. Last error: {last_error}"
        )

    def get_all_stats(self) -> dict[str, CircuitStats]:
        return {name: cb.stats for _, name, _, cb in self._providers}
```

**Utilisation** :

```python
from app.core.circuit_breaker import AIProviderManager

ai_manager = AIProviderManager()
ai_manager.add_provider("claude", call_claude_api, priority=1)
ai_manager.add_provider("gemini", call_gemini_api, priority=2)

# Dans un endpoint :
result = await ai_manager.call(prompt="Analyze this", model="auto")
```

**Registration dans `main.py`** :

```python
# Pas de middleware — le circuit breaker est un service injecté via dépendance
from app.core.circuit_breaker import AIProviderManager

ai_manager = AIProviderManager()
# Configurer les providers au startup...
```

**Repo GitHub de référence** : [pybreaker](https://github.com/danielfm/pybreaker) — 600+ stars. Pour le pattern complet : [resilience4j (Java, mais architecture de référence)](https://github.com/resilience4j/resilience4j) — 9k+ stars.

**Erreurs courantes à éviter** :
- **Un seul circuit breaker pour tous les providers** : chaque provider doit avoir son propre circuit. Un timeout Gemini ne doit pas bloquer les appels Claude.
- **`recovery_timeout` trop court** : le circuit oscille entre OPEN et HALF_OPEN sans laisser le temps au provider de se rétablir.
- **Ne pas tester le HALF_OPEN** : sans ce test, le circuit reste OPEN indéfiniment après un incident temporaire.

**Astuce non-évidente** : Le `window_size` (fenêtre de temps pour compter les failures) est critique. Sans fenêtre, 5 erreurs sur 24h déclenchent l'ouverture. Avec une fenêtre de 60s, seules 5 erreurs **en 60 secondes** déclenchent — beaucoup plus pertinent pour détecter une panne réelle vs des erreurs sporadiques.

---

## 9. API Rate Limiting avancé

**Fichier** : `app/middleware/rate_limiter.py`

```python
"""
Rate limiter avancé avec sliding window, burst, et headers standards.
Basé sur Redis — compatible cluster.
"""
import time
import hashlib
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from redis.asyncio import Redis

from app.core.config import settings
from app.core.redis import redis_pool

logger = structlog.get_logger()


class SlidingWindowRateLimiter:
    """
    Sliding window counter avec Redis sorted sets.
    Plus équitable que fixed window — pas de pics aux frontières de fenêtre.
    """

    def __init__(
        self,
        redis: Redis,
        requests_per_minute: int = 100,
        burst_size: int = 20,
        burst_window: int = 10,
    ):
        self.redis = redis
        self.rpm = requests_per_minute
        self.burst_size = burst_size
        self.burst_window = burst_window

    def _key(self, identifier: str, window: str) -> str:
        """Clé Redis pour le compteur."""
        h = hashlib.sha256(identifier.encode()).hexdigest()[:16]
        return f"ratelimit:{window}:{h}"

    async def check(self, identifier: str) -> tuple[bool, dict]:
        """
        Vérifie si la requête est autorisée.
        Retourne (allowed, headers_dict).
        """
        now = time.time()
        minute_key = self._key(identifier, "minute")
        burst_key = self._key(identifier, "burst")

        pipe = self.redis.pipeline()

        # ── Sliding window 1 minute ──
        window_start = now - 60
        # Supprimer les entrées hors fenêtre
        pipe.zremrangebyscore(minute_key, 0, window_start)
        # Ajouter la requête actuelle
        pipe.zadd(minute_key, {f"{now}": now})
        # Compter les requêtes dans la fenêtre
        pipe.zcard(minute_key)
        # TTL de sécurité
        pipe.expire(minute_key, 120)

        # ── Burst window (ex: 10 secondes) ──
        burst_start = now - self.burst_window
        pipe.zremrangebyscore(burst_key, 0, burst_start)
        pipe.zadd(burst_key, {f"{now}": now})
        pipe.zcard(burst_key)
        pipe.expire(burst_key, self.burst_window * 2)

        results = await pipe.execute()

        minute_count = results[2]
        burst_count = results[6]

        # Vérifier les deux limites
        minute_allowed = minute_count <= self.rpm
        burst_allowed = burst_count <= self.burst_size

        allowed = minute_allowed and burst_allowed

        # Calculer les headers
        remaining = max(0, self.rpm - minute_count)
        reset_time = int(now) + 60  # Prochaine fenêtre

        headers = {
            "X-RateLimit-Limit": str(self.rpm),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
            "X-RateLimit-Burst-Limit": str(self.burst_size),
            "X-RateLimit-Burst-Remaining": str(max(0, self.burst_size - burst_count)),
        }

        if not allowed:
            # Calculer Retry-After précis
            if not minute_allowed:
                # Trouver le plus ancien dans la fenêtre
                oldest = await self.redis.zrange(minute_key, 0, 0, withscores=True)
                if oldest:
                    retry_after = int(oldest[0][1] + 60 - now) + 1
                else:
                    retry_after = 60
            else:
                retry_after = self.burst_window
            headers["Retry-After"] = str(max(1, retry_after))

        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                identifier=identifier[:16],
                minute_count=minute_count,
                burst_count=burst_count,
            )

        return allowed, headers


# ── IPs whitelistées (monitoring, healthchecks, internes) ──
WHITELISTED_IPS: frozenset[str] = frozenset({
    "127.0.0.1",
    "::1",
    # Ajouter les IPs de monitoring / Kubernetes probes
    *getattr(settings, "RATE_LIMIT_WHITELIST_IPS", []),
})

# Paths exemptés
EXEMPT_PATHS: frozenset[str] = frozenset({
    "/health/live",
    "/health/ready",
    "/health/startup",
    "/metrics",
})


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting avec sliding window.
    Identification par IP + User-ID (si authentifié).
    """

    def __init__(self, app, requests_per_minute: int = 100, burst_size: int = 20):
        super().__init__(app)
        self.limiter = SlidingWindowRateLimiter(
            redis=redis_pool,
            requests_per_minute=requests_per_minute,
            burst_size=burst_size,
        )

    def _get_identifier(self, request: Request) -> str:
        """Identifie le client par IP ou user_id si authentifié."""
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        # Fallback sur IP (gérer les proxys)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        return f"ip:{request.client.host}" if request.client else "ip:unknown"

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip pour les paths exemptés
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Skip pour les IPs whitelistées
        client_ip = request.client.host if request.client else None
        if client_ip in WHITELISTED_IPS:
            return await call_next(request)

        identifier = self._get_identifier(request)

        try:
            allowed, headers = await self.limiter.check(identifier)
        except Exception as e:
            # Si Redis est down, laisser passer (fail open)
            logger.error("rate_limiter_redis_error", error=str(e)[:200])
            return await call_next(request)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "retry_after": int(headers.get("Retry-After", 60)),
                },
                headers=headers,
            )

        response: Response = await call_next(request)

        # Ajouter les headers de rate limit sur toutes les réponses
        for header, value in headers.items():
            response.headers[header] = value

        return response
```

**Registration dans `main.py`** :

```python
from app.middleware.rate_limiter import RateLimitMiddleware

app.add_middleware(RateLimitMiddleware, requests_per_minute=100, burst_size=20)
```

**Repo GitHub de référence** : [slowapi](https://github.com/laurentS/slowapi) — 1.2k+ stars. Pour le pattern sliding window : [Redis rate limiting patterns](https://redis.io/docs/latest/develop/use/patterns/rate-limiting/).

**Erreurs courantes à éviter** :
- **Fixed window** : un pic de 100 requêtes à 0:59 + 100 à 1:00 = 200 en 2 secondes. Le sliding window résout ce problème.
- **Fail closed** : si Redis est down, toutes les requêtes sont bloquées. Toujours fail open en cas d'erreur Redis.
- **Rate limit sur l'IP derrière un CDN** : toutes les requêtes viennent de la même IP. Utiliser `X-Forwarded-For` ou un header custom.

**Astuce non-évidente** : Le `burst_size` est indépendant du `requests_per_minute`. Un client peut faire 100 requêtes en 1 minute (RPM respecté) mais jamais plus de 20 en 10 secondes. Cela protège contre les rafales qui surchargent le backend sans violer le quota global.

---

## 10. Dockerfile Multi-Stage Optimisé

**Fichier** : `Dockerfile`

```dockerfile
# ============================================================
# Stage 1 : Builder — install deps, compile extensions
# ============================================================
FROM python:3.13-slim AS builder

# Metadata OCI
LABEL org.opencontainers.image.title="TelecomLabSaaS"
LABEL org.opencontainers.image.description="Telecom Lab SaaS Platform"
LABEL org.opencontainers.image.vendor="TelecomLabSaaS"
LABEL org.opencontainers.image.source="https://github.com/your-org/telecomlabsaas"

# Empêcher les prompts interactifs
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Dépendances système pour compiler (psycopg, cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Créer un virtualenv isolé (copié dans le stage runtime)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copier et installer les dépendances AVANT le code source (cache Docker)
COPY requirements.txt .
RUN pip install --no-compile -r requirements.txt

# ============================================================
# Stage 2 : Runtime — slim, non-root, sécurisé
# ============================================================
FROM python:3.13-slim AS runtime

# Labels OCI (hérités du builder si besoin)
LABEL org.opencontainers.image.title="TelecomLabSaaS"

# Variables runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Defaults surchargés par docker-compose/k8s
    ENVIRONMENT=production \
    PORT=8000

# Runtime deps uniquement (pas de build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Copier le virtualenv depuis le builder
COPY --from=builder /opt/venv /opt/venv

# Créer un utilisateur non-root
RUN groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home appuser

# Copier le code source
WORKDIR /app
COPY --chown=appuser:appuser . .

# Permissions
RUN chmod -R 755 /app

# Passer en non-root
USER appuser

# Port exposé (documentation)
EXPOSE ${PORT}

# Signal d'arrêt
STOPSIGNAL SIGTERM

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/live || exit 1

# Point d'entrée avec tini (PID 1 correct, signal forwarding)
ENTRYPOINT ["tini", "--"]

# Commande par défaut
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--access-log", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
```

**Fichier** : `.dockerignore`

```
# Version control
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.egg-info
*.egg
dist
build
.eggs
.mypy_cache
.pytest_cache
.ruff_cache
.coverage
htmlcov

# Virtual environments
venv
.venv
env

# IDE
.vscode
.idea
*.swp
*.swo

# Docker (pas d'inception)
Dockerfile
docker-compose*.yml
.dockerignore

# Docs & CI
docs
README.md
LICENSE
CHANGELOG.md
.github
.gitlab-ci.yml
Makefile

# Environnement
.env
.env.*
!.env.example

# Tests (pas en prod)
tests
test_*
conftest.py

# Frontend build artifacts (si séparé)
node_modules
frontend/node_modules

# Data & logs
*.log
*.sql
data/
backups/
```

**Registration** : pas de changement dans `main.py` — le Dockerfile remplace l'existant.

**Repo GitHub de référence** : [docker-python-best-practices](https://github.com/docker/getting-started) et [python-docker (Google)](https://github.com/GoogleCloudPlatform/python-docs-samples). Le Docker official best practices guide est la meilleure référence.

**Erreurs courantes à éviter** :
- **Pas de `tini`** : sans init system, le process Python est PID 1 et ne forward pas les signaux correctement. `tini` résout ça en 300KB.
- **`COPY . .` avant `pip install`** : invalide le cache Docker à chaque changement de code. Copier `requirements.txt` d'abord.
- **`USER root`** : une vulnérabilité dans l'app = accès root dans le container. Toujours utiliser un user non-root.
- **Oublier `--no-install-recommends`** : installe des packages inutiles (+200MB).

**Astuce non-évidente** : `PYTHONFAULTHANDLER=1` imprime un traceback Python même en cas de segfault (crash dans une extension C comme asyncpg ou cryptography). Sauveur de vies en production quand vous debuggez un crash sans stack trace.

---

## 11. OpenTelemetry Integration

**Fichier** : `app/core/telemetry.py`

```python
"""
OpenTelemetry setup pour FastAPI :
- Traces : FastAPI, asyncpg, Redis, httpx
- Métriques : Request count, latency, DB pool
- Corrélation avec structlog (trace_id dans les logs)
"""
import structlog
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.semconv.resource import ResourceAttributes

# Auto-instrumentation
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from app.core.config import settings

logger = structlog.get_logger()


def _create_resource() -> Resource:
    return Resource.create({
        SERVICE_NAME: "telecomlabsaas",
        SERVICE_VERSION: settings.APP_VERSION,
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT,
        "service.instance.id": settings.HOSTNAME,
    })


def _setup_tracing(resource: Resource):
    """Configure le TracerProvider avec export console (dev) ou OTLP (prod)."""
    provider = TracerProvider(resource=resource)

    if settings.ENVIRONMENT == "production" and settings.OTLP_ENDPOINT:
        # Production : export OTLP vers Jaeger/Tempo/etc.
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        exporter = OTLPSpanExporter(endpoint=settings.OTLP_ENDPOINT)
    else:
        # Dev : console
        exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def _setup_metrics(resource: Resource):
    """Configure le MeterProvider."""
    if settings.ENVIRONMENT == "production" and settings.OTLP_ENDPOINT:
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )
        reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=settings.OTLP_ENDPOINT),
            export_interval_millis=30000,
        )
    else:
        reader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(),
            export_interval_millis=60000,
        )

    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)


def setup_telemetry(app):
    """
    Point d'entrée unique pour configurer toute la télémétrie.
    Appeler dans le lifespan startup.
    """
    resource = _create_resource()

    _setup_tracing(resource)
    _setup_metrics(resource)

    # Auto-instrumentation des frameworks
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health/.*,metrics",  # Pas de traces pour les healthchecks
    )
    AsyncPGInstrumentor().instrument()
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    logger.info(
        "telemetry_initialized",
        environment=settings.ENVIRONMENT,
        otlp_endpoint=settings.OTLP_ENDPOINT or "console",
    )


def shutdown_telemetry():
    """Flush et shutdown propre des providers."""
    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()

    meter_provider = metrics.get_meter_provider()
    if hasattr(meter_provider, "shutdown"):
        meter_provider.shutdown()
```

**Fichier** : `app/core/telemetry_structlog.py` — Corrélation trace_id ↔ logs

```python
"""
Processeur structlog pour injecter trace_id et span_id depuis OpenTelemetry.
"""
from opentelemetry import trace


def inject_trace_context(logger, method, event_dict):
    """Ajoute trace_id et span_id au log si un span est actif."""
    span = trace.get_current_span()
    if span and span.is_recording():
        ctx = span.get_span_context()
        if ctx.trace_id:
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict
```

**Requirements additionnelles** :

```
opentelemetry-api>=1.25.0
opentelemetry-sdk>=1.25.0
opentelemetry-instrumentation-fastapi>=0.46b0
opentelemetry-instrumentation-asyncpg>=0.46b0
opentelemetry-instrumentation-redis>=0.46b0
opentelemetry-instrumentation-httpx>=0.46b0
opentelemetry-exporter-otlp-proto-grpc>=1.25.0
```

**Registration dans `main.py`** :

```python
from app.core.telemetry import setup_telemetry, shutdown_telemetry

# Dans le lifespan :
# STARTUP
setup_telemetry(app)

# SHUTDOWN
shutdown_telemetry()

# Dans logging_config.py, ajouter le processeur aux shared_processors :
from app.core.telemetry_structlog import inject_trace_context
# shared_processors.append(inject_trace_context)
```

**Repo GitHub de référence** : [opentelemetry-python](https://github.com/open-telemetry/opentelemetry-python) — 1.8k+ stars. [opentelemetry-python-contrib](https://github.com/open-telemetry/opentelemetry-python-contrib) — 700+ stars pour les instrumentations.

**Erreurs courantes à éviter** :
- **Tracer les healthchecks** : génère du bruit (80%+ des traces) et coûte cher en stockage. Toujours exclure avec `excluded_urls`.
- **`SimpleSpanProcessor` en production** : exporte de manière synchrone → bloque l'event loop. Toujours `BatchSpanProcessor`.
- **Oublier `shutdown_telemetry()`** : les derniers spans/métriques sont perdus au shutdown.

**Astuce non-évidente** : Le `trace_id` OpenTelemetry dans les logs structlog permet de faire une recherche `trace_id=abc123` dans Loki/ELK pour retrouver **tous les logs** d'une requête, y compris les logs SQL asyncpg et les appels Redis. C'est le pont entre traces et logs — impossible sans cette corrélation.

---

## 12. Error Tracking (Sentry-like)

**Fichier** : `app/core/error_tracking.py`

```python
"""
Error tracking avec Sentry (ou GlitchTip self-hosted).
Capture automatique des exceptions avec context enrichi.
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import structlog

from app.core.config import settings
from app.middleware.request_id import request_id_ctx, current_user_id_ctx

logger = structlog.get_logger()


def _before_send(event, hint):
    """
    Hook appelé avant d'envoyer un event à Sentry.
    Permet de filtrer ou enrichir les events.
    """
    # Filtrer les erreurs non-intéressantes
    if "exc_info" in hint:
        exc_type, exc_value, _ = hint["exc_info"]
        # Ne pas tracker les 404, déconnexions client, etc.
        ignored_exceptions = (
            "ConnectionResetError",
            "BrokenPipeError",
            "asyncio.CancelledError",
        )
        if exc_type.__name__ in ignored_exceptions:
            return None

    # Enrichir avec le request_id
    rid = request_id_ctx.get()
    if rid:
        event.setdefault("tags", {})["request_id"] = rid

    return event


def _before_send_transaction(event, hint):
    """Filtre les transactions (traces) non-intéressantes."""
    # Ne pas envoyer les healthchecks comme transactions
    transaction = event.get("transaction", "")
    if any(path in transaction for path in ["/health/", "/metrics"]):
        return None
    return event


def _set_user_context():
    """Callback Sentry pour injecter le user context."""
    uid = current_user_id_ctx.get()
    if uid and uid != "anonymous":
        sentry_sdk.set_user({"id": uid})


def init_error_tracking():
    """
    Initialise Sentry/GlitchTip.
    Compatible avec Sentry self-hosted et GlitchTip (open-source).
    """
    dsn = getattr(settings, "SENTRY_DSN", None)
    if not dsn:
        logger.info("error_tracking_disabled", reason="SENTRY_DSN not configured")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=settings.ENVIRONMENT,
        release=f"telecomlabsaas@{settings.APP_VERSION}",
        # Sampling
        traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
        profiles_sample_rate=0.1,
        # Hooks
        before_send=_before_send,
        before_send_transaction=_before_send_transaction,
        # Intégrations
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            CeleryIntegration(monitor_beat_tasks=True),
            RedisIntegration(),
            HttpxIntegration(),
            AsyncioIntegration(),
            LoggingIntegration(
                level=None,           # Ne pas capturer les logs comme breadcrumbs par défaut
                event_level="ERROR",  # Capturer ERROR+ comme events Sentry
            ),
        ],
        # Breadcrumbs (derniers events avant le crash)
        max_breadcrumbs=50,
        # Données sensibles
        send_default_pii=False,
        # Performance
        enable_tracing=True,
    )

    logger.info(
        "error_tracking_initialized",
        dsn_host=dsn.split("@")[-1].split("/")[0] if "@" in dsn else "unknown",
        environment=settings.ENVIRONMENT,
    )
```

**Fichier** : `app/middleware/sentry_context.py`

```python
"""
Middleware pour enrichir le contexte Sentry avec les infos de la requête.
"""
import sentry_sdk
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.request_id import request_id_ctx


class SentryContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        with sentry_sdk.new_scope() as scope:
            # Enrichir le scope avec le contexte de la requête
            scope.set_tag("request_id", request_id_ctx.get())
            scope.set_tag("endpoint", request.url.path)
            scope.set_tag("method", request.method)

            # User context
            user_id = getattr(request.state, "user_id", None)
            if user_id:
                scope.set_user({"id": str(user_id)})

            # Module (extrait du path)
            parts = request.url.path.strip("/").split("/")
            if len(parts) >= 3:  # /api/v1/module/...
                scope.set_tag("module", parts[2])

            response: Response = await call_next(request)

            if response.status_code >= 500:
                scope.set_tag("status_code", str(response.status_code))

            return response
```

**Docker Compose pour GlitchTip (alternative open-source à Sentry)** :

```yaml
# docker-compose.monitoring.yml
services:
  glitchtip:
    image: glitchtip/glitchtip:latest
    depends_on:
      - glitchtip-db
      - glitchtip-redis
    ports:
      - "8090:8080"
    environment:
      DATABASE_URL: postgresql://glitchtip:secret@glitchtip-db/glitchtip
      REDIS_URL: redis://glitchtip-redis:6379/0
      SECRET_KEY: your-secret-key-here
      GLITCHTIP_DOMAIN: https://errors.yourdomain.com
      DEFAULT_FROM_EMAIL: errors@yourdomain.com
      EMAIL_URL: smtp://localhost:25
    volumes:
      - glitchtip-uploads:/code/uploads

  glitchtip-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: glitchtip
      POSTGRES_USER: glitchtip
      POSTGRES_PASSWORD: secret
    volumes:
      - glitchtip-pgdata:/var/lib/postgresql/data

  glitchtip-redis:
    image: redis:7-alpine

  glitchtip-worker:
    image: glitchtip/glitchtip:latest
    command: ./bin/run-celery-with-beat.sh
    depends_on:
      - glitchtip-db
      - glitchtip-redis
    environment:
      DATABASE_URL: postgresql://glitchtip:secret@glitchtip-db/glitchtip
      REDIS_URL: redis://glitchtip-redis:6379/0
      SECRET_KEY: your-secret-key-here

volumes:
  glitchtip-pgdata:
  glitchtip-uploads:
```

**Registration dans `main.py`** :

```python
from app.core.error_tracking import init_error_tracking
from app.middleware.sentry_context import SentryContextMiddleware

# Au tout début, avant le lifespan
init_error_tracking()

app.add_middleware(SentryContextMiddleware)
```

**Repo GitHub de référence** : [sentry-python](https://github.com/getsentry/sentry-python) — 1.9k+ stars. [GlitchTip](https://github.com/mikekosulin/glitchtip-backend) — open-source Sentry alternative. [sentry self-hosted](https://github.com/getsentry/self-hosted) — 4k+ stars.

**Erreurs courantes à éviter** :
- **`traces_sample_rate=1.0` en production** : capture 100% des transactions → facture Sentry explosive ou surcharge GlitchTip. 0.1 (10%) est un bon début.
- **`send_default_pii=True`** : envoie IPs, cookies, headers auth à Sentry. Violation RGPD directe.
- **Ne pas filtrer les `ConnectionResetError`** : le client qui ferme sa connexion n'est pas un bug applicatif — ces erreurs polluent le dashboard.

**Astuce non-évidente** : GlitchTip est compatible avec le SDK `sentry-python` sans aucun changement de code — juste pointer le DSN vers votre instance GlitchTip. C'est un drop-in replacement pour Sentry self-hosted, mais beaucoup plus léger (1 container vs 20+ pour Sentry self-hosted).

---

## Ordre d'activation des middleware dans `main.py`

L'ordre est critique — Starlette exécute les middleware en **ordre inverse** de leur déclaration (le dernier `add_middleware` est le premier exécuté) :

```python
"""
main.py — Ordre complet des middleware.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging_config import configure_logging
from app.core.error_tracking import init_error_tracking
from app.core.lifecycle import lifespan

# ── 0. Logging (avant tout) ──
configure_logging()

# ── 0b. Error tracking (après logging) ──
init_error_tracking()

# ── App ──
app = FastAPI(
    title="TelecomLabSaaS",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# ── Middleware (ordre inverse d'exécution) ──
# Premier exécuté ← en bas
# Dernier exécuté ← en haut

# 7. Compression (exécuté en dernier, compresse la réponse finale)
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500)

# 6. Security Headers
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# 5. Request Logging (mesure le temps total incluant tous les middleware ci-dessous)
from app.middleware.logging_middleware import RequestLoggingMiddleware
app.add_middleware(RequestLoggingMiddleware)

# 4. Rate Limiting
from app.middleware.rate_limiter import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=100, burst_size=20)

# 3. Sentry Context
from app.middleware.sentry_context import SentryContextMiddleware
app.add_middleware(SentryContextMiddleware)

# 2. Shutdown Guard
from app.middleware.shutdown_guard import ShutdownGuardMiddleware
app.add_middleware(ShutdownGuardMiddleware)

# 1. Request ID (exécuté en premier — tout le reste en dépend)
from app.middleware.request_id import RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)

# 0. CORS (avant tout — requis pour les preflight OPTIONS)
from starlette.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ──
from app.api.health import router as health_router
app.include_router(health_router)

# ... autres routers auto-découverts ...
```

---

## Checklist de déploiement

```
□ Security Headers     → curl -I https://api.example.com | grep -i strict
□ Request ID           → curl -v → vérifier X-Request-ID dans la réponse
□ Compression          → curl -H "Accept-Encoding: gzip" → vérifier Content-Encoding
□ Graceful Shutdown    → docker stop api → vérifier les logs "drained"
□ Health Checks        → curl /health/ready → vérifier les checks DB/Redis
□ DB Pool              → /debug/db-pool → vérifier pool_size et overflow
□ Structured Logging   → docker logs api | jq . → vérifier JSON + request_id
□ Circuit Breaker      → /debug/circuit-breakers → vérifier les états
□ Rate Limiting        → ab -n 200 -c 10 → vérifier 429 + headers
□ Docker Image         → docker images → vérifier taille < 500MB
□ OpenTelemetry        → Jaeger UI → vérifier les traces inter-services
□ Error Tracking       → GlitchTip/Sentry → provoquer une 500, vérifier l'event
```

---

## Résumé des dépendances à ajouter

```
# requirements.txt — ajouts
structlog>=24.1.0
sentry-sdk[fastapi,celery,sqlalchemy,httpx,asyncio]>=2.0.0
opentelemetry-api>=1.25.0
opentelemetry-sdk>=1.25.0
opentelemetry-instrumentation-fastapi>=0.46b0
opentelemetry-instrumentation-asyncpg>=0.46b0
opentelemetry-instrumentation-redis>=0.46b0
opentelemetry-instrumentation-httpx>=0.46b0
opentelemetry-exporter-otlp-proto-grpc>=1.25.0
brotli>=1.1.0  # optionnel, pour la compression Brotli
tini  # installé via apt dans le Dockerfile, pas pip
```

> **Toutes les dépendances sont open-source et gratuites.** GlitchTip remplace Sentry SaaS. OpenTelemetry est 100% vendor-neutral. Redis est déjà dans le stack.
