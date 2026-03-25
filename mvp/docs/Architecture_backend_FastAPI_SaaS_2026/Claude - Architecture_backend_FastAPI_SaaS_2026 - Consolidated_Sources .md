# Enterprise FastAPI Architecture — S+++ Définitif

> **Guide consolidé** : meilleurs éléments de Claude, ChatGPT, Gemini, Perplexity, Ethy & ithy
> **Stack** : FastAPI 0.135 · Python 3.13 · PostgreSQL 16 · Redis 7 · Celery · Docker Compose / K8s
> **Principe** : Chaque module = 1 fichier indépendant, zéro breaking change, zéro dépendance payante

---

## Table des matières

1. [Security Headers Middleware](#1-security-headers-middleware)
2. [Request ID / Correlation ID](#2-request-id--correlation-id-middleware)
3. [Gzip/Brotli Compression](#3-gzipbrotli-compression-middleware)
4. [Graceful Shutdown](#4-graceful-shutdown)
5. [Health Checks K8s-ready](#5-health-checks-avancés-kubernetes-ready)
6. [Database Connection Pooling](#6-database-connection-pooling)
7. [Structured Logging Enterprise](#7-structured-logging-enterprise)
8. [Circuit Breaker AI Providers](#8-circuit-breaker-pour-ai-providers)
9. [API Rate Limiting avancé](#9-api-rate-limiting-avancé)
10. [Dockerfile Multi-Stage](#10-dockerfile-multi-stage-optimisé)
11. [OpenTelemetry Integration](#11-opentelemetry-integration)
12. [Error Tracking (Sentry)](#12-error-tracking-sentry)
13. [Bonus S++++ : Event-Driven, Audit Log, Multi-Tenant RLS](#13-bonus-s-event-driven-audit-log-multi-tenant-rls)

---

## 1. Security Headers Middleware

**Fichier** : `app/middleware/security_headers.py`

```python
"""
Enterprise security headers middleware — OWASP 2026.
Headers statiques pré-calculés pour minimiser la latence.
CSP paramétrable par environnement.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injecte les headers de sécurité recommandés par OWASP sur toutes les réponses.
    Supporte une CSP personnalisable et un mode report-only pour les migrations.
    """

    def __init__(
        self,
        app,
        *,
        csp_policy: str | None = None,
        hsts_max_age: int = 63072000,
        csp_report_only: bool = False,
    ):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.csp_report_only = csp_report_only
        self.csp_policy = csp_policy or self._default_csp()

        # Headers statiques — calculés une seule fois au startup
        self._static_headers: dict[str, str] = {
            "Strict-Transport-Security": f"max-age={self.hsts_max_age}; includeSubDomains; preload",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), bluetooth=()"
            ),
            # Headers Cross-Origin (protection contre Spectre/Meltdown side-channels)
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

    @staticmethod
    def _default_csp() -> str:
        directives = [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "object-src 'none'",
            "upgrade-insecure-requests",
        ]
        return "; ".join(directives)

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # Injecter tous les headers statiques
        for header, value in self._static_headers.items():
            response.headers[header] = value

        # CSP — mode report-only optionnel pour les migrations
        csp_header = (
            "Content-Security-Policy-Report-Only"
            if self.csp_report_only
            else "Content-Security-Policy"
        )
        response.headers[csp_header] = self.csp_policy

        # Cache-Control spécifique aux endpoints API (pas les assets statiques)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
        elif request.url.path.startswith("/static/"):
            response.headers.setdefault("Cache-Control", "public, max-age=31536000, immutable")

        # Supprimer le header Server (information disclosure)
        response.headers.pop("Server", None)

        return response
```

**Ligne dans `main.py`** :

```python
from app.middleware.security_headers import SecurityHeadersMiddleware

# En dev/staging — mode report-only pour identifier les blocages sans casser le front
app.add_middleware(SecurityHeadersMiddleware, csp_report_only=True)

# En production — CSP enforced
app.add_middleware(SecurityHeadersMiddleware)

# CSP personnalisée (si connect-src vers API AI)
app.add_middleware(
    SecurityHeadersMiddleware,
    csp_policy="default-src 'self'; connect-src 'self' https://api.anthropic.com",
)
```

**Repo GitHub** : [helmetjs/helmet](https://github.com/helmetjs/helmet) — 10k+ stars (concept de référence, JS). Python : [VolkanSah/Securing-FastAPI-Applications](https://github.com/VolkanSah/Securing-FastAPI-Applications) — implémentation OWASP.

**Erreurs courantes** :
- CSP trop permissive (`*`, `unsafe-eval`) → annule toute la protection XSS
- HSTS `includeSubDomains` activé alors que certains sous-domaines sont encore en HTTP → casse tout
- `no-store` sur les assets statiques → chaque page reload télécharge tout (perf -80%)
- Oublier `frame-ancestors 'none'` dans la CSP (X-Frame-Options est ignoré quand CSP est présent)

**Astuces non-évidentes** :
- **`Content-Security-Policy-Report-Only`** pendant les migrations : identifie les blocages sans interrompre le service utilisateur. Exposer la CSP effective dans les métriques Prometheus pour corréler avec les erreurs de chargement front.
- **`Cross-Origin-Opener-Policy: same-origin`** protège contre les attaques Spectre/Meltdown via `SharedArrayBuffer`. Souvent oublié mais requis pour les audits SOC2 2026.
- Commencer avec `max-age=300` en staging, monter à 2 ans (63072000) en production une fois validé.

---

## 2. Request ID / Correlation ID Middleware

**Fichier** : `app/middleware/request_id.py`

```python
"""
Request ID middleware avec propagation structlog + Celery + httpx.
Utilise contextvars pour la propagation thread-safe dans tout le lifecycle async.
"""
import contextvars
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

# ContextVar accessible depuis n'importe où dans l'application
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)
current_user_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_user_id", default=""
)


def get_request_id() -> str:
    """Helper pour accéder au request_id depuis n'importe où."""
    return request_id_ctx.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    - Lit X-Request-ID entrant (propagation inter-services / API Gateway)
    - Sinon génère un UUID4 hex (32 chars, sans tirets = plus compact en logs)
    - Valide la longueur (protection contre log injection)
    - Stocke dans contextvars + structlog.contextvars
    - Retourne X-Request-ID dans le header de réponse
    """

    HEADER_NAME = "X-Request-ID"
    MAX_LENGTH = 64

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming_id = request.headers.get(self.HEADER_NAME)

        # Valider le request_id entrant (protection log injection)
        if incoming_id and len(incoming_id) <= self.MAX_LENGTH and incoming_id.isascii():
            rid = incoming_id
        else:
            rid = uuid.uuid4().hex

        # Stocker dans contextvars (accessible partout en async)
        token = request_id_ctx.set(rid)

        # Bind dans structlog pour cette requête
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=rid)

        # Stocker dans request.state pour accès synchrone dans les dépendances
        request.state.request_id = rid

        try:
            response: Response = await call_next(request)
        finally:
            request_id_ctx.reset(token)

        response.headers[self.HEADER_NAME] = rid
        return response
```

**Fichier** : `app/celery/request_id.py`

```python
"""
Propagation du request_id vers les Celery tasks via les headers.
"""
from celery import signals
import structlog
from app.middleware.request_id import request_id_ctx


@signals.before_task_publish.connect
def propagate_request_id_to_task(headers: dict, **kwargs):
    """Injecte le request_id dans les headers Celery avant publication."""
    rid = request_id_ctx.get("")
    if rid:
        headers["x_request_id"] = rid


@signals.task_prerun.connect
def extract_request_id_from_task(task, **kwargs):
    """Récupère le request_id depuis les headers Celery au début de la task."""
    rid = None
    if task.request.headers:
        rid = task.request.headers.get("x_request_id")
    if not rid:
        rid = getattr(task.request, "x_request_id", None)
    if rid:
        request_id_ctx.set(rid)
        structlog.contextvars.bind_contextvars(request_id=rid)


@signals.task_postrun.connect
def clear_request_id_after_task(**kwargs):
    """Nettoie le contextvar après exécution de la task."""
    request_id_ctx.set("")
    structlog.contextvars.clear_contextvars()
```

**Propagation httpx (appels AI sortants)** — `app/core/http_client.py` :

```python
"""
Client httpx qui propage automatiquement le request_id dans les appels sortants.
"""
import httpx
from app.middleware.request_id import get_request_id


class CorrelatedHTTPClient:
    """Wrapper httpx qui injecte X-Request-ID dans tous les appels sortants."""

    def __init__(self, **kwargs):
        self._client = httpx.AsyncClient(**kwargs)

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        rid = get_request_id()
        if rid:
            headers["X-Request-ID"] = rid
        return await self._client.request(method, url, headers=headers, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def get(self, url: str, **kwargs) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def aclose(self):
        await self._client.aclose()
```

**Lignes dans `main.py`** :

```python
from app.middleware.request_id import RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)
```

```python
# celery_app.py
import app.celery.request_id  # noqa: F401 — side-effect import pour les signals
```

**Repo GitHub** : [snok/asgi-correlation-id](https://github.com/snok/asgi-correlation-id) — ~500 stars, pattern ASGI de référence. [tomwojcik/starlette-context](https://github.com/tomwojcik/starlette-context) pour une approche plus générique.

**Erreurs courantes** :
- `threading.local()` au lieu de `contextvars` → cassé en async
- Ne pas valider le request_id entrant → log injection (un attaquant envoie un header de 10 MB)
- Oublier la propagation Celery → les tasks sont impossibles à corréler avec la requête HTTP
- Ne pas propager dans les appels httpx sortants → le tracing distribué s'arrête à ton service

**Astuces non-évidentes** :
- Exposer le `request_id` dans les réponses d'erreur 4xx/5xx **JSON payload** (pas seulement le header) : les équipes support peuvent copier-coller l'ID depuis le front sans ouvrir les DevTools.
- Utiliser le format **W3C `traceparent`** en complément de X-Request-ID pour la compatibilité native avec les collecteurs OpenTelemetry.
- `structlog.contextvars.bind_contextvars()` est le mécanisme le plus puissant : il ajoute du contexte à TOUS les logs d'une requête sans passage explicite de paramètres.

---

## 3. Gzip/Brotli Compression Middleware

**Fichier** : `app/middleware/compression.py`

```python
"""
Compression intelligente : Gzip + Brotli (si disponible).
Exclut SSE, /metrics, health checks. Seuil minimum 500 bytes.
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


EXCLUDED_PATHS = frozenset({
    "/metrics",
    "/health/live",
    "/health/ready",
    "/health/startup",
})

EXCLUDED_PREFIXES = (
    "/api/v1/stream",
    "/api/v1/events",
    "/api/v1/sse",
)


class CompressionExclusionMiddleware(BaseHTTPMiddleware):
    """
    Marque les requêtes qui ne doivent PAS être compressées.
    Doit être ajouté AVANT GZipMiddleware dans la stack.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        skip_compression = (
            path in EXCLUDED_PATHS
            or path.startswith(EXCLUDED_PREFIXES)
            or request.headers.get("accept") == "text/event-stream"
        )

        response: Response = await call_next(request)

        if skip_compression:
            response.headers.pop("Content-Encoding", None)
            response.headers["X-No-Compression"] = "1"

        return response


class BrotliMiddleware:
    """
    Middleware ASGI Brotli. Compresse les réponses > minimum_size
    si le client supporte br encoding.
    Quality 4 = sweet spot vitesse/compression pour les APIs temps réel.
    """

    def __init__(self, app: ASGIApp, *, minimum_size: int = 500, quality: int = 4):
        self.app = app
        self.minimum_size = minimum_size
        self.quality = quality

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        accept_encoding = headers.get(b"accept-encoding", b"").decode()

        if "br" not in accept_encoding:
            await self.app(scope, receive, send)
            return

        response_body = []
        initial_message = None

        async def send_wrapper(message):
            nonlocal initial_message
            if message["type"] == "http.response.start":
                initial_message = message
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                more_body = message.get("more_body", False)

                if more_body:
                    # Streaming response — ne pas compresser
                    if initial_message:
                        await send(initial_message)
                        initial_message = None
                    await send(message)
                    return

                response_body.append(body)

                if not more_body:
                    full_body = b"".join(response_body)

                    if len(full_body) >= self.minimum_size:
                        compressed = brotli.compress(full_body, quality=self.quality)
                        if len(compressed) < len(full_body):
                            headers_list = list(initial_message["headers"])
                            headers_list = [
                                (k, v) for k, v in headers_list
                                if k.lower() not in (
                                    b"content-length", b"content-encoding", b"etag"
                                )
                            ]
                            headers_list.append((b"content-encoding", b"br"))
                            headers_list.append(
                                (b"content-length", str(len(compressed)).encode())
                            )
                            headers_list.append((b"vary", b"Accept-Encoding"))
                            initial_message["headers"] = headers_list
                            full_body = compressed

                    await send(initial_message)
                    await send({"type": "http.response.body", "body": full_body})

        await self.app(scope, receive, send_wrapper)
```

**Lignes dans `main.py`** :

```python
from starlette.middleware.gzip import GZipMiddleware
from app.middleware.compression import (
    CompressionExclusionMiddleware, BrotliMiddleware, BROTLI_AVAILABLE,
)

app.add_middleware(CompressionExclusionMiddleware)
if BROTLI_AVAILABLE:
    app.add_middleware(BrotliMiddleware, minimum_size=500, quality=4)
else:
    app.add_middleware(GZipMiddleware, minimum_size=500)
```

**Dépendance optionnelle** : `pip install brotli` — alternative : [fullonic/brotli-asgi](https://github.com/fullonic/brotli-asgi) pour un middleware prêt à l'emploi.

**Repo GitHub** : [google/brotli](https://github.com/google/brotli) — 13k+ stars.

**Erreurs courantes** :
- Compresser les endpoints SSE → buffering casse le streaming temps réel
- Brotli `quality > 6` en temps réel → 50× plus lent, bloque le thread. Quality 4 max pour les APIs
- Compresser des réponses déjà compressées (images JPEG) → augmente la taille
- Oublier de supprimer l'ETag après compression → les caches intermédiaires servent du contenu corrompu
- Ne pas ajouter `Vary: Accept-Encoding` → des proxies cachent la version compressée et la servent aux clients qui ne supportent pas Brotli

**Astuce non-évidente** : 500 bytes est le sweet spot réel mesuré en production. En dessous, l'overhead CPU de la compression dépasse le gain de bande passante. `GZipMiddleware` natif Starlette est un middleware ASGI pur (pas `BaseHTTPMiddleware`), donc plus performant et compatible streaming natif — pour la plupart des cas, c'est suffisant sans le wrapper Brotli custom.

---

## 4. Graceful Shutdown

**Fichier** : `app/lifecycle/shutdown.py`

```python
"""
Graceful shutdown pour FastAPI + asyncpg + Redis + Celery.
Signal handler (SIGTERM/SIGINT) → drain HTTP → fermeture pools → exit.
"""
import asyncio
import logging
import signal
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


class GracefulShutdownManager:
    """Coordonne l'arrêt propre de tous les composants."""

    def __init__(self, *, drain_timeout: float = 30.0):
        self.drain_timeout = drain_timeout
        self._shutting_down = False
        self._active_requests: int = 0
        self._shutdown_event = asyncio.Event()

    @property
    def is_shutting_down(self) -> bool:
        return self._shutting_down

    def track_request_start(self) -> None:
        self._active_requests += 1

    def track_request_end(self) -> None:
        self._active_requests -= 1
        if self._shutting_down and self._active_requests <= 0:
            self._shutdown_event.set()

    async def wait_for_drain(self) -> None:
        if self._active_requests <= 0:
            return
        logger.info(
            "Draining %d active requests (timeout=%ss)...",
            self._active_requests, self.drain_timeout,
        )
        try:
            await asyncio.wait_for(
                self._shutdown_event.wait(), timeout=self.drain_timeout
            )
            logger.info("All requests drained successfully.")
        except asyncio.TimeoutError:
            logger.warning(
                "Drain timeout. %d requests still active — forcing shutdown.",
                self._active_requests,
            )

    def initiate_shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        logger.info("Graceful shutdown initiated.")
        if self._active_requests <= 0:
            self._shutdown_event.set()


shutdown_manager = GracefulShutdownManager(drain_timeout=30.0)


def _install_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: (
            logger.info("Received signal %s", s.name),
            shutdown_manager.initiate_shutdown(),
        ))


@asynccontextmanager
async def lifespan(app) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan : setup au démarrage, cleanup au shutdown.
    Uvicorn gère déjà SIGTERM en interne (arrête d'accepter de nouvelles connexions).
    Ce handler est la couche supplémentaire pour le drain + cleanup des pools.
    """
    from app.core.database import engine, init_database
    from app.core.redis import redis_pool
    from app.api.health import mark_startup_complete

    loop = asyncio.get_running_loop()
    _install_signal_handlers(loop)

    # === STARTUP ===
    await init_database()
    # ... charger les modules auto-découverts ...
    mark_startup_complete(modules=["module1", "module2"])  # adapter
    logger.info("Application startup complete.")

    yield

    # === SHUTDOWN SEQUENCE ===
    logger.info("Starting shutdown sequence...")

    # 1. Drain des requêtes HTTP en cours
    await shutdown_manager.wait_for_drain()

    # 2. Fermeture Redis
    try:
        await redis_pool.aclose()
        logger.info("Redis pool closed.")
    except Exception as exc:
        logger.error("Error closing Redis pool: %s", exc)

    # 3. Fermeture asyncpg/SQLAlchemy
    try:
        if isinstance(engine, AsyncEngine):
            await engine.dispose()
        logger.info("Database pool disposed.")
    except Exception as exc:
        logger.error("Error disposing database pool: %s", exc)

    logger.info("Shutdown sequence complete.")
```

**Fichier** : `app/middleware/shutdown_tracking.py`

```python
"""
Middleware : refuse les nouvelles requêtes pendant le shutdown + track les requêtes actives.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from app.lifecycle.shutdown import shutdown_manager


class ShutdownTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if shutdown_manager.is_shutting_down:
            return JSONResponse(
                {"detail": "Service is shutting down. Please retry."},
                status_code=503,
                headers={"Retry-After": "5", "Connection": "close"},
            )

        shutdown_manager.track_request_start()
        try:
            return await call_next(request)
        finally:
            shutdown_manager.track_request_end()
```

**Celery warm shutdown** dans `celery_app.py` :

```python
from celery import Celery
from celery.signals import worker_shutting_down

celery_app = Celery("telecomlabsaas")

celery_app.conf.update(
    worker_prefetch_multiplier=1,       # 1 seule task dans le buffer (pas 4)
    worker_max_tasks_per_child=1000,    # Recycle le worker (fuite mémoire)
    task_acks_late=True,                # ACK APRÈS exécution (pas avant)
    task_reject_on_worker_lost=True,    # Re-queue si le worker crash
    worker_cancel_long_running_tasks_on_connection_loss=True,
)


@worker_shutting_down.connect
def on_worker_shutting_down(sig, how, exitcode, **kwargs):
    import structlog
    structlog.get_logger().info("celery_warm_shutdown", signal=sig, how=how)
```

**Docker Compose** :

```yaml
services:
  api:
    stop_signal: SIGTERM
    stop_grace_period: 45s  # > drain_timeout (30s) + marge
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  celery_worker:
    stop_signal: SIGTERM
    stop_grace_period: 120s  # Assez pour finir les tasks longues (AI inference)
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
```

**Lignes dans `main.py`** :

```python
from app.lifecycle.shutdown import lifespan
from app.middleware.shutdown_tracking import ShutdownTrackingMiddleware

app = FastAPI(lifespan=lifespan)
app.add_middleware(ShutdownTrackingMiddleware)
```

**Repo GitHub** : [encode/uvicorn](https://github.com/encode/uvicorn) — 8k+ stars. [emmett-framework/granian](https://github.com/emmett-framework/granian) — 3k+ stars (ASGI server avec graceful shutdown natif).

**Erreurs courantes** :
- `stop_grace_period` trop court → Docker SIGKILL avant la fin du drain → requêtes perdues
- `task_acks_late=False` (défaut Celery) → si le worker crash, la task est perdue
- Oublier `worker_prefetch_multiplier=1` → Celery pré-fetche 4 tasks, 3 sont perdues au shutdown
- Ne pas renvoyer 503 + `Connection: close` pendant le shutdown → le LB continue d'envoyer du trafic

**Astuces non-évidentes** :
- Toujours coupler graceful shutdown + readiness probe → sinon K8s envoie encore du trafic.
- Utiliser `exec` dans l'entrypoint Docker pour que le process Python remplace le shell et reçoive directement SIGTERM.
- Uvicorn a son propre `--timeout-graceful-shutdown` qu'il faut coordonner avec le lifespan handler.

---

## 5. Health Checks avancés (Kubernetes-ready)

**Fichier** : `app/api/health.py`

```python
"""
Health check endpoints Kubernetes-ready.
3 probes distinctes avec checks RÉELS sur les dépendances.
"""
import asyncio
import time
from typing import Any

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.core.database import async_session_factory
from app.core.redis import redis_pool
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])

_startup_time: float = 0.0
_startup_complete: bool = False
_loaded_modules: list[str] = []


def mark_startup_complete(modules: list[str]) -> None:
    global _startup_time, _startup_complete, _loaded_modules
    _startup_time = time.time()
    _startup_complete = True
    _loaded_modules = modules


# --- LIVENESS PROBE ---
@router.get("/live", status_code=200)
async def liveness() -> dict[str, Any]:
    """
    Liveness : l'app est-elle vivante ?
    Retourne 200 tant que le process tourne.
    K8s RESTART le pod si cette probe échoue.
    ⚠️ NE JAMAIS checker les dépendances ici.
    """
    return {
        "status": "alive",
        "uptime_seconds": round(time.time() - _startup_time, 1) if _startup_time else 0,
    }


# --- READINESS PROBE ---
@router.get("/ready")
async def readiness(response: Response) -> dict[str, Any]:
    """
    Readiness : l'app peut-elle servir du trafic ?
    Vérifie PostgreSQL + Redis.
    K8s RETIRE le pod du load balancer si cette probe échoue.
    """
    from app.lifecycle.shutdown import shutdown_manager

    # Si shutdown en cours → immédiatement not ready (sortir du LB)
    if shutdown_manager.is_shutting_down:
        response.status_code = 503
        return {"status": "shutting_down"}

    checks: dict[str, dict[str, Any]] = {}

    # Check PostgreSQL
    try:
        start = time.monotonic()
        async with async_session_factory() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=3.0)
        latency = round((time.monotonic() - start) * 1000, 1)
        checks["postgresql"] = {"status": "ok", "latency_ms": latency}
    except asyncio.TimeoutError:
        checks["postgresql"] = {"status": "timeout", "error": "Query exceeded 3s"}
    except Exception as exc:
        checks["postgresql"] = {"status": "error", "error": str(exc)[:200]}

    # Check Redis
    try:
        start = time.monotonic()
        pong = await asyncio.wait_for(redis_pool.ping(), timeout=2.0)
        latency = round((time.monotonic() - start) * 1000, 1)
        checks["redis"] = {"status": "ok" if pong else "error", "latency_ms": latency}
    except asyncio.TimeoutError:
        checks["redis"] = {"status": "timeout", "error": "Ping exceeded 2s"}
    except Exception as exc:
        checks["redis"] = {"status": "error", "error": str(exc)[:200]}

    all_ok = all(c["status"] == "ok" for c in checks.values())
    response.status_code = 200 if all_ok else 503

    return {"status": "ready" if all_ok else "not_ready", "checks": checks}


# --- STARTUP PROBE ---
@router.get("/startup")
async def startup_probe(response: Response) -> dict[str, Any]:
    """
    Startup : l'init est-elle terminée ?
    K8s attend avant d'activer liveness/readiness.
    """
    if not _startup_complete:
        response.status_code = 503
        return {"status": "starting", "modules_loaded": []}

    migration_ok = True
    migration_error = None
    try:
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            )
            version = result.scalar_one_or_none()
            if version is None:
                migration_ok = False
                migration_error = "No migration version found"
    except Exception as exc:
        migration_ok = False
        migration_error = str(exc)[:200]

    all_ok = _startup_complete and migration_ok
    response.status_code = 200 if all_ok else 503

    return {
        "status": "started" if all_ok else "starting",
        "modules_count": len(_loaded_modules),
        "modules": _loaded_modules,
        "migration_ok": migration_ok,
        "version": settings.VERSION,
        "build_sha": settings.BUILD_SHA,  # Pour vérifier quelle release tourne
    }
```

**Config Kubernetes** :

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 10
  failureThreshold: 3
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  failureThreshold: 2
startupProbe:
  httpGet:
    path: /health/startup
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 3
  failureThreshold: 30  # 30 × 3s = 90s max pour démarrer
```

**Ligne dans `main.py`** :

```python
from app.api.health import router as health_router, mark_startup_complete
app.include_router(health_router)
```

**Repo GitHub** : [kubernetes.io probes docs](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) — référence officielle.

**Erreurs courantes** :
- **Liveness qui check la DB** → si PostgreSQL lag, K8s restart TOUS les pods → cascade failure + thundering herd à la reconnexion
- `initialDelaySeconds` trop court → pods tués pendant le chargement des 25 modules
- Timeout de la probe > periodSeconds → les probes s'empilent
- Health checks qui retournent `200` sans vrai check → faux sentiment de sécurité

**Astuces non-évidentes** :
- Faire échouer la readiness dès le début du signal de shutdown → sortir du LB avant le drain.
- Versionner le payload (`version`, `build_sha`) → voir en un coup d'œil quels pods ont la dernière release dans le dashboard K8s.
- `startupProbe` avec `failureThreshold=30` et `periodSeconds=3` → 90s pour les cold starts lents (chargement de modèles ML, migrations). Pendant le startup, liveness/readiness sont suspendues.

---

## 6. Database Connection Pooling

**Fichier** : `app/core/database.py`

```python
"""
Configuration optimale du pool asyncpg pour PostgreSQL 16.
Retry avec backoff, health checks, métriques Prometheus, et monitoring des connexions lentes.
"""
import asyncio
import logging
import time

from prometheus_client import Gauge
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)

# === Prometheus Metrics ===
DB_POOL_SIZE = Gauge("db_pool_size", "Current pool size")
DB_POOL_CHECKED_IN = Gauge("db_pool_checked_in", "Connections available in pool")
DB_POOL_CHECKED_OUT = Gauge("db_pool_checked_out", "Connections in use")
DB_POOL_OVERFLOW = Gauge("db_pool_overflow", "Overflow connections")
DB_POOL_SATURATION = Gauge("db_pool_saturation_ratio", "checked_out / (size + overflow)")


def _create_engine() -> AsyncEngine:
    return create_async_engine(
        settings.DATABASE_URL,  # postgresql+asyncpg://user:pass@host:5432/db
        poolclass=AsyncAdaptedQueuePool,

        # Pool sizing — règle : max_connections PG / nb_pods >= pool_size + max_overflow
        pool_size=20,
        max_overflow=10,        # Total max = 30

        # Timeouts
        pool_timeout=10,        # Max 10s pour obtenir une connexion du pool
        pool_recycle=1800,      # Recycle connexions > 30min (évite stale connections firewalls)

        # Health checks
        pool_pre_ping=True,     # SELECT 1 avant chaque checkout (~0.5ms overhead)

        # Performance
        echo=settings.DEBUG,
        echo_pool=False,

        # AsyncPG specific
        connect_args={
            "server_settings": {
                "application_name": "telecomlabsaas",
                "jit": "off",                          # JIT off pour queries OLTP courtes
                "statement_timeout": "30000",           # 30s max par statement
                "idle_in_transaction_session_timeout": "60000",
            },
            "command_timeout": 30,
        },
    )


def _register_pool_events(engine: AsyncEngine) -> None:
    """Event listeners pour métriques du pool + monitoring connexions lentes."""

    @event.listens_for(engine.sync_engine.pool, "checkout")
    def _on_checkout(dbapi_conn, connection_record, connection_proxy):
        connection_record.info["checkout_time"] = time.monotonic()
        _update_metrics(engine)

    @event.listens_for(engine.sync_engine.pool, "checkin")
    def _on_checkin(dbapi_conn, connection_record):
        checkout_time = connection_record.info.get("checkout_time")
        if checkout_time:
            duration = time.monotonic() - checkout_time
            if duration > 5.0:
                logger.warning("slow_db_connection_usage", extra={"duration_s": round(duration, 2)})
        _update_metrics(engine)

    def _update_metrics(eng):
        pool = eng.sync_engine.pool
        size = pool.size()
        checked_out = pool.checkedout()
        DB_POOL_SIZE.set(size)
        DB_POOL_CHECKED_IN.set(pool.checkedin())
        DB_POOL_CHECKED_OUT.set(checked_out)
        DB_POOL_OVERFLOW.set(pool.overflow())
        max_total = size + pool.overflow()
        DB_POOL_SATURATION.set(checked_out / max_total if max_total > 0 else 0)


async def create_engine_with_retry(
    *, max_retries: int = 5, base_delay: float = 1.0
) -> AsyncEngine:
    """Crée le moteur avec retry et exponential backoff."""
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            eng = _create_engine()
            async with eng.begin() as conn:
                await conn.execute(text("SELECT 1"))
            _register_pool_events(eng)
            logger.info("Database connected (attempt %d/%d)", attempt, max_retries)
            return eng
        except Exception as exc:
            last_exc = exc
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "Database connection failed (attempt %d/%d): %s — retrying in %.1fs",
                attempt, max_retries, exc, delay,
            )
            if attempt < max_retries:
                await asyncio.sleep(delay)

    raise RuntimeError(f"Could not connect after {max_retries} attempts") from last_exc


# === Globals initialisés dans le lifespan ===
engine: AsyncEngine
async_session_factory: async_sessionmaker[AsyncSession]


async def init_database() -> None:
    global engine, async_session_factory
    engine = await create_engine_with_retry()
    async_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False,
    )
```

**Ligne dans `main.py`** (lifespan) :

```python
from app.core.database import init_database
await init_database()
```

**Repo GitHub** : [sqlalchemy/sqlalchemy](https://github.com/sqlalchemy/sqlalchemy) — 10k+ stars.

**Erreurs courantes** :
- `pool_size` trop grand → épuise `max_connections` PostgreSQL (défaut: 100). Formule : `pool_size ≈ vCPUs × 2 / nb_instances`
- Oublier `pool_pre_ping=True` → connexions stale après restart PG → crash en rafale
- `expire_on_commit=True` (défaut) → lazy loading en async = crash
- Ne pas mettre `statement_timeout` → une query folle bloque une connexion indéfiniment

**Astuces non-évidentes** :
- **`jit: off`** : le JIT PostgreSQL est conçu pour les queries analytiques longues (OLAP). Pour les queries OLTP courtes (<100ms), le coût de compilation JIT (5-50ms) > gain d'exécution. Gain typique : **-20% latence P95**.
- Le ratio **`DB_POOL_SATURATION`** (`checked_out / total`) est souvent un signal plus fiable que la latence moyenne SQL comme SLO de saturation DB.
- `asyncpg` avec `max_queries=50000` au niveau du driver prévient les fuites mémoire sur les connexions très longue durée.

---

## 7. Structured Logging Enterprise

**Fichier** : `app/core/logging_config.py`

```python
"""
Configuration structlog enterprise.
JSON en prod, coloré en dev. Request ID, User ID, trace_id, filtering automatiques.
"""
import logging
import re
import sys
import structlog
from typing import Any

from app.core.config import settings


# Clés sensibles à masquer (recherche récursive dans les dicts imbriqués)
_SENSITIVE_KEYS = frozenset({
    "password", "passwd", "secret", "token", "api_key", "authorization",
    "cookie", "session_id", "credit_card", "ssn", "access_token",
    "refresh_token", "private_key",
})

_SENSITIVE_PATTERNS = [
    (re.compile(r"(Bearer\s+)\S+", re.IGNORECASE), r"\1[REDACTED]"),
]


def _filter_sensitive_data(
    logger: Any, method_name: str, event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Filtre récursif des données sensibles dans tous les champs."""

    def _clean(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: ("[REDACTED]" if k.lower() in _SENSITIVE_KEYS else _clean(v))
                for k, v in obj.items()
            }
        if isinstance(obj, str):
            for pattern, replacement in _SENSITIVE_PATTERNS:
                obj = pattern.sub(replacement, obj)
        return obj

    return _clean(event_dict)


def _add_service_info(
    logger: Any, method_name: str, event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    event_dict.setdefault("service", settings.SERVICE_NAME)
    event_dict.setdefault("environment", settings.ENVIRONMENT)
    event_dict.setdefault("deployment", settings.DEPLOYMENT)  # blue, canary, etc.
    return event_dict


def _add_otel_trace_context(
    logger: Any, method_name: str, event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Injecte trace_id/span_id OpenTelemetry dans chaque log."""
    try:
        from opentelemetry.trace import get_current_span
        span = get_current_span()
        if span and span.get_span_context().is_valid:
            ctx = span.get_span_context()
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
    except ImportError:
        pass
    return event_dict


def configure_logging() -> None:
    """
    Configure structlog + stdlib logging.
    Appeler UNE SEULE FOIS au startup, AVANT tout autre import qui utilise structlog.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_service_info,
        _add_otel_trace_context,
        _filter_sensitive_data,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.ENVIRONMENT == "production":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,  # CRITIQUE : sans ça, ~50µs overhead par log
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Log levels par module
    root_logger.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.DEBUG else logging.WARNING
    )
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
```

**Fichier** : `app/middleware/request_logging.py`

```python
"""
Middleware de logging des requêtes HTTP avec timing + user_id.
"""
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.middleware.request_id import current_user_id_ctx

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    SKIP_PATHS = frozenset({"/health/live", "/health/ready", "/health/startup", "/metrics"})

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()

        # Extraire user_id si disponible (après auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            current_user_id_ctx.set(str(user_id))
            structlog.contextvars.bind_contextvars(user_id=str(user_id))

        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        log_method = logger.info if response.status_code < 400 else logger.warning
        if response.status_code >= 500:
            log_method = logger.error

        log_method(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "")[:100],
        )

        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        return response
```

**Lignes dans `main.py`** :

```python
from app.core.logging_config import configure_logging
from app.middleware.request_logging import RequestLoggingMiddleware

configure_logging()  # AVANT la création de l'app
app.add_middleware(RequestLoggingMiddleware)
```

**Repo GitHub** : [hynek/structlog](https://github.com/hynek/structlog) — 3.5k+ stars.

**Erreurs courantes** :
- Configurer structlog APRÈS les imports → loggers cachés avec la mauvaise config
- `logging.basicConfig()` appelé quelque part → override silencieusement structlog
- `time.time()` au lieu de `time.perf_counter()` → résolution ~15ms sur Windows, sensible au NTP
- Logger les request bodies → violation RGPD, passwords en clair dans les logs
- Ne pas réduire le bruit de `uvicorn.access` → 1000+ logs/minute inutiles en prod

**Astuces non-évidentes** :
- Le filtrage récursif (`_clean`) est nécessaire car les données sensibles peuvent être dans des dicts imbriqués (ex: `{"user": {"password": "xxx"}}`). Un filtrage superficiel rate ces cas.
- Ajouter un champ `deployment` (blue, canary, prod) dans chaque log → filtrer finement dans Grafana/Loki.
- `cache_logger_on_first_use=True` est **critique** : sans ça, structlog reconstruit la chain de processors à chaque appel.
- L'injection du `trace_id` OpenTelemetry directement dans structlog permet de passer d'un log d'erreur à la trace complète en un clic dans Grafana.

---

## 8. Circuit Breaker pour AI Providers

**Fichier** : `app/infra/circuit_breaker.py`

```python
"""
Circuit breaker zero-dependency pour les providers AI.
3 états : CLOSED (normal), OPEN (skip), HALF_OPEN (test recovery).
asyncio.Lock pour la sécurité des coroutines concurrentes.
"""
import asyncio
import enum
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

CB_STATE = Gauge("circuit_breaker_state", "State (0=closed, 1=open, 2=half_open)", ["provider"])
CB_FAILURES = Counter("circuit_breaker_failures_total", "Total failures", ["provider"])
CB_FALLBACKS = Counter("circuit_breaker_fallbacks_total", "Fallback activations", ["from_provider", "to_provider"])


class CircuitState(enum.IntEnum):
    CLOSED = 0
    OPEN = 1
    HALF_OPEN = 2


@dataclass
class CircuitBreaker:
    """
    Circuit breaker avec sliding window et asyncio.Lock.

    Usage:
        cb = CircuitBreaker(name="claude", failure_threshold=5, recovery_timeout=90)
        result = await cb.call(my_async_function, *args, **kwargs)
    """
    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    window_size: float = 60.0
    half_open_max_calls: int = 3    # 3 succès consécutifs pour refermer (plus robuste que 1)

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failures: deque = field(default_factory=deque, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _half_open_successes: int = field(default=0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    @property
    def state(self) -> CircuitState:
        return self._state

    def _clean_old_failures(self) -> None:
        cutoff = time.monotonic() - self.window_size
        while self._failures and self._failures[0] < cutoff:
            self._failures.popleft()

    def _transition_to(self, new_state: CircuitState) -> None:
        old = self._state
        self._state = new_state
        CB_STATE.labels(provider=self.name).set(new_state.value)
        logger.info("Circuit [%s]: %s -> %s", self.name, CircuitState(old).name, new_state.name)

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Exécute func à travers le circuit breaker. Raise CircuitOpenError si ouvert."""
        async with self._lock:
            now = time.monotonic()

            if self._state == CircuitState.OPEN:
                if now - self._last_failure_time >= self.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    self._half_open_successes = 0
                else:
                    remaining = self.recovery_timeout - (now - self._last_failure_time)
                    raise CircuitOpenError(
                        f"Circuit [{self.name}] OPEN. Recovery in {remaining:.0f}s"
                    )

        # Exécution EN DEHORS du lock
        try:
            result = await func(*args, **kwargs)
        except Exception as exc:
            await self._record_failure(exc)
            raise
        else:
            await self._record_success()
            return result

    async def _record_failure(self, error: Exception) -> None:
        async with self._lock:
            now = time.monotonic()
            self._failures.append(now)
            self._last_failure_time = now
            CB_FAILURES.labels(provider=self.name).inc()
            self._clean_old_failures()

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
                self._half_open_successes = 0
            elif len(self._failures) >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    async def _record_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_successes += 1
                if self._half_open_successes >= self.half_open_max_calls:
                    self._transition_to(CircuitState.CLOSED)
                    self._failures.clear()
                    self._half_open_successes = 0


class CircuitOpenError(Exception):
    pass


@dataclass
class AIProviderChain:
    """
    Chaîne de providers AI avec fallback automatique par priorité.

    Usage:
        chain = AIProviderChain(providers=[
            ("claude", claude_cb, call_claude),
            ("gemini", gemini_cb, call_gemini),
            ("groq",   groq_cb,   call_groq),
        ])
        result = await chain.execute(prompt="Hello")
    """
    providers: list[tuple[str, CircuitBreaker, Callable]]

    async def execute(self, **kwargs: Any) -> Any:
        last_exc: Exception | None = None

        for i, (name, cb, func) in enumerate(self.providers):
            try:
                return await cb.call(func, **kwargs)
            except CircuitOpenError:
                logger.info("Provider [%s] circuit open — trying next", name)
                last_exc = CircuitOpenError(f"[{name}] open")
            except Exception as exc:
                logger.warning("Provider [%s] failed: %s — trying next", name, exc)
                last_exc = exc
                if i + 1 < len(self.providers):
                    next_name = self.providers[i + 1][0]
                    CB_FALLBACKS.labels(from_provider=name, to_provider=next_name).inc()

        raise RuntimeError(f"All AI providers failed. Last: {last_exc}") from last_exc
```

**Repo GitHub** : [resilience4j/resilience4j](https://github.com/resilience4j/resilience4j) — 10k+ stars (Java, mais design de référence). Python : [danielfm/pybreaker](https://github.com/danielfm/pybreaker).

**Erreurs courantes** :
- Un seul circuit breaker pour tous les providers → un timeout Gemini bloque Claude
- Compter les timeouts clients comme des failures provider → ouvre le circuit inutilement
- `recovery_timeout` < timeout API du provider (Claude peut prendre 60s+) → oscille en boucle
- `half_open_max_calls=1` → décision binaire fragile, augmenter à 3

**Astuces non-évidentes** :
- L'`asyncio.Lock` est **critique** même en single-threaded : asyncio interleave les coroutines entre les `await`. Sans lock, deux coroutines peuvent ouvrir le circuit deux fois.
- Utiliser un circuit breaker **par modèle d'IA** (pas par provider) : GPT-4 peut être down alors que GPT-3.5 fonctionne sur la même API OpenAI.
- Le `window_size` évite qu'une erreur vieille de 12h participe au décompte → seules les erreurs **récentes** comptent.

---

## 9. API Rate Limiting avancé

**Fichier** : `app/middleware/rate_limiter.py`

```python
"""
Rate limiter sliding window + burst. Redis sorted sets.
Lua script pour atomicité (pas de race conditions).
"""
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.redis import redis_pool

logger = logging.getLogger(__name__)

WHITELIST_IPS: frozenset[str] = frozenset({"127.0.0.1", "::1"})
EXCLUDED_PATHS: frozenset[str] = frozenset({
    "/health/live", "/health/ready", "/health/startup", "/metrics",
})

# Script Lua atomique — garantit la cohérence même sous haute concurrence
RATE_LIMIT_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local current_count = redis.call('ZCARD', key)

if current_count < limit then
    redis.call('ZADD', key, now, tostring(now) .. ':' .. tostring(math.random(1000000)))
    redis.call('EXPIRE', key, window + 1)
    return {0, limit - current_count - 1}
else
    return {1, 0}
end
"""


class SlidingWindowRateLimiter(BaseHTTPMiddleware):
    """
    Sliding window rate limiter avec Redis + Lua (atomique).
    Dual check : rate limit global (100/min) + burst limit (20/10s).
    """

    def __init__(
        self,
        app,
        *,
        requests_per_minute: int = 100,
        burst_limit: int = 20,
        burst_window_seconds: int = 10,
    ):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.burst_limit = burst_limit
        self.burst_window = burst_window_seconds
        self._lua_sha: str | None = None

    async def _ensure_lua_loaded(self) -> str:
        """Charge le script Lua une seule fois (EVALSHA est plus rapide que EVAL)."""
        if self._lua_sha is None:
            self._lua_sha = await redis_pool.script_load(RATE_LIMIT_LUA)
        return self._lua_sha

    async def _check_limit(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Returns (allowed, remaining)."""
        now = time.time()
        try:
            sha = await self._ensure_lua_loaded()
            result = await redis_pool.evalsha(sha, 1, key, now, window, limit)
            blocked = result[0] == 1
            remaining = result[1]
            return not blocked, remaining
        except Exception:
            # Script not loaded (Redis restart) — fallback to EVAL
            result = await redis_pool.eval(RATE_LIMIT_LUA, 1, key, now, window, limit)
            self._lua_sha = None
            blocked = result[0] == 1
            remaining = result[1]
            return not blocked, remaining

    def _get_client_key(self, request: Request) -> str:
        ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", "")
        return f"{ip}:{user_id}" if user_id else ip

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        if client_ip in WHITELIST_IPS:
            return await call_next(request)

        client_key = self._get_client_key(request)

        try:
            # 1. Burst check
            burst_ok, _ = await self._check_limit(
                f"rl:burst:{client_key}", self.burst_limit, self.burst_window
            )
            if not burst_ok:
                return self._rate_limit_response(self.burst_limit, 0, self.burst_window)

            # 2. Global check
            global_ok, remaining = await self._check_limit(
                f"rl:global:{client_key}", self.rpm, 60
            )
            if not global_ok:
                return self._rate_limit_response(self.rpm, 0, 60)

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.rpm)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
            return response

        except Exception as exc:
            # Fail open si Redis est down
            logger.error("Rate limiter error (failing open): %s", exc)
            return await call_next(request)

    @staticmethod
    def _rate_limit_response(limit: int, remaining: int, retry_after: int) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded", "type": "rate_limit_error"},
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                "Retry-After": str(retry_after),
            },
        )
```

**Ligne dans `main.py`** :

```python
from app.middleware.rate_limiter import SlidingWindowRateLimiter
app.add_middleware(SlidingWindowRateLimiter, requests_per_minute=100, burst_limit=20)
```

**Repo GitHub** : [laurentS/slowapi](https://github.com/laurentS/slowapi) — 1k+ stars. Pour l'algo : [Redis rate limiting patterns](https://redis.io/docs/latest/develop/use/patterns/rate-limiter/).

**Erreurs courantes** :
- Fixed window → permet 2× le rate limit à la frontière (100 à 0:59 + 100 à 1:00)
- Pipeline Redis non-atomique → race conditions sous forte concurrence (d'où le Lua)
- Rate limiter les health checks K8s → pods marqués "not ready" → downtime
- `Retry-After` manquant → les clients bien faits spamment au lieu d'attendre

**Astuces non-évidentes** :
- `EVALSHA` est ~30% plus rapide que `EVAL` car Redis ne re-parse pas le script. Le `script_load` au démarrage amortit le coût.
- Le "fail open" est **intentionnel** : un rate limiter qui crash quand Redis tombe = DoS auto-infligé.
- La clé Lua utilise `math.random()` dans le membre du sorted set pour éviter les collisions quand deux requêtes arrivent au même timestamp.
- `Retry-After` précis en secondes → les clients bien faits (httpx, axios) savent exactement quand réessayer.

---

## 10. Dockerfile Multi-Stage Optimisé

**Fichier** : `Dockerfile`

```dockerfile
# ============================================
# STAGE 1: Builder — Install deps, compile
# ============================================
FROM python:3.13-slim AS builder

LABEL org.opencontainers.image.title="telecomlabsaas-api" \
      org.opencontainers.image.description="TelecomLabSaaS FastAPI Backend" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.source="https://github.com/org/telecomlabsaas"

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier SEULEMENT les fichiers de dépendances (cache Docker layer)
COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# ============================================
# STAGE 2: Runtime — Slim, non-root, sécurisé
# ============================================
FROM python:3.13-slim AS runtime

LABEL org.opencontainers.image.title="telecomlabsaas-api"

# Dépendances runtime uniquement (pas de build-essential !)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Utilisateur non-root
RUN groupadd --gid 1001 appuser \
    && useradd --uid 1001 --gid 1001 --shell /bin/false --create-home appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /home/appuser/app
COPY --chown=appuser:appuser . .

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

STOPSIGNAL SIGTERM

# tini comme init (reap zombies, forward signals)
ENTRYPOINT ["tini", "--"]

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--timeout-graceful-shutdown", "30", \
     "--log-level", "info", \
     "--no-access-log"]
```

**Fichier** : `.dockerignore`

```
.git
.gitignore
__pycache__
*.pyc
*.pyo
*.egg-info
.eggs
dist
build
.venv
venv
.vscode
.idea
tests/
pytest.ini
.pytest_cache
.coverage
htmlcov/
.github
.gitlab-ci.yml
Dockerfile
docker-compose*.yml
.dockerignore
docs/
*.md
LICENSE
CHANGELOG
.env
.env.*
node_modules/
```

**Repo GitHub** : [GoogleContainerTools/distroless](https://github.com/GoogleContainerTools/distroless) — 18k+ stars. Pour `uv` : [astral-sh/uv-docker-example](https://github.com/astral-sh/uv).

**Erreurs courantes** :
- `USER root` en production → une RCE donne accès root au container
- `COPY . .` AVANT `pip install` → le cache Docker est invalidé à chaque changement de code
- `.env` dans l'image → fuite de secrets dans le registry
- Oublier `PYTHONDONTWRITEBYTECODE=1` → `__pycache__` en read-only filesystem = crash

**Astuces non-évidentes** :
- **`tini`** comme ENTRYPOINT est **essentiel** : sans init process, les signaux SIGTERM ne sont pas forwardés correctement, et les processus zombies s'accumulent. Docker ajoute `--init` sur `docker run` mais PAS dans Docker Compose ni Kubernetes.
- `--no-access-log` sur Uvicorn → les logs d'accès sont gérés par le middleware structlog. Sans ça, doublons.
- Alternative à pip : **`uv`** avec `UV_COMPILE_BYTECODE=1` pré-compile les `.py` en `.pyc` au build → -15% temps de démarrage du premier endpoint.
- Utiliser `exec` dans l'entrypoint shell pour que le process Python remplace le shell et reçoive directement SIGTERM.

---

## 11. OpenTelemetry Integration

**Fichier** : `app/observability/otel.py`

```python
"""
OpenTelemetry setup complet : traces + metrics.
Auto-instrumentation FastAPI, SQLAlchemy, Redis, httpx.
Corrélation avec structlog via trace_id.
"""
import logging
import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import settings

logger = logging.getLogger(__name__)


def setup_opentelemetry(app=None, engine=None) -> None:
    resource = Resource.create({
        "service.name": settings.SERVICE_NAME,
        "service.version": settings.VERSION,
        "deployment.environment": settings.ENVIRONMENT,
    })

    provider = TracerProvider(resource=resource)

    if settings.ENVIRONMENT == "production":
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("OTel: OTLP exporter → %s", otlp_endpoint)
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("OTel: Console exporter (dev)")

    trace.set_tracer_provider(provider)

    # Auto-instrumentation FastAPI (exclure health checks)
    if app is not None:
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health/live,health/ready,health/startup,metrics",
        )

    # Auto-instrumentation SQLAlchemy/asyncpg
    if engine is not None:
        SQLAlchemyInstrumentor().instrument(
            engine=engine.sync_engine,
            enable_commenter=True,  # Ajoute trace_id en commentaire SQL !
        )

    # Redis + httpx
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    logger.info("OpenTelemetry initialized (FastAPI + SQLAlchemy + Redis + httpx)")
```

**Ligne dans `main.py`** :

```python
from app.observability.otel import setup_opentelemetry
# Dans le lifespan, après init_database() :
setup_opentelemetry(app=app, engine=engine)
```

**Dépendances** :

```
opentelemetry-api>=1.27.0
opentelemetry-sdk>=1.27.0
opentelemetry-exporter-otlp-proto-grpc>=1.27.0
opentelemetry-instrumentation-fastapi>=0.48b0
opentelemetry-instrumentation-sqlalchemy>=0.48b0
opentelemetry-instrumentation-redis>=0.48b0
opentelemetry-instrumentation-httpx>=0.48b0
```

**Repo GitHub** : [open-telemetry/opentelemetry-python](https://github.com/open-telemetry/opentelemetry-python) — 1.8k+ stars.

**Erreurs courantes** :
- Instrumenter les health checks → milliers de spans inutiles par minute, coûts qui explosent
- `ConsoleSpanExporter` en prod → stdout saturé
- Oublier `insecure=True` pour le collector local → TLS error silencieux, pas de traces
- Ne pas corréler logs ↔ traces → deux systèmes d'observabilité déconnectés

**Astuces non-évidentes** :
- **`enable_commenter=True`** est un game changer : il ajoute `/* trace_id=abc123 */` en commentaire SQL. Tu peux croiser les slow queries dans `pg_stat_statements` avec les traces OTel.
- La corrélation structlog ↔ OTel se fait via le processeur `_add_otel_trace_context` dans la config logging (section 7). Un log d'erreur → clic sur le `trace_id` → trace complète dans Grafana Tempo/Jaeger.
- L'instrumentation httpx capture automatiquement les appels vers Claude/Gemini/Groq avec la latence, le status code, et la propagation du contexte de trace.

---

## 12. Error Tracking (Sentry)

**Fichier** : `app/observability/error_tracking.py`

```python
"""
Intégration Sentry / GlitchTip pour le tracking d'erreurs.
Capture automatique des 500, context enrichi, sampling dynamique.
"""
import logging
import os

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.config import settings
from app.middleware.request_id import request_id_ctx

logger = logging.getLogger(__name__)


def _before_send(event: dict, hint: dict) -> dict | None:
    """Hook : filtre et enrichit les events avant envoi."""
    if "exc_info" in hint:
        exc_type = hint["exc_info"][0]
        if exc_type.__name__ in ("ConnectionResetError", "BrokenPipeError"):
            return None

    # Enrichir avec request_id
    rid = request_id_ctx.get("")
    if rid:
        event.setdefault("tags", {})["request_id"] = rid

    # Scrub données sensibles
    if "request" in event and "headers" in event["request"]:
        for key in ("authorization", "cookie", "x-api-key"):
            if key in event["request"]["headers"]:
                event["request"]["headers"][key] = "[REDACTED]"

    return event


def _traces_sampler(sampling_context: dict) -> float:
    """Sample rate dynamique : 100% sur les endpoints AI, 0% sur les health checks."""
    if sampling_context.get("parent_sampled") is not None:
        return 1.0 if sampling_context["parent_sampled"] else 0.0

    name = sampling_context.get("transaction_context", {}).get("name", "")

    if "/api/v1/ai/" in name:
        return 1.0
    if "/health/" in name or "/metrics" in name:
        return 0.0
    return 0.1  # 10% pour le reste


def init_error_tracking() -> None:
    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn:
        logger.info("Sentry DSN not configured — error tracking disabled")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=settings.ENVIRONMENT,
        release=f"{settings.SERVICE_NAME}@{settings.VERSION}",
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
            CeleryIntegration(monitor_beat_tasks=True),
            SqlalchemyIntegration(),
            RedisIntegration(),
            HttpxIntegration(),
            AsyncioIntegration(),
            LoggingIntegration(level=logging.WARNING, event_level=logging.ERROR),
        ],
        traces_sampler=_traces_sampler,
        profiles_sample_rate=0.1,
        before_send=_before_send,
        send_default_pii=False,
        request_bodies="medium",
        max_breadcrumbs=50,
        attach_stacktrace=True,
        enable_tracing=True,
        debug=settings.DEBUG,
    )
    logger.info("Sentry initialized (env=%s)", settings.ENVIRONMENT)
```

**Ligne dans `main.py`** :

```python
from app.observability.error_tracking import init_error_tracking
init_error_tracking()  # AVANT la création de l'app
```

**Dépendance** : `sentry-sdk[fastapi,celery,sqlalchemy,httpx,pure_eval]>=2.14.0`

**Repo GitHub** : [getsentry/sentry](https://github.com/getsentry/sentry) — 40k+ stars. Alternative self-hosted : [GlitchTip](https://github.com/glitchtip/glitchtip-backend) — compatible SDK Sentry.

**Erreurs courantes** :
- `send_default_pii=True` → fuite d'emails, IPs, cookies (violation RGPD)
- Pas de `before_send` → tokens JWT visibles dans les headers capturés
- `traces_sample_rate=1.0` en prod → facture qui explose, performance dégradée
- Oublier `CeleryIntegration` → erreurs dans les tasks silencieuses

**Astuces non-évidentes** :
- **`transaction_style="endpoint"`** est critique : sans ça, Sentry regroupe par URL raw (`/devices/123` ≠ `/devices/456`). Avec `endpoint`, il regroupe par route FastAPI (`/devices/{id}`).
- Le `traces_sampler` dynamique > `traces_sample_rate` fixe : 100% sur les endpoints AI critiques, 0% sur les health checks.
- GlitchTip = Sentry open-source (0€) compatible avec le même SDK.

---

## 13. Bonus S++++ : Event-Driven, Audit Log, Multi-Tenant RLS

### 13.1 Transactional Outbox (Event-Driven)

```python
# app/core/outbox.py
"""
Pattern Transactional Outbox : les events sont écrits en DB dans la même transaction
que les mutations, puis un dispatcher les publie vers NATS/Kafka.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
import uuid
from datetime import datetime, UTC


async def emit_event(
    session: AsyncSession,
    event_type: str,
    payload: dict,
    tenant_id: str,
) -> str:
    """Écrit un event dans la table outbox dans la MÊME transaction."""
    event_id = str(uuid.uuid4())
    await session.execute(
        text("""
            INSERT INTO outbox (id, type, payload, tenant_id, created_at)
            VALUES (:id, :type, :payload, :tenant_id, :created_at)
        """),
        {
            "id": event_id,
            "type": event_type,
            "payload": json.dumps(payload),
            "tenant_id": tenant_id,
            "created_at": datetime.now(UTC),
        },
    )
    return event_id
```

### 13.2 Audit Log immuable

```sql
-- Compliance-grade : INSERT only, jamais UPDATE/DELETE
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index pour la recherche
CREATE INDEX idx_audit_tenant_created ON audit_log (tenant_id, created_at DESC);
CREATE INDEX idx_audit_entity ON audit_log (entity, entity_id);

-- Protection : aucune policy UPDATE/DELETE
REVOKE UPDATE, DELETE ON audit_log FROM app_user;
```

### 13.3 Multi-Tenant RLS (Row Level Security)

```sql
-- Isolation au niveau DB, pas au niveau code
ALTER TABLE devices ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON devices
    USING (tenant_id = current_setting('app.tenant_id')::text);
```

```python
# app/middleware/tenant.py
"""Middleware qui bind le tenant_id depuis le JWT dans la session PostgreSQL."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy import text

from app.core.database import async_session_factory


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            async with async_session_factory() as session:
                # Paramétré pour éviter l'injection SQL
                await session.execute(
                    text("SET LOCAL app.tenant_id = :tid"),
                    {"tid": tenant_id},
                )
        return await call_next(request)
```

**Insight** : 99% des SaaS filtrent le tenant en Python (`WHERE tenant_id = :tid`). RLS est le seul vrai multi-tenant sécurisé — un bug dans le code ne peut PAS fuiter des données vers un autre tenant.

---

## Ordre des middlewares dans `main.py`

```python
# L'ordre d'ajout est INVERSÉ par rapport à l'exécution (Starlette onion model)
# Exécution : Request → ⑧ → ⑦ → ⑥ → ⑤ → ④ → ③ → ② → ① → Handler

app.add_middleware(SentryContextMiddleware)           # ① Près du handler
app.add_middleware(RequestLoggingMiddleware)           # ② Timing complet
app.add_middleware(SlidingWindowRateLimiter)           # ③ Rate limit
app.add_middleware(CompressionExclusionMiddleware)     # ④ Post-compression
if BROTLI_AVAILABLE:
    app.add_middleware(BrotliMiddleware)               # ⑤ Compression
else:
    app.add_middleware(GZipMiddleware)
app.add_middleware(RequestIDMiddleware)                # ⑥ Request ID (tôt)
app.add_middleware(SecurityHeadersMiddleware)          # ⑦ Security
app.add_middleware(ShutdownTrackingMiddleware)         # ⑧ Premier exécuté
```

---

## Ordre d'implémentation recommandé

```
7 → 2 → 1 → 5 → 6 → 4 → 10 → 3 → 9 → 8 → 11 → 12 → 13
```

1. **Logging (7) + Request ID (2)** : aide au debug de tout le reste
2. **Security (1) + Health Checks (5)** : la base enterprise
3. **DB Pooling (6) + Graceful Shutdown (4)** : stabilise la prod
4. **Docker (10) + Compression (3)** : optimise les performances
5. **Rate Limiting (9) + Circuit Breaker (8)** : résilience
6. **OTel (11) + Sentry (12)** : observabilité avancée
7. **Event-Driven + Audit + RLS (13)** : platform-grade

---

## Dépendances à ajouter

```
# requirements-enterprise.txt
brotli>=1.1.0
structlog>=24.4.0
opentelemetry-api>=1.27.0
opentelemetry-sdk>=1.27.0
opentelemetry-exporter-otlp-proto-grpc>=1.27.0
opentelemetry-instrumentation-fastapi>=0.48b0
opentelemetry-instrumentation-sqlalchemy>=0.48b0
opentelemetry-instrumentation-redis>=0.48b0
opentelemetry-instrumentation-httpx>=0.48b0
sentry-sdk[fastapi,celery,sqlalchemy,httpx,pure_eval]>=2.14.0
```
