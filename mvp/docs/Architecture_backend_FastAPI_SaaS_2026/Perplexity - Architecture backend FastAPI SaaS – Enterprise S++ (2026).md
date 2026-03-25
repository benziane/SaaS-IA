```markdown
# Architecture backend FastAPI SaaS – Enterprise S++ (2026)

Stack cible (rappel) : FastAPI 0.135, Python 3.13, PostgreSQL 16 (asyncpg + SQLModel), Redis 7, Celery, Docker Compose + Kubernetes.

Chaque section ci‑dessous contient :
- Fichier cible (chemin suggéré)
- Code complet (Python / Docker)
- Ligne à ajouter dans `main.py` (ou équivalent) pour l’activer
- Repo GitHub de référence (> 1000 stars) quand pertinent
- Erreurs courantes + astuce non évidente

Les exemples supposent une arborescence de type :

```text
app/
  core/
    config.py
    logging.py
    opentelemetry.py
  middleware/
    security_headers.py
    request_id.py
    compression.py
    rate_limit.py
  db/
    engine.py
    health.py
  health/
    routes.py
  observability/
    errors.py
    circuit_breaker.py
  worker/
    celery_app.py
main.py
```

Adapte les chemins à ta structure, mais garde les modules/middlewares indépendants.

---

## 1. Security Headers Middleware

### Fichier : `app/middleware/security_headers.py`

```python
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


API_CACHE_PATH_PREFIXES = ("/api", "/v1", "/v2")  # à adapter à ta convention de routing


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Ajoute des en‑têtes de sécurité sur toutes les réponses HTTP.

    - HSTS
    - CSP
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    - Cache-Control (agressif pour endpoints API)
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:  # type: ignore[override]
        response = await call_next(request)

        # Strict-Transport-Security (assume HTTPS terminé au reverse proxy)
        response.headers.setdefault(
            "Strict-Transport-Security",
            "max-age=63072000; includeSubDomains; preload",
        )

        # Content-Security-Policy : à adapter selon ton front
        csp = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
        )
        response.headers.setdefault("Content-Security-Policy", csp)

        # Clickjacking / MIME sniffing / XSS legacy
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")

        # Referrer & permissions
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()",
        )

        # Cache-Control spécifique API (évite le cache intermédiaire sur données sensibles)
        if request.url.path.startswith(API_CACHE_PATH_PREFIXES):
            # pas de cache navigateur/intermédiaires
            response.headers.setdefault(
                "Cache-Control",
                "no-store, no-cache, must-revalidate, max-age=0",
            )

        return response
```

### Ligne à ajouter dans `main.py`

```python
from app.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

### Repo GitHub de référence

- `fastapi-armor` – middleware de sécurité pour FastAPI avec headers HSTS/CSP/XFO, inspiré de helmet.js.[web:13]

### Erreurs courantes à éviter

- Mettre une CSP trop restrictive qui casse le front (scripts externes, fonts, etc.) sans coordination avec l’équipe front.[web:1]
- Activer HSTS en local (HTTP) ou avant d’avoir un certificat TLS valide en prod.
- Forcer `Cache-Control` sur tout (y compris assets statiques) au lieu de cibler les endpoints d’API.

### Astuce non évidente

Expose la CSP effective dans les métriques (Prometheus/gauge ou log structuré) pour pouvoir la corréler avec les erreurs de chargement front : tu verras tout de suite quand une release front nécessite un assouplissement.

---

## 2. Request ID / Correlation ID Middleware

### Fichier : `app/middleware/request_id.py`

```python
import contextvars
import uuid
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

import structlog

# Context var globale pour tout le cycle de la requête
request_id_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


def get_request_id() -> Optional[str]:
    return request_id_ctx_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Gère X-Request-ID et l’injection dans structlog/contextvars.

    - Reprend l’ID existant si fourni
    - Sinon génère un UUID4
    - Injection dans structlog.contextvars
    - Ajout X-Request-ID dans la réponse
    """

    def __init__(self, app: ASGIApp, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:  # type: ignore[override]
        incoming_request_id = request.headers.get(self.header_name)
        request_id = incoming_request_id or str(uuid.uuid4())

        # Bind dans contextvars
        token = request_id_ctx_var.set(request_id)

        # Bind dans structlog
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        try:
            response = await call_next(request)
        finally:
            # reset contextvar pour éviter la fuite de contexte
            request_id_ctx_var.reset(token)

        response.headers[self.header_name] = request_id
        return response
```

### Intégration structlog : `app/core/logging.py`

```python
import logging
import sys
from typing import Any, Dict

import structlog


def configure_logging(json_logs: bool = True, log_level: str = "INFO") -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=shared_processors,
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Optionnel : réduire le bruit de certains loggers tiers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(**kwargs: Any) -> structlog.stdlib.BoundLogger:
    logger = structlog.get_logger()
    if kwargs:
        return logger.bind(**kwargs)
    return logger
```

### Propagation vers Celery : `app/worker/celery_app.py`

```python
import os

from celery import Celery, signals

from app.middleware.request_id import get_request_id


CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_BACKEND_URL = os.getenv("CELERY_BACKEND_URL", "redis://redis:6379/1")

celery_app = Celery(
    "worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BACKEND_URL,
)


@signals.before_task_publish.connect
def add_request_id_to_headers(  # type: ignore[override]
    headers=None,
    **kwargs,
) -> None:
    """Injecte le request_id courant dans les headers Celery si présent."""

    if headers is None:
        headers = {}
    rid = get_request_id()
    if rid:
        headers.setdefault("X-Request-ID", rid)


@signals.task_prerun.connect
def bind_request_id_in_worker(sender=None, headers=None, **kwargs) -> None:  # type: ignore[override]
    """Rebind le request_id dans le worker pour corréler les logs côté Celery."""
    import structlog

    rid = None
    if headers and isinstance(headers, dict):
        rid = headers.get("X-Request-ID")
    if rid:
        structlog.contextvars.bind_contextvars(request_id=rid)
```

### Ligne à ajouter dans `main.py`

```python
from app.core.logging import configure_logging
from app.middleware.request_id import RequestIDMiddleware

configure_logging(json_logs=True)  # idéalement avant création de l’app

app.add_middleware(RequestIDMiddleware)
```

### Repo GitHub de référence

- Exemple d’intégration structlog + FastAPI + correlation id.[web:6][web:14]

### Erreurs courantes à éviter

- Ne pas utiliser `contextvars` (et se retrouver avec des `request_id` mélangés entre requêtes concurrentes).[web:34]
- Ré‑initialiser les `contextvars` trop tard (ex. dans un middleware aval) et perdre la valeur pour certains logs.
- Oublier de propager le header côté worker (tasks Celery non corrélées).

### Astuce non évidente

Expose `request_id` aussi dans les réponses d’erreur 4xx/5xx JSON (payload) : les équipes support peuvent copier‑coller l’ID depuis le front sans ouvrir les DevTools.

---

## 3. Gzip/Brotli Compression Middleware

### Fichier : `app/middleware/compression.py`

```python
import gzip
from io import BytesIO
from typing import Callable, Iterable

import brotli
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


EXCLUDED_PATH_PREFIXES = (
    "/metrics",  # Prometheus
)
EXCLUDED_EXACT_PATHS = (
    "/events/stream",  # exemple SSE
)


class BrotliGZipMiddleware(BaseHTTPMiddleware):
    """Middleware HTTP compression Brotli + GZip fallback.

    - Taille min configurable
    - Skip SSE et /metrics
    - Respect Accept-Encoding
    """

    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = 500,
        brotli_quality: int = 5,
    ) -> None:
        super().__init__(app)
        self.minimum_size = minimum_size
        self.brotli_quality = brotli_quality

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:  # type: ignore[override]
        path = request.url.path

        # Exclusions explicites (SSE, metrics, etc.)
        if path in EXCLUDED_EXACT_PATHS or any(
            path.startswith(prefix) for prefix in EXCLUDED_PATH_PREFIXES
        ):
            return await call_next(request)

        response = await call_next(request)

        # Ne pas recompresser si déjà encodé ou trop petit
        if "content-encoding" in response.headers:
            return response

        body = b"".join(self._iterate_body(response.body))

        if len(body) < self.minimum_size:
            response.body = body
            return response

        accept_encoding = request.headers.get("accept-encoding", "")
        accept_encoding = accept_encoding.lower()

        if "br" in accept_encoding:
            compressed_body = brotli.compress(body, quality=self.brotli_quality)
            encoding = "br"
        elif "gzip" in accept_encoding:
            compressed_body = self._gzip_compress(body)
            encoding = "gzip"
        else:
            response.body = body
            return response

        response.body = compressed_body

        # Met à jour les headers
        response.headers["Content-Encoding"] = encoding
        response.headers["Content-Length"] = str(len(compressed_body))
        # Garde le Vary pour cache intermédiaires
        vary = response.headers.get("Vary") or ""
        if "accept-encoding" not in vary.lower():
            response.headers["Vary"] = ", ".join(
                filter(None, [vary, "Accept-Encoding"])
            )

        return response

    @staticmethod
    def _gzip_compress(data: bytes) -> bytes:
        buf = BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as f:
            f.write(data)
        return buf.getvalue()

    @staticmethod
    def _iterate_body(body: Iterable[bytes] | bytes | None) -> Iterable[bytes]:
        if body is None:
            return []
        if isinstance(body, (bytes, bytearray)):
            return [body]
        return body
```

### Ligne à ajouter dans `main.py`

```python
from app.middleware.compression import BrotliGZipMiddleware

app.add_middleware(BrotliGZipMiddleware, minimum_size=500, brotli_quality=5)
```

### Repo GitHub de référence

- `brotli-asgi` – middleware ASGI Brotli pour Starlette/FastAPI.[web:3]

### Erreurs courantes à éviter

- Compresser les flux SSE / WebSocket (ça casse le protocole ou la latence).[web:11]
- Compresser à nouveau un contenu déjà compressé (double compression).
- Mettre un `minimum_size` trop faible et perdre du CPU inutilement.

### Astuce non évidente

Expose le taux de compression moyen par endpoint (bytes avant/après) dans Prometheus : tu repères rapidement les endpoints qui envoient beaucoup de JSON inutiles ou des payloads sur‑dimensionnés.

---

## 4. Graceful Shutdown FastAPI + Celery + asyncpg

### Fichier : `app/db/engine.py`

```python
import os
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@postgres:5432/app",
)


engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


async def init_engine() -> None:
    global engine, AsyncSessionLocal
    if engine is not None:
        return

    engine = create_async_engine(
        DATABASE_URL,
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),  # 30 min
        pool_pre_ping=True,
    )

    AsyncSessionLocal = async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        raise RuntimeError("Database engine not initialized")
    async with AsyncSessionLocal() as session:
        yield session


async def close_engine() -> None:
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None
```

### Fichier : `main.py` – lifespan + signaux

```python
import asyncio
import os
import signal
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app.core.logging import configure_logging, get_logger
from app.db.engine import init_engine, close_engine


configure_logging(json_logs=os.getenv("LOG_JSON", "true").lower() == "true")
logger = get_logger()

# Événement de shutdown partagé
shutdown_event = asyncio.Event()


def _install_signal_handlers() -> None:
    loop = asyncio.get_running_loop()

    def _signal_handler(sig: int) -> None:
        logger.info("received_stop_signal", signal=sig)
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(
                sig, _signal_handler, sig.value if hasattr(sig, "value") else int(sig)
            )
        except NotImplementedError:
            # Windows / environnements limités
            pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("lifespan_start")
    _install_signal_handlers()

    # Init ressources (DB, caches, etc.)
    await init_engine()

    try:
        yield
    finally:
        logger.info("lifespan_shutdown_start")

        # Donne jusqu’à 30s pour drainer les requêtes en cours
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            logger.warning("shutdown_timeout_expired")

        await close_engine()
        logger.info("lifespan_shutdown_complete")


app = FastAPI(lifespan=lifespan)
```

### Celery : shutdown warm

Dans ton process worker (entrypoint Celery), utilise `--time-limit` raisonnable et `--soft-time-limit` pour éviter des tasks qui ne s’arrêtent jamais. Exemple (command Docker) :

```bash
celery -A app.worker.celery_app.celery_app worker \
  --loglevel=INFO \
  --concurrency=4 \
  --time-limit=600 \
  --soft-time-limit=540
```

Celery gère déjà un warm shutdown sur SIGTERM : il termine les tasks en cours et n’en prend plus de nouvelles.[web:25]

### Docker Compose (graceful)

```yaml
services:
  api:
    stop_grace_period: 40s
```

### Repo GitHub de référence

- Exemple complet FastAPI + Celery + Postgres + Prometheus.[web:28]
- Discussions FastAPI/Uvicorn sur graceful shutdown et signaux.[web:19][web:22]

### Erreurs courantes à éviter

- Lancer Uvicorn avec `--reload` en prod : empêche un shutdown propre dans Docker.[web:22]
- Oublier de disposer le pool SQLAlchemy/asyncpg (fuites connexions, locks, timeouts).[web:21]
- Ne pas augmenter `stop_grace_period` dans Compose/K8s : les requêtes longues sont coupées brutalement.

### Astuce non évidente

Expose un compteur Prometheus `app_shutdown_initiated_total` et un histogramme `app_shutdown_duration_seconds` dans le lifespan : tu verras vite si tes rollouts K8s coupent trop agressivement les pods.

---

## 5. Health Checks avancés (Kubernetes‑ready)

### Fichier : `app/db/health.py`

```python
from typing import Any, Dict

from sqlalchemy import text

from app.db.engine import engine


async def check_postgres() -> Dict[str, Any]:
    if engine is None:
        return {"status": "DOWN", "reason": "engine_not_initialized"}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "UP"}
    except Exception as exc:  # pragma: no cover - pure infra path
        return {"status": "DOWN", "reason": str(exc)}
```

### Fichier : `app/health/redis_check.py`

```python
from typing import Any, Dict

import redis.asyncio as redis


async def check_redis(client: redis.Redis | None) -> Dict[str, Any]:
    if client is None:
        return {"status": "DOWN", "reason": "redis_not_initialized"}
    try:
        pong = await client.ping()
        return {"status": "UP", "pong": pong}
    except Exception as exc:  # pragma: no cover
        return {"status": "DOWN", "reason": str(exc)}
```

### Fichier : `app/health/routes.py`

```python
import asyncio
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.db.health import check_postgres
from app.health.redis_check import check_redis


router = APIRouter()

# États globaux très simples
_app_started = time.time()
_startup_completed = False


def mark_startup_complete() -> None:
    global _startup_completed
    _startup_completed = True


async def get_redis_client() -> Any:  # à remplacer par ta factory réelle
    from app.main import redis_client  # import lazy pour éviter les cycles

    return redis_client


@router.get("/health/live", tags=["health"])
async def liveness() -> Dict[str, Any]:
    return {"status": "UP", "since": _app_started}


@router.get("/health/ready", tags=["health"])
async def readiness(redis=Depends(get_redis_client)) -> JSONResponse:
    postgres_result, redis_result = await asyncio.gather(
        check_postgres(),
        check_redis(redis),
    )

    ok = (
        postgres_result.get("status") == "UP"
        and redis_result.get("status") == "UP"
    )

    payload: Dict[str, Any] = {
        "status": "UP" if ok else "DOWN",
        "postgres": postgres_result,
        "redis": redis_result,
    }

    status_code = 200 if ok else 503
    return JSONResponse(status_code=status_code, content=payload)


@router.get("/health/startup", tags=["health"])
async def startup_probe() -> JSONResponse:
    if not _startup_completed:
        return JSONResponse(
            status_code=503,
            content={
                "status": "DOWN",
                "reason": "startup_not_completed",
            },
        )
    return JSONResponse(
        status_code=200,
        content={"status": "UP", "since": _app_started},
    )
```

### Intégration dans `main.py`

```python
from fastapi import FastAPI

from app.health.routes import router as health_router, mark_startup_complete


@app.on_event("startup")
async def on_startup() -> None:
    # ... autres inits (DB, Redis, etc.)
    mark_startup_complete()


app.include_router(health_router)
```

### Extraits Docker / K8s

Docker Compose :

```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 20s
```

Kubernetes :

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: http
  initialDelaySeconds: 10
  periodSeconds: 15
readinessProbe:
  httpGet:
    path: /health/ready
    port: http
  initialDelaySeconds: 5
  periodSeconds: 10
startupProbe:
  httpGet:
    path: /health/startup
    port: http
  failureThreshold: 30
  periodSeconds: 10
```

### Repo GitHub de référence

- Implémentations de `/live` + `/ready` + checks DB/Redis en FastAPI.[web:20][web:23][web:26]

### Erreurs courantes à éviter

- Faire des health checks « fake » (`return 200`) sans réellement tester DB/Redis.[web:20]
- Rendre le liveness trop strict (utilise readiness pour la disponibilité des dépendances).
- Ajouter de la logique lente dans les probes, ce qui bloque le scheduler K8s.

### Astuce non évidente

Versionne le payload de healthcheck (`version`, `build_sha`) et utilise‑le dans les dashboards K8s : tu peux vérifier en un coup d’œil quels pods ont déjà pris la dernière release.

---

## 6. Database Connection Pooling (asyncpg + SQLModel)

### Fichier : `app/db/engine.py` (version avec retry + métriques)

```python
import asyncio
import os
from typing import AsyncGenerator

from prometheus_client import Gauge
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@postgres:5432/app",
)

DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))


engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


# Métriques simples (à exposer sur /metrics ailleurs)
DB_POOL_IN_USE = Gauge("db_pool_in_use", "Number of DB connections currently in use")
DB_POOL_MAX = Gauge("db_pool_max_size", "Max DB pool size configured")


async def init_engine_with_retry(max_retries: int = 5, backoff_base: float = 0.5) -> None:
    """Initialise l’engine SQLAlchemy avec retries (backoff exponentiel)."""

    global engine, AsyncSessionLocal
    if engine is not None:
        return

    attempt = 0
    last_exc: Exception | None = None

    while attempt < max_retries:
        try:
            engine = create_async_engine(
                DATABASE_URL,
                pool_size=DB_POOL_SIZE,
                max_overflow=DB_MAX_OVERFLOW,
                pool_timeout=DB_POOL_TIMEOUT,
                pool_recycle=DB_POOL_RECYCLE,
                pool_pre_ping=True,
            )
            AsyncSessionLocal = async_sessionmaker(
                engine,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )

            # Test simple
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            DB_POOL_MAX.set(DB_POOL_SIZE + DB_MAX_OVERFLOW)
            return
        except Exception as exc:  # pragma: no cover
            last_exc = exc
            attempt += 1
            await asyncio.sleep(backoff_base * (2 ** (attempt - 1)))

    if last_exc:
        raise last_exc


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if AsyncSessionLocal is None:
        raise RuntimeError("Database engine not initialized")

    if engine is not None:
        # best effort : `engine.pool.size()` / `checkedin()` / `checkedout()`
        try:
            pool = engine.pool
            in_use = pool.checkedout()
            DB_POOL_IN_USE.set(in_use)
        except Exception:
            pass

    async with AsyncSessionLocal() as session:
        yield session


async def close_engine() -> None:
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None
```

### Ligne à utiliser dans `main.py`

```python
from app.db.engine import init_engine_with_retry

@app.on_event("startup")
async def on_startup_db() -> None:
    await init_engine_with_retry()
```

### Repo GitHub de référence

- SQLAlchemy async engine pooling (issues/discussions autour d’asyncpg/locks/pool_pre_ping).[web:21][web:27][web:30]

### Erreurs courantes à éviter

- Ne pas activer `pool_pre_ping=True` avec des connexions longues (RDS, load balancers) : connexions mortes dans le pool.[web:30]
- Sur‑dimensionner le `pool_size` par rapport à `max_connections` Postgres → erreurs `too many connections`.
- Oublier un retry propre au boot : la première minute d’indisponibilité Postgres fait crasher tout le pod.

### Astuce non évidente

Expose en métriques le ratio `checkedout/size` et utilise‑le comme SLO de saturation DB : c’est souvent un signal plus fiable que la latence moyenne SQL.

---

## 7. Structured Logging Enterprise (structlog)

### Fichier : `app/core/logging.py` (version complétée user_id + filtrage + trace_id)

```python
import logging
import os
import sys
from typing import Any, Dict

import structlog
from opentelemetry.trace import get_current_span


SENSITIVE_KEYS = {"password", "token", "access_token", "refresh_token", "authorization"}


def _filter_sensitive_keys(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Supprime les clés sensibles des events loggués."""

    def _clean(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: ("***" if k.lower() in SENSITIVE_KEYS else _clean(v))
                for k, v in obj.items()
            }
        if isinstance(obj, (list, tuple, set)):
            return type(obj)(_clean(v) for v in obj)
        return obj

    return _clean(event_dict)


def _add_trace_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    span = get_current_span()
    if span and span.get_span_context().is_valid:
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


def configure_logging(json_logs: bool = True, log_level: str = "INFO") -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        _add_trace_context,
        structlog.stdlib.add_log_level,
        timestamper,
        _filter_sensitive_keys,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=shared_processors,
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Loggers tiers
    logging.getLogger("uvicorn.access").setLevel(os.getenv("UVICORN_ACCESS_LEVEL", "WARNING"))
    logging.getLogger("uvicorn.error").setLevel(os.getenv("UVICORN_ERROR_LEVEL", "INFO"))


def get_logger(**kwargs: Any) -> structlog.stdlib.BoundLogger:
    logger = structlog.get_logger()
    if kwargs:
        return logger.bind(**kwargs)
    return logger
```

### Middleware pour timing + user_id : `app/middleware/logging.py`

```python
import time
from typing import Callable

from fastapi import Request, Response
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger
from app.middleware.request_id import get_request_id


JWT_SECRET = "CHANGE_ME"  # à mettre dans env
JWT_ALG = "HS256"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.logger = get_logger()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:  # type: ignore[override]
        start = time.perf_counter()

        user_id = self._extract_user_id(request)
        request_id = get_request_id()

        log = self.logger.bind(
            path=request.url.path,
            method=request.method,
            request_id=request_id,
            user_id=user_id,
        )

        try:
            response = await call_next(request)
        except Exception:
            duration = time.perf_counter() - start
            log.exception("unhandled_exception", duration_ms=int(duration * 1000))
            raise

        duration = time.perf_counter() - start
        status_code = response.status_code

        if status_code >= 500:
            log.error("request_failed", status_code=status_code, duration_ms=int(duration * 1000))
        elif status_code >= 400:
            log.warning("client_error", status_code=status_code, duration_ms=int(duration * 1000))
        else:
            log.info("request_succeeded", status_code=status_code, duration_ms=int(duration * 1000))

        return response

    @staticmethod
    def _extract_user_id(request: Request) -> str | None:
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return None
        token = auth.split(" ", 1) [davidmuraya](https://davidmuraya.com/blog/adding-middleware-to-fastapi-applications/)
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        except JWTError:
            return None
        sub = payload.get("sub")
        return str(sub) if sub is not None else None
```

### Ligne à ajouter dans `main.py`

```python
from app.core.logging import configure_logging
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware

configure_logging(json_logs=os.getenv("LOG_JSON", "true").lower() == "true")

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)
```

### Repo GitHub de référence

- Guides structlog + FastAPI (contextvars, JSON logs, prod vs dev).[web:31][web:34][web:42]

### Erreurs courantes à éviter

- Logger des tokens JWT/auth headers en clair (RGPD / sécurité).[web:34]
- Ne pas désactiver/rabaisser `uvicorn.access` → bruit énorme en prod.
- Oublier de binder `request_id` dans les logs d’erreur async (hors middleware HTTP).

### Astuce non évidente

Ajoute un champ `env` / `deployment` dans les logs (via structlog `bind` global) pour pouvoir filtrer finement entre `staging`, `canary`, `prod-blue`, etc. dans ton agrégateur de logs.

---

## 8. Circuit Breaker pour AI Providers

### Fichier : `app/observability/circuit_breaker.py`

```python
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Deque, Dict


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitMetrics:
    failures: int = 0
    last_failure_time: float = 0.0
    state: CircuitState = CircuitState.CLOSED
    opened_at: float = 0.0
    half_open_trial_in_progress: bool = False


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 5
    window_seconds: int = 60
    recovery_timeout: int = 30

    metrics: CircuitMetrics = field(default_factory=CircuitMetrics)
    _failures_window: Deque[float] = field(default_factory=deque, init=False)

    def _prune_window(self, now: float) -> None:
        while self._failures_window and now - self._failures_window > self.window_seconds:
            self._failures_window.popleft()

    def _record_failure(self, now: float) -> None:
        self._failures_window.append(now)
        self._prune_window(now)
        self.metrics.failures = len(self._failures_window)
        self.metrics.last_failure_time = now

        if (
            self.metrics.state == CircuitState.CLOSED
            and self.metrics.failures >= self.failure_threshold
        ):
            self.metrics.state = CircuitState.OPEN
            self.metrics.opened_at = now

    def _record_success(self) -> None:
        self._failures_window.clear()
        self.metrics.failures = 0
        self.metrics.state = CircuitState.CLOSED
        self.metrics.half_open_trial_in_progress = False

    def _can_pass(self, now: float) -> bool:
        if self.metrics.state == CircuitState.CLOSED:
            return True
        if self.metrics.state == CircuitState.OPEN:
            if now - self.metrics.opened_at >= self.recovery_timeout:
                # passe en half-open pour un essai
                self.metrics.state = CircuitState.HALF_OPEN
                self.metrics.half_open_trial_in_progress = False
                return True
            return False
        if self.metrics.state == CircuitState.HALF_OPEN:
            # n’autoriser qu’un seul essai à la fois
            return not self.metrics.half_open_trial_in_progress
        return False

    def _on_half_open_call_start(self) -> None:
        if self.metrics.state == CircuitState.HALF_OPEN:
            self.metrics.half_open_trial_in_progress = True

    def _on_half_open_call_end(self) -> None:
        if self.metrics.state == CircuitState.HALF_OPEN:
            self.metrics.half_open_trial_in_progress = False

    def decorate(self, func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        breaker = self

        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            now = time.monotonic()
            if not breaker._can_pass(now):
                raise RuntimeError(f"Circuit {breaker.name} is OPEN")

            is_half_open_trial = breaker.metrics.state == CircuitState.HALF_OPEN
            if is_half_open_trial:
                breaker._on_half_open_call_start()

            try:
                result = await func(*args, **kwargs)
            except Exception:
                breaker._record_failure(time.monotonic())
                if is_half_open_trial:
                    breaker.metrics.state = CircuitState.OPEN
                    breaker.metrics.opened_at = time.monotonic()
                    breaker._on_half_open_call_end()
                raise
            else:
                breaker._record_success()
                return result

        return wrapper
```

### Fichier : `app/observability/ai_clients.py`

```python
from typing import Any, Dict, List

import httpx

from app.observability.circuit_breaker import CircuitBreaker


# Circuit breakers par provider
CLAUDE_BREAKER = CircuitBreaker("claude", failure_threshold=5, window_seconds=60, recovery_timeout=30)
GEMINI_BREAKER = CircuitBreaker("gemini", failure_threshold=5, window_seconds=60, recovery_timeout=30)
GROQ_BREAKER = CircuitBreaker("groq", failure_threshold=5, window_seconds=60, recovery_timeout=30)


async def _call_claude(payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post("https://api.anthropic.com/v1/messages", json=payload)
        resp.raise_for_status()
        return resp.json()


async def _call_gemini(payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post("https://generativelanguage.googleapis.com/v1beta/models", json=payload)
        resp.raise_for_status()
        return resp.json()


async def _call_groq(payload: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post("https://api.groq.com/openai/v1/chat/completions", json=payload)
        resp.raise_for_status()
        return resp.json()


CALL_CLAUDE = CLAUDE_BREAKER.decorate(_call_claude)
CALL_GEMINI = GEMINI_BREAKER.decorate(_call_gemini)
CALL_GROQ = GROQ_BREAKER.decorate(_call_groq)


async def call_with_fallback(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Appelle les providers avec fallback automatique selon l’état des circuits."""

    providers: List[str] = ["claude", "gemini", "groq"]
    errors: Dict[str, str] = {}

    for name in providers:
        try:
            if name == "claude":
                return await CALL_CLAUDE(payload)
            if name == "gemini":
                return await CALL_GEMINI(payload)
            if name == "groq":
                return await CALL_GROQ(payload)
        except Exception as exc:
            errors[name] = str(exc)
            continue

    raise RuntimeError(f"All AI providers failed: {errors}")
```

### Utilisation dans un endpoint

```python
from fastapi import APIRouter

from app.observability.ai_clients import call_with_fallback


router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat")
async def ai_chat(payload: dict) -> dict:
    return await call_with_fallback(payload)
```

### Ligne à ajouter dans `main.py`

```python
from app.routes.ai import router as ai_router
from app.observability import ai_clients  # force import pour initialiser les breakers

app.include_router(ai_router)
```

### Repo GitHub de référence

- `pybreaker` – implémentation Circuit Breaker en Python utilisée comme inspiration pour les états/paramètres.[web:35][web:43]

### Erreurs courantes à éviter

- Ne pas limiter la fenêtre temporelle des erreurs (compter tous les fails depuis le boot).
- Oublier l’état HALF_OPEN : le circuit reste ouvert indéfiniment.
- Blinder tous les providers avec un même breaker → un seul provider HS mute tous les autres.

### Astuce non évidente

Expose l’état des circuits via un endpoint debug (`/debug/circuits`) ou Prometheus : tu peux déclencher des autoscaling / feature toggles (ex. désactiver un provider côté front) dès que le circuit passe en OPEN.

---

## 9. API Rate Limiting avancé (Sliding Window + Redis)

### Fichier : `app/middleware/rate_limit.py`

```python
import time
from dataclasses import dataclass
from typing import Optional

import redis.asyncio as redis
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


WHITELIST_IPS = {"127.0.0.1"}


@dataclass
class RateLimitStatus:
    allowed: bool
    limit: int
    remaining: int
    reset_after: int
    retry_after: Optional[int]


class RedisSlidingWindowLimiter:
    """Implémentation simple de sliding window en Redis.

    Clé = `prefix:user_id`
    Valeur = timestamps (score) dans un ZSET.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        max_requests: int,
        window_seconds: int,
        burst: int = 0,
        key_prefix: str = "rate:sliding",
    ) -> None:
        self.client = redis_client
        self.max_requests = max_requests
        self.window = window_seconds
        self.burst = burst
        self.key_prefix = key_prefix

    def _key(self, identifier: str) -> str:
        return f"{self.key_prefix}:{identifier}"

    async def check(self, identifier: str) -> RateLimitStatus:
        now = int(time.time())
        window_start = now - self.window
        key = self._key(identifier)

        pipe = self.client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zrange(key, 0, 0, withscores=True)
        pipe.expire(key, self.window)
        removed, current_count, oldest, _ = await pipe.execute()

        limit = self.max_requests
        # Burst = autorise un pic plus court (tokens supplémentaires dans la fenêtre)
        effective_limit = limit + self.burst

        if current_count >= effective_limit:
            # déjà au-dessus, calcul retry
            if oldest:
                oldest_ts = int(oldest)  # type: ignore[index] [davidmuraya](https://davidmuraya.com/blog/adding-middleware-to-fastapi-applications/)
                reset_after = max(1, self.window - (now - oldest_ts))
            else:
                reset_after = self.window

            return RateLimitStatus(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_after=reset_after,
                retry_after=reset_after,
            )

        # Autorisé → on ajoute le hit actuel
        await self.client.zadd(key, {str(now): now})

        new_count = current_count + 1
        remaining = max(limit - new_count, 0)

        # reset_after = quand la fenêtre sera vraiment vide (basé sur le plus vieux event)
        if oldest:
            oldest_ts = int(oldest)  # type: ignore[index] [davidmuraya](https://davidmuraya.com/blog/adding-middleware-to-fastapi-applications/)
            reset_after = max(1, self.window - (now - oldest_ts))
        else:
            reset_after = self.window

        return RateLimitStatus(
            allowed=True,
            limit=limit,
            remaining=remaining,
            reset_after=reset_after,
            retry_after=None,
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        limiter: RedisSlidingWindowLimiter,
    ) -> None:
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        path = request.url.path

        # Bypass health/metrics
        if path.startswith("/health") or path.startswith("/metrics"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        if client_ip in WHITELIST_IPS:
            return await call_next(request)

        identifier = request.headers.get("X-User-ID") or client_ip

        status_ = await self.limiter.check(identifier)

        if not status_.allowed:
            headers = {
                "X-RateLimit-Limit": str(status_.limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(status_.reset_after),
            }
            if status_.retry_after is not None:
                headers["Retry-After"] = str(status_.retry_after)

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too Many Requests",
                    "retry_after": status_.retry_after,
                },
                headers=headers,
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(status_.limit)
        response.headers["X-RateLimit-Remaining"] = str(status_.remaining)
        response.headers["X-RateLimit-Reset"] = str(status_.reset_after)
        return response
```

### Init Redis + middleware dans `main.py`

```python
import os

import redis.asyncio as redis

from app.middleware.rate_limit import RateLimitMiddleware, RedisSlidingWindowLimiter


redis_client: redis.Redis | None = None


@app.on_event("startup")
async def on_startup_rate_limit() -> None:
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    limiter = RedisSlidingWindowLimiter(
        redis_client=redis_client,
        max_requests=int(os.getenv("RATE_LIMIT_PER_MINUTE", "100")),
        window_seconds=60,
        burst=int(os.getenv("RATE_LIMIT_BURST", "20")),
    )

    app.add_middleware(RateLimitMiddleware, limiter=limiter)
```

### Repo GitHub de référence

- Articles + exemples complets de sliding window Redis + FastAPI.[web:33][web:36][web:39]

### Erreurs courantes à éviter

- Utiliser un fixed window pur (effet « bursty » sur les frontières de fenêtres).[web:33]
- Oublier les headers `X-RateLimit-*` et `Retry-After` (le client ne sait pas quand retenter).[web:39]
- Stocker des JSON volumineux par clé dans Redis plutôt que des timestamps compacts.

### Astuce non évidente

Expose un endpoint interne `/debug/rate-limit/{id}` qui lit directement le `ZCARD` + `ZRANGE` pour un user donné : débugger des faux positifs de 429 devient trivial.

---

## 10. Dockerfile multi‑stage optimisé

### Fichier : `Dockerfile`

```dockerfile
# ======= BUILDER =======
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier uniquement les fichiers de dépendances
COPY pyproject.toml poetry.lock* requirements.txt* ./

# Installer deps dans un dossier dédié
RUN python -m venv /venv \
    && /venv/bin/pip install --upgrade pip \
    && if [ -f "requirements.txt" ]; then /venv/bin/pip install -r requirements.txt; fi \
    && if [ -f "pyproject.toml" ]; then /venv/bin/pip install .; fi

# ======= RUNTIME =======
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/venv/bin:$PATH"

# User non-root
RUN useradd -m appuser

WORKDIR /app

# Copier l’environnement virtuel depuis le builder
COPY --from=builder /venv /venv

# Copier uniquement le code nécessaire
COPY app ./app
COPY main.py ./main.py

# Ports
EXPOSE 8000

# Labels OCI
LABEL org.opencontainers.image.title="ai-saas-fastapi" \
      org.opencontainers.image.description="Enterprise-grade FastAPI AI SaaS" \
      org.opencontainers.image.source="https://example.com/repo" \
      org.opencontainers.image.licenses="MIT"

# Santé
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD \
  python - << 'EOF'
import sys
import urllib.request

try:
    with urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=3) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
EOF

# Signal d'arrêt
STOPSIGNAL SIGTERM

# Changer d'utilisateur
USER appuser

# Commande (Gunicorn + Uvicorn workers recommandé en prod)
CMD [
  "gunicorn",
  "main:app",
  "-k", "uvicorn.workers.UvicornWorker",
  "-b", "0.0.0.0:8000",
  "--workers", "4",
  "--timeout", "60"
]
```

### Fichier : `.dockerignore`

```dockerignore
__pycache__
*.py[cod]
*.log
.env
.git
.gitignore
.idea
.vscode
.mypy_cache
.pytest_cache
.tox
.dist
build
dist
*.egg-info
.DS_Store
node_modules
coverage*
htmlcov

# Docs
/site
/docs/_build

# Venv locaux
.venv
venv

# Docker
Dockerfile*
```

### Repo GitHub de référence

- Dockerfiles prod FastAPI multi‑stage + Gunicorn/Uvicorn + HEALTHCHECK + user non‑root.[web:45][web:48][web:51][web:57]

### Erreurs courantes à éviter

- Utiliser une image `python:3.13` pleine (non‑slim) → image > 1.5 Go.[web:57]
- Lancer Uvicorn direct en prod au lieu de Gunicorn (gestion workers / reload / signaux moins robuste).[web:51]
- Oublier `HEALTHCHECK` → orchestrateur considère le conteneur « healthy » même si l’app est KO.

### Astuce non évidente

Si tu ajoutes un front ou des assets volumineux, crée un troisième stage `assets` pour les builder (npm) puis ne copier que les fichiers statiques finaux dans `runtime` → gros gain sur la taille de l’image.

---

## 11. OpenTelemetry Integration

### Fichier : `app/core/opentelemetry.py`

```python
import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor


def setup_tracing(app: FastAPI) -> None:
    service_name = os.getenv("SERVICE_NAME", "ai-saas-fastapi")
    env = os.getenv("ENV", "local")

    resource = Resource.create({
        "service.name": service_name,
        "service.namespace": "ai-saas",
        "deployment.environment": env,
    })

    tracer_provider = TracerProvider(resource=resource)

    if env == "local":
        tracer_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        endpoint = os.getenv("OTLP_ENDPOINT", "http://otel-collector:4317")
        otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    trace.set_tracer_provider(tracer_provider)

    # FastAPI HTTP server spans
    FastAPIInstrumentor.instrument_app(app)

    # asyncpg, Redis, httpx
    AsyncPGInstrumentor().instrument()
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
```

### Corrélation avec structlog (trace_id dans les logs)

Déjà intégré dans `_add_trace_context` dans `app/core/logging.py`.

### Ligne à ajouter dans `main.py`

```python
from app.core.opentelemetry import setup_tracing

setup_tracing(app)
```

### Repo GitHub / docs de référence

- Docs officielles OpenTelemetry FastAPI instrumentation.[web:46][web:55]
- Guides d’intégration FastAPI + OTLP collector / Uptrace / Last9.[web:49][web:52][web:58]

### Erreurs courantes à éviter

- Instrumenter FastAPI avant d’avoir configuré le `TracerProvider` (tu perds des spans).[web:46]
- Oublier d’exclure les endpoints `/health` et `/metrics` des traces (bruit énorme).
- Configurer un `BatchSpanProcessor` en local → debugging plus compliqué (buffering).

### Astuce non évidente

Utilise les hooks `request_hook` / `response_hook` (FastAPIInstrumentor) pour binder `user_id` / `request_id` en attributs de span : tu peux alors filtrer dans ton APM exactement comme dans tes logs structlog.

---

## 12. Error Tracking (Sentry‑like)

### Exemple avec Sentry / GlitchTip (self‑hosté)

### Fichier : `app/observability/errors.py`

```python
import os

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.middleware.request_id import get_request_id


def init_error_tracking(app: FastAPI) -> None:
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return

    env = os.getenv("ENV", "local")

    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        send_default_pii=True,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
    )

    @app.exception_handler(Exception)
    async def sentry_exception_handler(request: Request, exc: Exception):  # type: ignore[override]
        # Laisse passer les HTTPException 4xx telles quelles
        if isinstance(exc, HTTPException) and exc.status_code < 500:
            raise exc

        with sentry_sdk.push_scope() as scope:
            scope.set_tag("path", request.url.path)
            scope.set_tag("method", request.method)
            endpoint = request.scope.get("endpoint")
            scope.set_tag("module", endpoint.__module__ if endpoint else "unknown")

            rid = get_request_id()
            if rid:
                scope.set_tag("request_id", rid)

            # user_id depuis un middleware / dependency (state.user)
            user = getattr(request.state, "user", None)
            if user and getattr(user, "id", None):
                scope.set_user({"id": str(user.id)})

            sentry_sdk.capture_exception(exc)

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
                "request_id": get_request_id(),
            },
        )
```

> Remarque : GlitchTip est compatible Sentry API, le `dsn` pointera simplement vers ton instance self‑hostée.[web:56]

### Ligne à ajouter dans `main.py`

```python
from app.observability.errors import init_error_tracking

init_error_tracking(app)
```

### Repo / docs de référence

- Intégration officielle Sentry Python + FastAPI.[web:47][web:50][web:53]
- GlitchTip (compatible Sentry, open‑source) pour self‑hosting.[web:56]

### Erreurs courantes à éviter

- Capturer toutes les exceptions y compris les `HTTPException` 4xx volontaires → bruit massif.[web:50]
- Oublier de renseigner `environment` (`staging`, `prod`) dans Sentry → difficile de filtrer.
- Logger les mêmes erreurs côté logs + Sentry en boucle (boucles de notifications).

### Astuce non évidente

Utilise des fingerprints custom (Sentry) pour grouper intelligemment les erreurs métier (ex. par code de business error) plutôt que par stacktrace pure : tu y vois plus clair sur ce qui impacte vraiment les users.

---
```