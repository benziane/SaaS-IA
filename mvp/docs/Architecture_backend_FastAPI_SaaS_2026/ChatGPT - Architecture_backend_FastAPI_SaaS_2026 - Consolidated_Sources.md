# Architecture backend FastAPI SaaS - Consolidated Sources (2026)

Ce document consolide en un seul fichier les sources presentes dans `Architecture_backend_FastAPI_SaaS_2026`.
Les fichiers originaux sont laisses intacts.

## Sources incluses

- ChatGPT - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md
- Claude - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md
- Ethy - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md
- Gemini - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md
- Perplexity - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md
- ithy-article-fastapi-saas-architecture-s-plus-plus-plus-yr3917x2v5.html

## Contenu consolide

---

## Source: ChatGPT - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md

Chemin d'origine: `C:\Users\ibzpc\Git\SaaS-IA\mvp\docs\Architecture_backend_FastAPI_SaaS_2026\ChatGPT - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md`

Voici un **fichier `.md` structuré, production-ready, sans pseudo-code**, avec un niveau S+++ (industrial-grade).
Je ne traite ici que **#1 → #4** (sinon la réponse devient illisible et inutilisable).
Dis-moi “continue” pour #5 → #12.

---

# 📦 ENTERPRISE FASTAPI HARDENING — PART 1 (S+++)

---

# 1. Security Headers Middleware

### 📁 `app/middleware/security_headers.py`

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

        self.headers = {
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
            "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        for key, value in self.headers.items():
            response.headers.setdefault(key, value)

        # Cache-Control uniquement pour API
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store, max-age=0"

        return response
```

### 📌 `main.py`

```python
from app.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

### 📚 Repo référence

* fastapi (⭐ 80k+, actif 2025)
* fastapi-middlewares → implémentation OWASP headers ([GitHub][1])

### ⚠️ erreurs critiques

* CSP trop permissive (`*`) → inutile
* oublier HSTS → downgrade HTTPS possible
* casser Swagger UI avec CSP trop strict

### 💡 astuce non évidente

➡️ **Versionner ta CSP par environnement** (dev vs prod), sinon tu bloques ton frontend.

---

# 2. Request ID / Correlation ID

## 📁 `app/core/request_context.py`

```python
import uuid
import contextvars

request_id_ctx = contextvars.ContextVar("request_id", default=None)
user_id_ctx = contextvars.ContextVar("user_id", default=None)


def get_request_id():
    return request_id_ctx.get()


def set_request_id(request_id: str):
    request_id_ctx.set(request_id)
```

---

## 📁 `app/middleware/request_id.py`

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid

from app.core.request_context import set_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    HEADER_NAME = "X-Request-ID"

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.HEADER_NAME)

        if not request_id:
            request_id = str(uuid.uuid4())

        set_request_id(request_id)

        response: Response = await call_next(request)
        response.headers[self.HEADER_NAME] = request_id

        return response
```

---

## 📁 `app/core/logging.py`

```python
import structlog
from app.core.request_context import get_request_id

def add_request_id(logger, method_name, event_dict):
    event_dict["request_id"] = get_request_id()
    return event_dict


structlog.configure(
    processors=[
        add_request_id,
        structlog.processors.JSONRenderer(),
    ]
)
```

---

## 📁 propagation Celery

```python
# task.py
from celery import Task
from app.core.request_context import get_request_id

class ContextTask(Task):
    def apply_async(self, args=None, kwargs=None, **options):
        headers = options.setdefault("headers", {})
        headers["X-Request-ID"] = get_request_id()
        return super().apply_async(args, kwargs, **options)
```

---

### 📌 `main.py`

```python
app.add_middleware(RequestIDMiddleware)
```

---

### 📚 Repo référence

* fastapi-middlewares (Request ID impl) ([GitHub][1])

---

### ⚠️ erreurs critiques

* utiliser `threading.local()` → cassé en async
* ne pas propager dans Celery → perte de traçabilité
* générer plusieurs IDs par requête

---

### 💡 astuce

➡️ **Toujours propager Request-ID dans tes appels HTTP sortants (httpx)**
sinon ton tracing distribué est inutile.

---

# 3. Compression Gzip + Brotli

## 📁 `app/middleware/compression.py`

```python
from starlette.middleware.gzip import GZipMiddleware
from fastapi import Request


EXCLUDED_PATHS = {"/metrics"}


class SmartGZipMiddleware(GZipMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # SSE exclusion
        if request.headers.get("accept") == "text/event-stream":
            return await call_next(request)

        return await super().dispatch(request, call_next)
```

---

### 📌 `main.py`

```python
from app.middleware.compression import SmartGZipMiddleware

app.add_middleware(SmartGZipMiddleware, minimum_size=500)
```

---

### Brotli (optionnel)

```bash
pip install brotli
```

FastAPI/Starlette utilisera automatiquement Brotli si dispo.

---

### 📚 Repo référence

* fastapi (GZipMiddleware officiel)

---

### ⚠️ erreurs critiques

* compresser SSE → casse streaming
* compresser /metrics → inutile (Prometheus déjà compressé)
* seuil trop bas → overhead CPU

---

### 💡 astuce

➡️ **500 bytes = sweet spot réel prod** (en dessous → perte CPU)

---

# 4. Graceful Shutdown (FastAPI + Celery + asyncpg)

## 📁 `app/core/lifespan.py`

```python
import asyncio
import signal
from contextlib import asynccontextmanager

shutdown_event = asyncio.Event()


def setup_signal_handlers():
    def handler():
        shutdown_event.set()

    signal.signal(signal.SIGTERM, lambda s, f: handler())
    signal.signal(signal.SIGINT, lambda s, f: handler())


@asynccontextmanager
async def lifespan(app):
    setup_signal_handlers()

    yield

    # WAIT graceful shutdown
    try:
        await asyncio.wait_for(shutdown_event.wait(), timeout=30)
    except asyncio.TimeoutError:
        pass

    # close DB pool
    if hasattr(app.state, "db"):
        await app.state.db.dispose()
```

---

## 📁 `main.py`

```python
from fastapi import FastAPI
from app.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)
```

---

## Celery worker config

```bash
celery -A app.worker worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=100 \
  --graceful-timeout=30
```

---

## Dockerfile

```dockerfile
STOPSIGNAL SIGTERM
```

---

## docker-compose.yml

```yaml
services:
  api:
    stop_grace_period: 30s
```

---

### 📚 Repo référence

* fastapi (lifespan pattern officiel)

---

### ⚠️ erreurs critiques

* shutdown immédiat → perte requêtes
* oublier pool DB close → fuite connexions
* Celery SIGKILL → tasks corrompues

---

### 💡 astuce critique

➡️ **toujours coupler graceful shutdown avec readiness probe**
→ sinon Kubernetes envoie encore du trafic

---

# 🔴 ANALYSE CRITIQUE (important)

Ton architecture actuelle :

* déjà bonne (middleware + structlog + metrics)
* MAIS il manque 3 choses critiques enterprise :

1. **correlation distribuée (trace_id + request_id)**
2. **graceful shutdown réel (pas juste FastAPI stop)**
3. **CSP + headers stricts (actuellement souvent mal faits)**

👉 Sans ça, ton système n’est pas S+++ (juste S+).

---

# 👉 SUITE

Réponds **“continue”** et je t’envoie :

* #5 Health checks K8s (production-grade réel)
* #6 DB pooling asyncpg optimisé (critique perf)
* #7 Structlog enterprise complet
* #8 Circuit breaker IA (clé pour ton use case)
* #9 Rate limiting avancé Redis
* #10 Docker multi-stage <500MB
* #11 OpenTelemetry (distributed tracing réel)
* #12 Error tracking (Sentry-like open source)

---

[1]: https://github.com/mahdijafaridev/fastapi-middlewares?utm_source=chatgpt.com "mahdijafaridev/fastapi-middlewares"
Voici un **fichier `.md` structuré, production-ready, sans pseudo-code**, avec un niveau S+++ (industrial-grade).
Je ne traite ici que **#1 → #4** (sinon la réponse devient illisible et inutilisable).
Dis-moi “continue” pour #5 → #12.

---

# 📦 ENTERPRISE FASTAPI HARDENING — PART 1 (S+++)

---

# 1. Security Headers Middleware

### 📁 `app/middleware/security_headers.py`

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

        self.headers = {
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
            "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        for key, value in self.headers.items():
            response.headers.setdefault(key, value)

        # Cache-Control uniquement pour API
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-store, max-age=0"

        return response
```

### 📌 `main.py`

```python
from app.middleware.security_headers import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

### 📚 Repo référence

* fastapi (⭐ 80k+, actif 2025)
* fastapi-middlewares → implémentation OWASP headers ([GitHub][1])

### ⚠️ erreurs critiques

* CSP trop permissive (`*`) → inutile
* oublier HSTS → downgrade HTTPS possible
* casser Swagger UI avec CSP trop strict

### 💡 astuce non évidente

➡️ **Versionner ta CSP par environnement** (dev vs prod), sinon tu bloques ton frontend.

---

# 2. Request ID / Correlation ID

## 📁 `app/core/request_context.py`

```python
import uuid
import contextvars

request_id_ctx = contextvars.ContextVar("request_id", default=None)
user_id_ctx = contextvars.ContextVar("user_id", default=None)


def get_request_id():
    return request_id_ctx.get()


def set_request_id(request_id: str):
    request_id_ctx.set(request_id)
```

---

## 📁 `app/middleware/request_id.py`

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid

from app.core.request_context import set_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    HEADER_NAME = "X-Request-ID"

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.HEADER_NAME)

        if not request_id:
            request_id = str(uuid.uuid4())

        set_request_id(request_id)

        response: Response = await call_next(request)
        response.headers[self.HEADER_NAME] = request_id

        return response
```

---

## 📁 `app/core/logging.py`

```python
import structlog
from app.core.request_context import get_request_id

def add_request_id(logger, method_name, event_dict):
    event_dict["request_id"] = get_request_id()
    return event_dict


structlog.configure(
    processors=[
        add_request_id,
        structlog.processors.JSONRenderer(),
    ]
)
```

---

## 📁 propagation Celery

```python
# task.py
from celery import Task
from app.core.request_context import get_request_id

class ContextTask(Task):
    def apply_async(self, args=None, kwargs=None, **options):
        headers = options.setdefault("headers", {})
        headers["X-Request-ID"] = get_request_id()
        return super().apply_async(args, kwargs, **options)
```

---

### 📌 `main.py`

```python
app.add_middleware(RequestIDMiddleware)
```

---

### 📚 Repo référence

* fastapi-middlewares (Request ID impl) ([GitHub][1])

---

### ⚠️ erreurs critiques

* utiliser `threading.local()` → cassé en async
* ne pas propager dans Celery → perte de traçabilité
* générer plusieurs IDs par requête

---

### 💡 astuce

➡️ **Toujours propager Request-ID dans tes appels HTTP sortants (httpx)**
sinon ton tracing distribué est inutile.

---

# 3. Compression Gzip + Brotli

## 📁 `app/middleware/compression.py`

```python
from starlette.middleware.gzip import GZipMiddleware
from fastapi import Request


EXCLUDED_PATHS = {"/metrics"}


class SmartGZipMiddleware(GZipMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # SSE exclusion
        if request.headers.get("accept") == "text/event-stream":
            return await call_next(request)

        return await super().dispatch(request, call_next)
```

---

### 📌 `main.py`

```python
from app.middleware.compression import SmartGZipMiddleware

app.add_middleware(SmartGZipMiddleware, minimum_size=500)
```

---

### Brotli (optionnel)

```bash
pip install brotli
```

FastAPI/Starlette utilisera automatiquement Brotli si dispo.

---

### 📚 Repo référence

* fastapi (GZipMiddleware officiel)

---

### ⚠️ erreurs critiques

* compresser SSE → casse streaming
* compresser /metrics → inutile (Prometheus déjà compressé)
* seuil trop bas → overhead CPU

---

### 💡 astuce

➡️ **500 bytes = sweet spot réel prod** (en dessous → perte CPU)

---

# 4. Graceful Shutdown (FastAPI + Celery + asyncpg)

## 📁 `app/core/lifespan.py`

```python
import asyncio
import signal
from contextlib import asynccontextmanager

shutdown_event = asyncio.Event()


def setup_signal_handlers():
    def handler():
        shutdown_event.set()

    signal.signal(signal.SIGTERM, lambda s, f: handler())
    signal.signal(signal.SIGINT, lambda s, f: handler())


@asynccontextmanager
async def lifespan(app):
    setup_signal_handlers()

    yield

    # WAIT graceful shutdown
    try:
        await asyncio.wait_for(shutdown_event.wait(), timeout=30)
    except asyncio.TimeoutError:
        pass

    # close DB pool
    if hasattr(app.state, "db"):
        await app.state.db.dispose()
```

---

## 📁 `main.py`

```python
from fastapi import FastAPI
from app.core.lifespan import lifespan

app = FastAPI(lifespan=lifespan)
```

---

## Celery worker config

```bash
celery -A app.worker worker \
  --loglevel=info \
  --concurrency=4 \
  --max-tasks-per-child=100 \
  --graceful-timeout=30
```

---

## Dockerfile

```dockerfile
STOPSIGNAL SIGTERM
```

---

## docker-compose.yml

```yaml
services:
  api:
    stop_grace_period: 30s
```

---

### 📚 Repo référence

* fastapi (lifespan pattern officiel)

---

### ⚠️ erreurs critiques

* shutdown immédiat → perte requêtes
* oublier pool DB close → fuite connexions
* Celery SIGKILL → tasks corrompues

---

### 💡 astuce critique

➡️ **toujours coupler graceful shutdown avec readiness probe**
→ sinon Kubernetes envoie encore du trafic

---

# 🔴 ANALYSE CRITIQUE (important)

Ton architecture actuelle :

* déjà bonne (middleware + structlog + metrics)
* MAIS il manque 3 choses critiques enterprise :

1. **correlation distribuée (trace_id + request_id)**
2. **graceful shutdown réel (pas juste FastAPI stop)**
3. **CSP + headers stricts (actuellement souvent mal faits)**

👉 Sans ça, ton système n’est pas S+++ (juste S+).

---

# 👉 SUITE

Réponds **“continue”** et je t’envoie :

* #5 Health checks K8s (production-grade réel)
* #6 DB pooling asyncpg optimisé (critique perf)
* #7 Structlog enterprise complet
* #8 Circuit breaker IA (clé pour ton use case)
* #9 Rate limiting avancé Redis
* #10 Docker multi-stage <500MB
* #11 OpenTelemetry (distributed tracing réel)
* #12 Error tracking (Sentry-like open source)

---

[1]: https://github.com/mahdijafaridev/fastapi-middlewares?utm_source=chatgpt.com "mahdijafaridev/fastapi-middlewares"


Parfait. On passe au **niveau réellement enterprise (S+++)** — là où 90% des stacks FastAPI échouent en prod.

Je te donne **#5 → #12 complets, production-ready**, sans bullshit.

---

# 📦 ENTERPRISE FASTAPI HARDENING — PART 2 (S+++)

---

# 5. Health Checks Kubernetes-Ready

## 📁 `app/api/health.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncEngine
import redis.asyncio as redis

router = APIRouter(prefix="/health", tags=["health"])


async def check_db(engine: AsyncEngine):
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False


async def check_redis(r: redis.Redis):
    try:
        await r.ping()
        return True
    except Exception:
        return False


@router.get("/live")
async def liveness():
    return {"status": "alive"}


@router.get("/ready")
async def readiness(engine: AsyncEngine = Depends(lambda: router.state.db),
                    r: redis.Redis = Depends(lambda: router.state.redis)):
    db_ok = await check_db(engine)
    redis_ok = await check_redis(r)

    status = db_ok and redis_ok

    return {
        "status": "ready" if status else "not_ready",
        "db": db_ok,
        "redis": redis_ok,
    }


@router.get("/startup")
async def startup_check():
    # vérifie modules chargés
    from app.core.module_loader import registry

    return {
        "status": "started",
        "modules_loaded": len(registry),
    }
```

---

## 📌 `main.py`

```python
from app.api.health import router as health_router

app.include_router(health_router)
```

---

## 📁 Kubernetes probes

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 10

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  periodSeconds: 5

startupProbe:
  httpGet:
    path: /health/startup
    port: 8000
  failureThreshold: 30
```

---

### ⚠️ erreurs

* readiness = simple 200 → faux (doit tester DB)
* liveness trop complexe → redémarrage inutile
* pas de startup probe → crash loops

---

### 💡 astuce

➡️ **séparer strictement les 3 probes**
= base de la stabilité Kubernetes

---

# 6. Database Pooling (asyncpg + SQLAlchemy)

## 📁 `app/core/db.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
import asyncio
import time

DATABASE_URL = "postgresql+asyncpg://user:pass@db:5432/app"


def create_engine():
    return create_async_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False,
    )


async def with_retry(fn, retries=5, delay=1):
    for i in range(retries):
        try:
            return await fn()
        except Exception:
            if i == retries - 1:
                raise
            await asyncio.sleep(delay * (2 ** i))
```

---

## metrics pool

```python
from prometheus_client import Gauge

db_pool_size = Gauge("db_pool_size", "Total connections")
db_pool_checked_out = Gauge("db_pool_checked_out", "Active connections")


def track_pool(engine):
    pool = engine.pool
    db_pool_size.set(pool.size())
    db_pool_checked_out.set(pool.checkedout())
```

---

### ⚠️ erreurs critiques

* pool_size trop grand → saturation DB
* pas de pre_ping → connexions mortes
* pas de retry → crash transient

---

### 💡 astuce

➡️ **pool_size = (CPU * 2) + IO factor**
pas une valeur random

---

# 7. Structured Logging Enterprise (structlog)

## 📁 `app/core/logging.py`

```python
import logging
import sys
import structlog
from app.core.request_context import get_request_id, user_id_ctx


def add_context(logger, method_name, event_dict):
    event_dict["request_id"] = get_request_id()
    event_dict["user_id"] = user_id_ctx.get()
    return event_dict


def remove_sensitive(logger, method_name, event_dict):
    for key in ["password", "token", "authorization"]:
        if key in event_dict:
            event_dict[key] = "***REDACTED***"
    return event_dict


def setup_logging(json_logs=True):
    processors = [
        structlog.contextvars.merge_contextvars,
        add_context,
        remove_sensitive,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
```

---

## middleware timing

```python
import time
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        logger = structlog.get_logger()
        logger.info(
            "request",
            path=request.url.path,
            method=request.method,
            status=response.status_code,
            duration=duration,
        )

        return response
```

---

### 📚 repo solide

* [asgi-correlation-id GitHub](https://github.com/snok/asgi-correlation-id?utm_source=chatgpt.com) → standard correlation ID middleware ([GitHub][1])
* structlog production patterns (guides) ([dash0.com][2])

---

### ⚠️ erreurs

* logs texte → inutilisable
* pas de request_id → debugging impossible
* log des tokens → fail sécurité

---

### 💡 astuce critique

➡️ **structlog + contextvars = standard moderne** ([Gist][3])

---

# 8. Circuit Breaker (AI Providers)

## 📁 `app/core/circuit_breaker.py`

```python
import time


class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_time=60):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time

        self.failures = 0
        self.state = "CLOSED"
        self.last_failure_time = None

    def call(self, fn, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_time:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit open")

        try:
            result = fn(*args, **kwargs)
            self.reset()
            return result

        except Exception:
            self.record_failure()
            raise

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"

    def reset(self):
        self.failures = 0
        self.state = "CLOSED"
```

---

### fallback multi-provider

```python
def call_with_fallback(providers, prompt):
    for provider in providers:
        try:
            return provider.generate(prompt)
        except Exception:
            continue
    raise Exception("All providers failed")
```

---

### ⚠️ erreurs

* pas de circuit breaker → cascade failure
* pas de fallback → downtime complet

---

### 💡 astuce critique

➡️ **indispensable pour ton use-case IA multi-provider**

---

# 9. Rate Limiting avancé (Sliding Window)

## 📁 `app/core/rate_limit.py`

```python
import time
import redis.asyncio as redis

r = redis.Redis()


async def is_allowed(key, limit, window):
    now = time.time()

    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window)

    _, _, count, _ = await pipe.execute()

    return count <= limit, count
```

---

## headers

```python
def rate_headers(limit, remaining, reset):
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset),
    }
```

---

### ⚠️ erreurs

* fixed window → burst unfair
* pas de headers → opaque
* pas de Redis → pas scalable

---

### 💡 astuce

➡️ sliding window = comportement “réel utilisateur”

---

# 10. Dockerfile Multi-Stage

## 📁 `Dockerfile`

```dockerfile
# Stage 1
FROM python:3.13-slim AS builder

WORKDIR /app
COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2
FROM python:3.13-slim

LABEL org.opencontainers.image.source="your-repo"
LABEL org.opencontainers.image.description="FastAPI SaaS"

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

RUN adduser --disabled-password appuser
USER appuser

EXPOSE 8000

HEALTHCHECK CMD curl -f http://localhost:8000/health/live || exit 1

STOPSIGNAL SIGTERM

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📁 `.dockerignore`

```
__pycache__
*.pyc
.env
.git
node_modules
tests
```

---

### ⚠️ erreurs

* image 1.5GB → mauvais layering
* root user → fail sécurité
* pas de healthcheck

---

### 💡 astuce

➡️ multi-stage = -70% taille image

---

# 11. OpenTelemetry (FULL STACK)

## 📁 `app/core/otel.py`

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def setup_otel(app):
    provider = TracerProvider()
    trace.set_tracer_provider(provider)

    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    FastAPIInstrumentor.instrument_app(app)
    AsyncPGInstrumentor().instrument()
    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
```

---

### ⚠️ erreurs

* pas de tracing → debugging impossible
* pas de correlation logs → perte valeur

---

### 💡 astuce

➡️ injecter trace_id dans structlog = S+++ observabilité

---

# 12. Error Tracking (Sentry / GlitchTip)

## 📁 `app/core/errors.py`

```python
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware


def setup_sentry(app):
    sentry_sdk.init(
        dsn="http://localhost:9000",
        traces_sample_rate=1.0,
    )

    app.add_middleware(SentryAsgiMiddleware)
```

---

### enrich context

```python
import sentry_sdk
from app.core.request_context import get_request_id


def before_send(event, hint):
    event["request_id"] = get_request_id()
    return event
```

---

### ⚠️ erreurs

* logs sans error tracking → aveugle
* pas de grouping → spam incidents

---

### 💡 astuce critique

➡️ GlitchTip = Sentry open-source (0€)

---

# 🔴 ANALYSE FINALE (TRÈS IMPORTANTE)

Tu voulais S+++.

Voici la vérité :

👉 Avec ces 12 blocs →
tu passes de **FastAPI “propre” → plateforme enterprise réelle**

Mais ton vrai gap n’est PAS technique.

### Ton vrai problème potentiel :

* pas de **distributed tracing complet**
* pas de **control plane observability**
* pas de **event-driven audit logs**

👉 donc ton système reste “monolith observé”, pas “platform-grade”.

---

# 👉 NEXT STEP (si tu veux aller encore plus loin)

Je peux te donner :

* Event-driven observability (Kafka / NATS)
* Audit log immuable (compliance-grade)
* Multi-tenant isolation HARD (RLS + JWT binding)
* Control plane vs data plane split (niveau Stripe / OpenAI)

---

Si tu veux aller au niveau **architecture FAANG / hyperscaler**, dis :

👉 **“niveau S++++”**

[1]: https://github.com/snok/asgi-correlation-id?utm_source=chatgpt.com "snok/asgi-correlation-id: Request ID propagation for ..."
[2]: https://www.dash0.com/guides/python-logging-with-structlog?utm_source=chatgpt.com "Leveling Up Your Python Logs with Structlog"
[3]: https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e?utm_source=chatgpt.com "Logging setup for FastAPI, Uvicorn and Structlog (with ..."




Parfait. Là tu touches au **vrai niveau hyperscaler / FAANG**.
Je vais être direct : ce que tu demandes n’est **plus du “FastAPI architecture”**, c’est du **platform engineering**.

Je te donne un **blueprint exécutable + code minimal viable**, mais surtout **les invariants** (ce que 95% des équipes ratent).

---

# 🧠 0. CONTEXTE — vérité brutale

Si tu implémentes ces 4 blocs correctement, ton système :

* devient **event-driven (non bloquant, scalable)**
* devient **audit-compliant (finance-grade)**
* devient **multi-tenant sécurisé (isolation réelle)**
* devient **plateforme (pas juste API)**

👉 Sinon → tu restes un backend SaaS classique.

---

# 1. Event-Driven Observability (Kafka / NATS)

## 🔴 Principe clé

> Tout devient un événement (logs, metrics, state change)

Pourquoi :

* découplage total des services ([Growin][1])
* résilience (buffer + retry) ([Growin][1])
* observabilité réelle distribuée

---

## 🏗 Architecture cible

```
[FastAPI] → [Outbox Table] → [Dispatcher]
                          → [NATS / Kafka]
                          → [Consumers]
                               ├─ Logging Service
                               ├─ Metrics Aggregator
                               ├─ Audit Service
                               └─ AI Monitoring
```

👉 Pattern obligatoire : **Transactional Outbox**

---

## 📁 `app/core/events.py`

```python
from pydantic import BaseModel
from datetime import datetime
import uuid

class Event(BaseModel):
    id: str
    type: str
    payload: dict
    timestamp: datetime
    tenant_id: str

    @staticmethod
    def create(event_type: str, payload: dict, tenant_id: str):
        return Event(
            id=str(uuid.uuid4()),
            type=event_type,
            payload=payload,
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
        )
```

---

## 📁 `app/core/outbox.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.events import Event
from sqlalchemy import text
import json

async def save_event(session: AsyncSession, event: Event):
    await session.execute(
        text("""
        INSERT INTO outbox (id, type, payload, tenant_id, created_at)
        VALUES (:id, :type, :payload, :tenant_id, :created_at)
        """),
        {
            "id": event.id,
            "type": event.type,
            "payload": json.dumps(event.payload),
            "tenant_id": event.tenant_id,
            "created_at": event.timestamp,
        },
    )
```

---

## 📁 dispatcher NATS

```python
import asyncio
import nats
from sqlalchemy import text

async def dispatcher_loop(engine):
    nc = await nats.connect("nats://localhost:4222")

    while True:
        async with engine.begin() as conn:
            rows = await conn.execute(text("SELECT * FROM outbox LIMIT 100"))

            for row in rows:
                await nc.publish(
                    f"events.{row.type}",
                    row.payload.encode()
                )

                await conn.execute(
                    text("DELETE FROM outbox WHERE id = :id"),
                    {"id": row.id}
                )

        await asyncio.sleep(0.5)
```

---

## ⚠️ erreurs critiques

* publier directement dans Kafka → perte garantie (race condition DB)
* pas d’idempotency → duplication
* pas de partitioning → scalabilité morte

---

## 💡 insight clé

👉 Kafka = analytics / persistence
👉 NATS = realtime / microservices

👉 **Tu dois utiliser les deux dans une vraie plateforme**

---

# 2. Audit Log immuable (compliance-grade)

## 🔴 Principe

> Rien ne se modifie. Tout s’ajoute.

Inspiré :

* Stripe ledger
* systèmes bancaires

---

## 📁 schema SQL

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY,
    tenant_id TEXT,
    actor_id TEXT,
    action TEXT,
    entity TEXT,
    entity_id TEXT,
    payload JSONB,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## 📁 `app/core/audit.py`

```python
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

async def audit_log(
    session: AsyncSession,
    tenant_id: str,
    actor_id: str,
    action: str,
    entity: str,
    entity_id: str,
    payload: dict,
):
    await session.execute(
        """
        INSERT INTO audit_log (
            id, tenant_id, actor_id, action, entity, entity_id, payload
        )
        VALUES (:id, :tenant_id, :actor_id, :action, :entity, :entity_id, :payload)
        """,
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "actor_id": actor_id,
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "payload": payload,
        },
    )
```

---

## 🔴 règle absolue

❌ UPDATE interdit
❌ DELETE interdit

---

## 💡 niveau S+++

* hash chain (blockchain-like)
* signature cryptographique
* export immutable (S3 + versioning)

---

# 3. Multi-Tenant HARD (RLS + JWT binding)

## 🔴 Principe

> Isolation au niveau DB, pas au niveau code

---

## 📁 PostgreSQL RLS

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON users
USING (tenant_id = current_setting('app.tenant_id')::text);
```

---

## 📁 middleware tenant binding

```python
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID")

        async with request.app.state.db.begin() as conn:
            await conn.execute(
                f"SET app.tenant_id = '{tenant_id}'"
            )

        response = await call_next(request)
        return response
```

---

## 🔴 JWT binding

```python
def extract_tenant(jwt_payload):
    return jwt_payload["tenant_id"]
```

---

## ⚠️ erreurs critiques

* filtrer tenant dans Python → FAIL sécurité
* oublier RLS → fuite données
* partager DB sans isolation → catastrophe

---

## 💡 insight

👉 RLS = seul vrai multi-tenant sécurisé

---

# 4. Control Plane vs Data Plane (niveau Stripe/OpenAI)

## 🔴 Principe

> séparation stricte des responsabilités

---

## 🏗 architecture

```
CONTROL PLANE
- API management
- Billing
- Auth
- Config
- Orchestration (Temporal)

DATA PLANE
- Execution (AI, jobs, tests)
- Workers
- Event processing
```

---

## 📁 séparation FastAPI

### control plane

```
app/control/
  - users
  - billing
  - api_keys
  - tenants
```

---

### data plane

```
app/data/
  - execution
  - ai_inference
  - pipelines
  - workers
```

---

## 🔴 règle

👉 Control plane = faible volume, critique
👉 Data plane = massif, scalable

---

## 📁 gateway routing

```python
@app.middleware("http")
async def route_plane(request, call_next):
    if request.url.path.startswith("/api/control"):
        request.state.plane = "control"
    else:
        request.state.plane = "data"

    return await call_next(request)
```

---

## 💡 insight critique

👉 99% des SaaS mélangent les deux → scaling impossible

---

# 🔴 SYNTHÈSE (très importante)

## Ce que tu viens d’obtenir :

| bloc               | impact                   |
| ------------------ | ------------------------ |
| Event-driven       | scalabilité + résilience |
| Audit log          | compliance + forensic    |
| Multi-tenant RLS   | sécurité réelle          |
| Control/Data plane | scalabilité architecture |

---

# ⚠️ vérité brutale

Si tu ne fais pas ces 4 choses :

👉 ton système ne peut PAS devenir enterprise-grade

---

# 🚀 CE QUI TE MANQUE ENCORE (niveau ultime)

Si tu veux aller encore plus loin :

* Event sourcing complet
* CQRS read models
* Temporal orchestration avancée
* Schema registry (Kafka)
* AsyncAPI contracts
* Backpressure management

---

# 👉 prochaine étape

Si tu veux, je peux te construire :

👉 **l’architecture complète de ton AI OPS platform (Control/Data/Event plane + Temporal + NATS + DB + Front)**

niveau :

* diagrammes
* contracts
* invariants
* phases de build

Dis-moi :
👉 **“build architecture complète”**

[1]: https://www.growin.com/blog/event-driven-architecture-scale-systems-2025/?utm_source=chatgpt.com "Event Driven Architecture Done Right: How to Scale Systems ..."



Voici **l’architecture complète S++++ (niveau hyperscaler)** adaptée à TON contexte (FastAPI + AI + orchestration).
Ce n’est pas un “design joli” — c’est un **contrat d’architecture exécutable**, avec invariants.

---

# 🧠 1. VISION GLOBALE — TON SYSTÈME FINAL

## 🔴 objectif réel

Transformer ton SaaS en :

> **AI-native distributed platform (control plane + data plane + event plane)**

---

## 🏗 ARCHITECTURE GLOBALE

```text
                        ┌────────────────────────────┐
                        │        FRONTEND (Next.js)  │
                        └────────────┬───────────────┘
                                     │
                           ┌─────────▼─────────┐
                           │   API GATEWAY     │
                           │ (FastAPI Edge)    │
                           └─────────┬─────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
┌───────▼────────┐        ┌──────────▼──────────┐       ┌─────────▼────────┐
│ CONTROL PLANE  │        │     DATA PLANE      │       │   EVENT PLANE    │
│ (state + rules)│        │ (execution engine)  │       │ (async backbone) │
└───────┬────────┘        └──────────┬──────────┘       └─────────┬────────┘
        │                            │                            │
        │                            │                            │
┌───────▼────────┐        ┌──────────▼──────────┐       ┌─────────▼────────┐
│ PostgreSQL     │        │ Workers / AI Agents │       │ Kafka / NATS     │
│ (RLS + audit)  │        │ Celery / Temporal   │       │ Event Streams    │
└────────────────┘        └─────────────────────┘       └──────────────────┘
```

---

## 🔴 invariant critique

👉 **AUCUN composant ne parle directement à un autre sans passer par un contrat**

* sync → API contract
* async → event contract

👉 sinon → couplage → mort du système

---

# 2. EVENT PLANE (le cœur réel du système)

## 🔴 vérité

Les systèmes modernes :

> ne sont pas API-first
> mais **event-first** ([Atlan][1])

---

## 🏗 architecture event plane

```text
Producer → Outbox → Broker → Consumer → Side Effects
```

---

## 🔴 composants obligatoires

| composant       | rôle              |
| --------------- | ----------------- |
| Kafka           | throughput massif |
| NATS            | low latency       |
| Schema Registry | versioning events |
| DLQ             | gestion erreurs   |
| Consumer Groups | scalabilité       |

---

## 📁 contracts AsyncAPI

```yaml
channels:
  user.created:
    subscribe:
      payload:
        type: object
        properties:
          user_id:
            type: string
```

---

## 🔴 invariants

* idempotency obligatoire
* versioning events obligatoire
* no synchronous dependency

---

## 💡 insight critique

👉 Shopify / Uber / Netflix → tout tourne sur Kafka
→ jusqu’à **66M events/sec** ([Growin][2])

---

# 3. CONTROL PLANE (le cerveau)

## 🔴 rôle

* orchestration
* config
* auth
* billing
* policies

---

## 📁 modules

```text
control/
  - auth
  - tenants
  - billing
  - api_keys
  - workflows (Temporal)
  - audit
```

---

## 🔴 DB (PostgreSQL)

* RLS activé
* audit log immuable
* config store

---

## 🔴 invariant critique

👉 control plane = **source of truth**

---

## 💡 insight

👉 dans les systèmes modernes :

> control plane = décide
> data plane = exécute

([arXiv][3])

---

# 4. DATA PLANE (le moteur)

## 🔴 rôle

* exécution AI
* jobs
* pipelines
* compute

---

## 🏗 composants

```text
Workers:
- Celery (simple)
- Temporal (enterprise)

AI Providers:
- Claude
- Gemini
- Groq

Execution:
- pipelines
- tasks
- streaming
```

---

## 🔴 invariant critique

👉 data plane = **stateless + scalable**

---

## ⚠️ erreur classique

* stocker state dans workers → scaling impossible

---

# 5. STORAGE LAYER (polyglot)

## 🧠 pattern réel

| type          | tech       |
| ------------- | ---------- |
| transactional | PostgreSQL |
| events        | Kafka      |
| cache         | Redis      |
| metrics       | Prometheus |
| blobs         | MinIO      |

---

## 🔴 invariant

👉 un seul storage = architecture morte

---

# 6. MULTI-TENANT HARD ISOLATION

## 🔴 design final

```text
JWT → tenant_id
        ↓
Middleware
        ↓
SET app.tenant_id
        ↓
PostgreSQL RLS
```

---

## 🔴 invariant

👉 sécurité = DB layer
pas code

---

# 7. OBSERVABILITY COMPLETE

## 🏗 stack

```text
Logs → structlog
Metrics → Prometheus
Tracing → OpenTelemetry
Events → Kafka
```

---

## 🔴 invariant

👉 chaque requête =

* request_id
* trace_id
* tenant_id

---

## 💡 insight

👉 sans ça → debugging impossible dans event systems

---

# 8. SECURITY MODEL

## 🔴 layers

1. API Gateway
2. JWT validation
3. RLS
4. Rate limiting
5. Audit log

---

## 🔴 invariant

👉 security = multi-layer
jamais unique point

---

# 9. ORCHESTRATION (Temporal obligatoire)

## 🔴 pourquoi

* retry natif
* timeout
* durability
* long-running workflows

---

## 🏗 exemple

```python
@workflow.defn
class GenerateAIWorkflow:
    @workflow.run
    async def run(self, input):
        result = await activity.call_ai(input)
        return result
```

---

## 💡 insight critique

👉 Celery ≠ orchestration
👉 Temporal = orchestration

---

# 10. FAILURE MODEL (très critique)

## 🔴 règles

* tout peut tomber
* tout doit retry
* tout doit être idempotent

---

## 🧠 patterns

* circuit breaker
* retry exponential
* DLQ
* backpressure

---

# 11. DEPLOYMENT (Kubernetes)

## 🏗 setup

```text
Ingress → API Gateway
Pods:
  - control plane
  - data plane workers
  - event consumers

Stateful:
  - PostgreSQL
  - Kafka
  - Redis
```

---

## 🔴 invariant

👉 stateless services uniquement

---

# 12. DATA FLOW COMPLET (important)

## 🔁 exemple réel

```text
User request
→ API Gateway
→ Control Plane (auth + config)
→ Event emitted (user.requested)

→ Data Plane consume
→ AI processing
→ Event emitted (result.ready)

→ Control Plane update DB
→ Frontend notified (SSE/WebSocket)
```

---

# 🔴 CE QUI FAIT LA DIFFÉRENCE (très important)

## 99% des systèmes FAIL ici :

### ❌ erreur 1

API-centric → couplage

### ❌ erreur 2

pas d’event sourcing → perte historique

### ❌ erreur 3

pas de separation control/data → scaling impossible

### ❌ erreur 4

pas d’observabilité → debugging impossible

---

# 🚀 TON NIVEAU APRÈS ÇA

Si tu implémentes ça correctement :

👉 tu passes de :

* SaaS backend classique

à :

* **AI-native distributed platform**

---

# 🔴 DERNIÈRE VÉRITÉ (important)

Ce qui va te bloquer maintenant :

👉 pas la technique
👉 mais la discipline architecture

---

# 👉 NEXT STEP (hautement recommandé)

Je peux te construire :

### 1. ROADMAP 10 mois (phase par phase)

### 2. STRUCTURE repo monorepo complète

### 3. CONTRATS API + EVENTS (OpenAPI + AsyncAPI)

### 4. CHECKLIST S+++ (audit architecture)

---



[1]: https://atlan.com/know/event-driven-architecture-for-ai-agents/?utm_source=chatgpt.com "Event-Driven Architecture for AI Agents: Patterns and Benefits"
[2]: https://www.growin.com/blog/event-driven-architecture-scale-systems-2025/?utm_source=chatgpt.com "Event Driven Architecture Done Right: How to Scale Systems ..."
[3]: https://arxiv.org/html/2510.04404v2?utm_source=chatgpt.com "Next-Generation Event-Driven Architectures: Performance ..."

---

## Source: Claude - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md

Chemin d'origine: `C:\Users\ibzpc\Git\SaaS-IA\mvp\docs\Architecture_backend_FastAPI_SaaS_2026\Claude - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md`

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

---

## Source: Ethy - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md

Chemin d'origine: `C:\Users\ibzpc\Git\SaaS-IA\mvp\docs\Architecture_backend_FastAPI_SaaS_2026\Ethy - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md`

Élevez Votre FastAPI au Rang S+++ : Le Guide Ultime de l'Architecture Enterprise-Grade
======================================================================================

### Transformez votre plateforme SaaS IA avec FastAPI 0.135, Python 3.13, et des pratiques d'ingénierie logicielle de pointe pour une scalabilité, une sécurité et une observabilité inégalées.

PRO

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://medium.com)![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://github.com)![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://oneuptime.com)

68+ Sources

1. [1.Points Saillants pour une Architecture S+++](#heading-1)
2. [2.1. Security Headers Middleware : Une Muraille Numérique pour Votre API](#heading-2)
3. [3.2. Request ID / Correlation ID Middleware : Tracer le Parcours de Chaque Requête](#heading-3)
4. [4.3. Gzip/Brotli Compression Middleware : Accélérer les Réponses API](#heading-4)
5. [5.4. Graceful Shutdown : Des Arrêts Propres pour une Disponibilité Continue](#heading-5)
6. [6.5. Health Checks Avancés (Kubernetes-ready) : Surveillance Intelligente](#heading-6)
7. [7.6. Database Connection Pooling : Optimisation des Accès PostgreSQL](#heading-7)
8. [8.7. Structured Logging Enterprise : Des Logs Clairs et Exploitables](#heading-8)
9. [9.8. Circuit Breaker pour AI Providers : Protéger Votre Application des Défaillances Externes](#heading-9)
10. [10.9. API Rate Limiting Avancé : Contrôle Granulaire du Trafic](#heading-10)
11. [11.10. Dockerfile Multi-Stage Optimisé : Des Images Légères et Sécurisées](#heading-11)
12. [12.11. OpenTelemetry Integration : Traçabilité et Métriques Distribuées](#heading-12)
13. [13.12. Error Tracking (Sentry-like) : Capture Intelligente des Exceptions](#heading-13)
14. [14.FAQ (Foire Aux Questions)](#heading-14)
15. [15.Conclusion](#heading-15)
16. [16.Recommandations](#heading-16)
17. [17.Résultats de recherche référencés](#heading-17)

En tant qu'expert en architecture backend Python pour les plateformes SaaS de qualité entreprise, je comprends l'importance de construire des systèmes non seulement fonctionnels mais aussi robustes, sécurisés, observables et résilients. Votre plateforme SaaS IA, avec FastAPI, Python 3.13, PostgreSQL, Redis, Celery et Docker Compose, est déjà sur une bonne voie. Mon objectif est de vous fournir les stratégies et le code exacts pour élever votre architecture au niveau "S+++".

---

Points Saillants pour une Architecture S+++
-------------------------------------------

* **Sécurité Renforcée et Observabilité Détaillée :** Implémentez des middlewares de sécurité avancés et un système de logging structuré avec des IDs de corrélation, couplés à OpenTelemetry pour une traçabilité complète, afin d'assurer une défense robuste et une visibilité sans précédent sur le comportement de votre application.
* **Gestion Intelligente des Ressources et Résilience Accrue :** Optimisez la gestion des connexions à la base de données avec des pools sophistiqués et intégrez des patterns de disjoncteur pour vos appels à des services tiers, garantissant ainsi une performance stable et une meilleure tolérance aux pannes.
* **Déploiement Robuste et Efficace :** Utilisez des Dockerfiles multi-étapes pour des images légères et sécurisées, et mettez en œuvre un mécanisme d'arrêt gracieux pour des mises à jour sans interruption, assurant la continuité et l'efficacité de vos opérations en environnement conteneurisé.

Chaque section ci-dessous détaille les implémentations spécifiques, le code, les références et les pièges à éviter pour atteindre cet objectif.

---

1. Security Headers Middleware : Une Muraille Numérique pour Votre API
----------------------------------------------------------------------

Les en-têtes de sécurité HTTP sont une première ligne de défense cruciale contre de nombreuses vulnérabilités web courantes. Ce middleware s'assure que chaque réponse de votre API inclut les directives de sécurité recommandées, protégeant vos utilisateurs et vos données.

### Code Python Complet : `app/middleware/security_headers.py`

```
# app/middleware/security_headers.py
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp,
                 hsts_max_age: int = 31536000,
                 csp_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'",
                 permissions_policy: str = "camera=(), microphone=(), geolocation=()",
                 cache_control_api: str = "no-store, no-cache, must-revalidate, proxy-revalidate",
                 cache_control_static: str = "public, max-age=31536000, immutable"):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.csp_policy = csp_policy
        self.permissions_policy = permissions_policy
        self.cache_control_api = cache_control_api
        self.cache_control_static = cache_control_static

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Strict-Transport-Security (HSTS)
        response.headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains; preload"

        # Content-Security-Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # X-Content-Type-Options: nosniff
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: DENY
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: 1; mode=block
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: strict-origin-when-cross-origin
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy
        response.headers["Permissions-Policy"] = self.permissions_policy

        # Cache-Control for API endpoints vs. static assets
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = self.cache_control_api
        elif request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = self.cache_control_static

        return response
```

### Intégration dans `main.py`

```
# main.py
from fastapi import FastAPI
from app.middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI()

# Enregistrement du middleware
app.add_middleware(
    SecurityHeadersMiddleware,
    # Personnalisez les politiques si nécessaire
    csp_policy="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' ws:",
    permissions_policy="camera=(), microphone=(), geolocation=(), clipboard-write=()",
    cache_control_api="no-store, no-cache, must-revalidate, proxy-revalidate",
    cache_control_static="public, max-age=31536000, immutable"
)

# ... vos autres routes et configurations
```

#### Astuce non-évidente :

La directive `preload` dans HSTS indique aux navigateurs d'ajouter votre domaine à une liste de préchargement HSTS, garantissant que les futures visites seront toujours via HTTPS, même la première. Cela nécessite cependant que votre domaine soit approuvé et listé par le projet Chromium HSTS preload list. Pour les politiques de cache, assurez-vous que les en-têtes sont appropriés pour chaque type de ressource. Par exemple, les API ne devraient généralement pas être mises en cache par les clients, d'où `no-store`, tandis que les assets statiques peuvent avoir un cache long.

#### Erreurs Courantes à Éviter :

* Une CSP trop restrictive peut casser des fonctionnalités (ex: intégration avec des outils tiers, CDNs). Testez minutieusement.
* Une CSP trop permissive est inefficace. Visez la spécificité.
* Oublier de configurer `preload` pour HSTS ou de le renouveler après expiration.

#### Repo GitHub de Référence :

* [tiangolo/fastapi - GitHub](https://github.com/fastapi/fastapi) (bien que les middlewares de sécurité soient souvent personnalisés, FastAPI lui-même est la base)

---

2. Request ID / Correlation ID Middleware : Tracer le Parcours de Chaque Requête
--------------------------------------------------------------------------------

Le *correlation ID* est essentiel pour la traçabilité des requêtes à travers un système distribué. Il permet de lier tous les logs, les traces et les événements à une transaction unique, simplifiant le débogage et l'analyse des incidents.

### Code Python Complet : `app/middleware/correlation_id.py` et Intégration Structlog/Celery

```
# app/middleware/correlation_id.py
import uuid
from contextvars import ContextVar
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

# ContextVar pour stocker le Request ID
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

def get_request_id() -> Optional[str]:
    return request_id_var.get()

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Request-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        token = request_id_var.set(correlation_id) # Stocke l'ID dans le contextvars

        # Injecter dans structlog pour cette requête
        structlog.contextvars.bind_contextvars(request_id=correlation_id)

        response = await call_next(request)

        response.headers["X-Request-ID"] = correlation_id
        
        structlog.contextvars.unbind_contextvars("request_id") # Nettoyer
        request_id_var.reset(token) # Réinitialiser le contextvars

        return response

# Pour Celery: propagation du Request ID
# Dans votre task Celery, vous devrez extraire le request_id du header
# et le re-bind dans structlog.contextvars si vous voulez qu'il apparaisse dans les logs de Celery.
# Exemple dans une task:
# from celery import Celery
# from structlog.contextvars import bind_contextvars
#
# celery_app = Celery('my_app')
#
# @celery_app.task(bind=True)
# def my_celery_task(self, *args, **kwargs):
#     request_id = self.request.headers.get('X-Request-ID') # Assurez-vous que Celery transmet les headers
#     if request_id:
#         bind_contextvars(request_id=request_id)
#     # ... votre logique de tâche
```

### Intégration dans `main.py`

```
# main.py
from fastapi import FastAPI
from app.middleware.correlation_id import CorrelationIdMiddleware
import structlog
import structlog.contextvars

app = FastAPI()

# Assurez-vous que ce middleware est ajouté tôt dans la pile
app.add_middleware(CorrelationIdMiddleware)

# Configuration de structlog pour inclure request_id (détaillée plus loin)
# ...
```

#### Astuce non-évidente :

L'utilisation de `contextvars` est cruciale en programmation asynchrone pour stocker des données contextuelles spécifiques à la requête sans les passer explicitement à chaque fonction. Pour Celery, la propagation du `request_id` nécessite de configurer votre broker (ex: RabbitMQ ou Redis) pour qu'il transmette les en-têtes personnalisés, puis de les récupérer et de les re-binder dans le contexte de la tâche Celery. Cela assure une traçabilité de bout en bout.

#### Erreurs Courantes à Éviter :

* Oublier de réinitialiser le `contextvars` après la requête, ce qui peut entraîner des fuites d'ID entre les requêtes.
* Ne pas propager le `request_id` aux services en aval (microservices, bases de données, queues de messages), brisant ainsi la chaîne de traçabilité.
* Ne pas configurer correctement Celery pour transmettre les en-têtes et les lier dans les workers.

#### Repo GitHub de Référence :

* [snok/asgi-correlation-id - GitHub](https://github.com/snok/asgi-correlation-id)

---

3. Gzip/Brotli Compression Middleware : Accélérer les Réponses API
------------------------------------------------------------------

La compression HTTP réduit la taille des données transférées, ce qui améliore la vitesse des requêtes et réduit la consommation de bande passante. Brotli offre généralement de meilleurs taux de compression que Gzip.

### Code Python Complet : `app/middleware/compression.py`

```
# app/middleware/compression.py
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import StreamingResponse
import brotli
import gzip
import io
import re

class SmartCompressionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, minimum_size: int = 500, exclude_paths: list[str] = None):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.exclude_paths = exclude_paths if exclude_paths is not None else []

    async def dispatch(self, request: Request, call_next):
        if any(re.match(pattern, request.url.path) for pattern in self.exclude_paths):
            return await call_next(request)

        response: Response = await call_next(request)

        if response.status_code < 200 or response.status_code >= 300:
            return response

        if not response.headers.get("content-type", "").startswith("application/json") and \
           not response.headers.get("content-type", "").startswith("text/"):
            return response
        
        if isinstance(response, StreamingResponse):
            return response

        response_body = b''
        async for chunk in response.body_iterator:
            response_body += chunk

        if len(response_body) < self.minimum_size:
            # Si le corps est trop petit, ne pas compresser
            response.headers["Content-Length"] = str(len(response_body))
            return Response(content=response_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)

        accept_encoding = request.headers.get("Accept-Encoding", "")
        
        # Préférer Brotli si supporté
        if "br" in accept_encoding and brotli:
            compressed_body = brotli.compress(response_body)
            response.headers["Content-Encoding"] = "br"
        elif "gzip" in accept_encoding:
            compressed_body = gzip.compress(response_body)
            response.headers["Content-Encoding"] = "gzip"
        else:
            response.headers["Content-Length"] = str(len(response_body))
            return Response(content=response_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)

        response.headers["Content-Length"] = str(len(compressed_body))
        # Supprime l'en-tête ETag original car le contenu compressé est différent
        if "ETag" in response.headers:
            del response.headers["ETag"]
        return Response(content=compressed_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
```

### Intégration dans `main.py`

```
# main.py
from fastapi import FastAPI
from app.middleware.compression import SmartCompressionMiddleware

app = FastAPI()

# Enregistrement du middleware de compression
app.add_middleware(
    SmartCompressionMiddleware,
    minimum_size=500,  # Compresser seulement si la taille est >= 500 octets
    exclude_paths=[
        "/metrics",        # Exclure les métriques Prometheus
        "/sse.*",          # Exclure les endpoints SSE (streaming)
        "/health/.*"       # Exclure les health checks
    ]
)

# ... vos autres routes
```

#### Astuce non-évidente :

L'ordre des middlewares est important. Le middleware de compression doit se situer après tout middleware qui pourrait modifier le corps de la réponse, mais avant les middlewares qui pourraient avoir besoin du corps final (non compressé) pour leur logique (ex: logging de la taille réelle du body). La vérification de `brotli` en tant que module est importante car il n'est pas toujours installé par défaut. S'assurer d'exclure les endpoints de streaming (SSE) et les métriques (Prometheus) est crucial pour éviter des comportements inattendus ou des performances dégradées.

#### Erreurs Courantes à Éviter :

* Compresser des fichiers déjà compressés (images, vidéos) ce qui peut augmenter la taille au lieu de la réduire.
* Compresser des très petits fichiers où le coût de la compression/décompression dépasse le gain en bande passante.
* Ne pas exclure les endpoints de streaming ou les métriques, entraînant des problèmes.
* Oublier de supprimer l'en-tête ETag après compression, ce qui peut induire les caches en erreur.

#### Repo GitHub de Référence :

* [fullonic/brotli-asgi - GitHub](https://github.com/fullonic/brotli-asgi)

---

4. Graceful Shutdown : Des Arrêts Propres pour une Disponibilité Continue
-------------------------------------------------------------------------

Un arrêt gracieux permet à une application de terminer les tâches en cours et de libérer les ressources avant de s'arrêter complètement, minimisant ainsi les interruptions de service et la perte de données.

### Code Python Complet : `app/lifespan.py` et Config Docker

```
# app/lifespan.py
import asyncio
import signal
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
import asyncpg.pool
import structlog
from celery import Celery

logger = structlog.get_logger(__name__)

# Simule un pool asyncpg
# Remplacez par votre instance réelle de pool asyncpg
# from app.db.connection import database_pool_manager (exemple)
class MockAsyncpgPool:
    def __init__(self):
        self.connections = 0
        self.is_closed = False
    
    async def connect(self):
        self.connections += 1
        logger.info("Database connection opened", current_connections=self.connections)
    
    async def close(self):
        self.connections -= 1
        logger.info("Database connection closed", current_connections=self.connections)

    async def terminate(self):
        self.is_closed = True
        logger.info("Asyncpg pool terminated")

# Remplacez par l'initialisation de votre app Celery
celery_app = Celery('my_app') 

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("FastAPI application startup")

    # ----- Initialisation des ressources -----
    # Exemple: Connexion à la base de données
    # Supposons que votre pool est géré globalement ou via une classe Singleton
    app.state.db_pool = MockAsyncpgPool() # Remplacez par votre pool réel
    logger.info("Database pool initialized")

    # ----- Gestion des signaux pour l'arrêt gracieux -----
    shutdown_event = asyncio.Event()

    def handle_signal():
        logger.info("Shutdown signal received, initiating graceful shutdown...")
        shutdown_event.set()

    # Capture SIGTERM et SIGINT (Ctrl+C)
    # Note: Uvicorn gère déjà SIGTERM/SIGINT de base pour son propre processus
    # Ceci est plus pour des logiques d'arrêt spécifiques à l'application
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, handle_signal)
    loop.add_signal_handler(signal.SIGINT, handle_signal)
    
    # Démarrage des workers Celery (si non démarrés séparément)
    # Si Celery est un service distinct, cette partie n'est pas nécessaire ici
    # Si vous voulez un warm shutdown, Celery doit être configuré pour cela.
    # celery_app.control.enable_events() # Pour surveiller les tâches
    # logger.info("Celery worker events enabled")

    yield

    # ----- Nettoyage des ressources lors de l'arrêt -----
    logger.info("FastAPI application shutdown initiated")

    # Attendre que toutes les requêtes HTTP en cours soient terminées (max 30s)
    # Uvicorn gère cela en interne via son <code>graceful_timeout.
    # Pour une logique plus fine, vous pourriez utiliser des compteurs de requêtes actives.
    # await shutdown_event.wait() # Si vous voulez attendre un signal explicite

    # Fermeture propre du pool asyncpg
    if hasattr(app.state, 'db_pool') and app.state.db_pool:
        logger.info("Closing database pool...")
        await app.state.db_pool.terminate()
        logger.info("Database pool closed")

    # Celery worker: warm shutdown
    # Si Celery est géré par un autre processus (ex: en dehors de FastAPI),
    # il doit avoir sa propre logique de warm shutdown.
    # Exemple de commande pour un warm shutdown de Celery:
    # celery -A proj worker -P solo -c 1 --loglevel=info --pool=solo --time-limit=30 --max-tasks-per-child=1 --max-memory-per-child=1000 --shutdown-when-finished
    # Pour déclencher un shutdown via l'application FastAPI, cela dépend de votre architecture.
    # Souvent, Celery workers reçoivent un SIGTERM directement de Kubernetes/Docker.
    # Pour une approche in-app si Celery tourne avec FastAPI, vous pouvez simuler
    # un warm shutdown pour les tâches en cours si vous les gérez.
    # logger.info("Initiating warm shutdown for Celery workers (if running within this process)...")
    # celery_app.control.broadcast('shutdown', destination=[]) # Cela envoie un signal de shutdown
    #                                                       # mais les tâches en cours peuvent finir.
    # asyncio.sleep(5) # Attendre un peu pour que les messages soient traités
    logger.info("FastAPI application shutdown complete")
```

### Intégration dans `main.py`

```
# main.py
from fastapi import FastAPI
from app.lifespan import lifespan # Importer votre fonction lifespan

app = FastAPI(lifespan=lifespan)

# ... vos routes
```

### Configuration Docker

```
# Dockerfile
# ... votre Dockerfile optimisé (voir section 10)
STOPSIGNAL SIGTERM
# Pour Uvicorn, le paramètre --graceful-timeout gère le temps d'attente
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--graceful-timeout", "30"]

# docker-compose.yml
services:
  fastapi_app:
    build: .
    ports:
      - "8000:8000"
    stop_signal: SIGTERM
    stop_grace_period: 30s # Donne 30 secondes au conteneur pour s'arrêter
  celery_worker:
    build: .
    command: celery -A app.celery_worker.celery_app worker -P gevent -c 1 --loglevel=info --time-limit=300 --max-tasks-per-child=1 # Exemple de commande
    stop_signal: SIGTERM
    stop_grace_period: 60s # Plus long pour Celery car les tâches peuvent être longues
```

#### Astuce non-évidente :

Pour Celery, un "warm shutdown" signifie que le worker arrête d'accepter de nouvelles tâches, mais termine celles qui sont déjà en cours. La commande `celery multi stop --wait` ou l'envoi d'un `SIGTERM` au worker Celery permet cette approche. Le `--time-limit` et `--max-tasks-per-child` de Celery sont également cruciaux pour éviter que des tâches individuelles ne bloquent le shutdown. Dans Docker Compose et Kubernetes, `stop_grace_period` et le `STOPSIGNAL` travaillent ensemble pour permettre un arrêt en douceur.

#### Erreurs Courantes à Éviter :

* Ne pas libérer les ressources ouvertes (connexions DB, fichiers, etc.) lors du shutdown.
* Dépendre uniquement du `SIGKILL` par défaut, qui coupe brutalement l'application.
* Ne pas donner suffisamment de temps aux workers Celery pour terminer leurs tâches.
* Oublier de configurer le `graceful-timeout` d'Uvicorn pour FastAPI.

#### Repo GitHub de Référence :

* [tiangolo/fastapi - GitHub](https://github.com/fastapi/fastapi) (pour le `lifespan`)

---

5. Health Checks Avancés (Kubernetes-ready) : Surveillance Intelligente
-----------------------------------------------------------------------

Les probes Kubernetes (liveness, readiness, startup) sont fondamentales pour une gestion efficace des pods. Des checks avancés garantissent que l'état rapporté reflète précisément la capacité du service à fonctionner.

### Code Python Complet : `app/routers/health.py`

```
# app/routers/health.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import asyncpg
import redis.asyncio as redis
import os
import asyncio
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)

# Dépendances pour les checks de connectivité (mock pour l'exemple)
# Remplacez par vos fonctions de connexion réelles
async def get_db_pool():
    # Ici, vous retournerez votre pool de connexion asyncpg réel
    class MockDBPool:
        async def fetchval(self, query):
            # Simule une requête simple à la DB
            await asyncio.sleep(0.01)
            return 1
    return MockDBPool()

async def get_redis_client():
    # Ici, vous retournerez votre client Redis réel
    class MockRedisClient:
        async def ping(self):
            await asyncio.sleep(0.01)
            return True
    return MockRedisClient()


@router.get("/health/live", summary="Liveness Probe", status_code=status.HTTP_200_OK)
async def liveness_probe() -> Dict[str, str]:
    """
    Indique si l'application est en cours d'exécution.
    Ne devrait échouer qu'en cas de crash majeur (ex: blocage de l'event loop).
    """
    return {"status": "alive"}

@router.get("/health/ready", summary="Readiness Probe", status_code=status.HTTP_200_OK)
async def readiness_probe(
    db_pool: object = Depends(get_db_pool), # Typez avec votre pool réel (ex: asyncpg.pool.Pool)
    redis_client: object = Depends(get_redis_client) # Typez avec votre client réel (ex: redis.asyncio.Redis)
) -> Dict[str, str]:
    """
    Indique si l'application est prête à servir des requêtes.
    Vérifie les dépendances critiques (DB, Redis).
    """
    checks = {}
    try:
        # Check PostgreSQL
        # Exemple: exécutez une requête légère
        await db_pool.fetchval("SELECT 1")
        checks["postgresql"] = "ok"
    except Exception as e:
        logger.error("Readiness check failed: PostgreSQL", error=str(e))
        checks["postgresql"] = f"failed: {e}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="PostgreSQL unavailable")

    try:
        # Check Redis
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        logger.error("Readiness check failed: Redis", error=str(e))
        checks["redis"] = f"failed: {e}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis unavailable")

    return {"status": "ready", "dependencies": checks}

@router.get("/health/startup", summary="Startup Probe", status_code=status.HTTP_200_OK)
async def startup_probe() -> Dict[str, str]:
    """
    Indique si l'application a terminé son initialisation coûteuse (migrations, chargement modules).
    """
    # Exemple: Vérifier l'état d'une variable globale ou d'un fichier de lock
    # qui indique que les migrations ont été appliquées et que les modules sont chargés.
    # Dans un environnement réel, cela pourrait impliquer:
    # - La vérification de la version de la base de données après migrations
    # - La confirmation du chargement de modèles ML ou de configurations complexes
    
    # Placeholder: Implémentez votre logique réelle ici
    # Par exemple, si vous avez un flag global <code>app.state.startup_complete = True
    if not os.path.exists("/tmp/app_startup_complete"): # Exemple de flag via fichier
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Application still starting up")
    
    # Simulate async operations
    await asyncio.sleep(0.1) 
    
    return {"status": "startup_complete"}
```

### Intégration dans `main.py`

```
# main.py
from fastapi import FastAPI
from app.routers import health

app = FastAPI()

app.include_router(health.router)

# Pour la startup probe, vous devrez signaler la complétion après vos initialisations
# Par exemple, dans votre fonction lifespan ou après les migrations
@app.on_event("startup")
async def app_startup_event():
    # Exemple: exécuter les migrations ici ou charger des modules lourds
    # await run_migrations()
    # await load_ml_models()
    # Une fois tout terminé:
    with open("/tmp/app_startup_complete", "w") as f:
        f.write("ready")
    print("Application startup process complete.") # Output pour debug
```

### Configuration Docker/K8s

```
# Dockerfile
# Ajoutez une instruction HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/health/live || exit 1
```

```
# Kubernetes Deployment YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-fastapi-app
spec:
  # ...
  template:
    # ...
    spec:
      containers:
      - name: fastapi-container
        image: my-fastapi-image:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 15 # Démarrer la vérification après 15s
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 30 # Démarrer la vérification après 30s
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health/startup
            port: 8000
          initialDelaySeconds: 0
          periodSeconds: 5
          failureThreshold: 20 # Permettre 20 * 5 = 100 secondes pour le démarrage
          timeoutSeconds: 5
```

#### Astuce non-évidente :

Pour la `startupProbe`, l'utilisation d'un fichier temporaire (comme `/tmp/app_startup_complete`) est une méthode simple pour signaler la complétion. Dans des environnements plus complexes, vous pourriez utiliser une entrée Redis ou une petite table dans PostgreSQL pour stocker l'état de démarrage. Il est crucial d'ajuster `initialDelaySeconds` et `failureThreshold` pour donner à votre application suffisamment de temps pour démarrer, surtout si des migrations ou des chargements de données sont longs.

#### Erreurs Courantes à Éviter :

* Utiliser le même endpoint pour toutes les probes (`/health` qui renvoie toujours 200).
* Des checks trop longs ou coûteux dans les probes de liveness/readiness, qui peuvent bloquer l'application.
* Des seuils de `failureThreshold` trop bas pour la `startupProbe`, ce qui peut tuer l'application avant qu'elle n'ait eu le temps de démarrer.

#### Repo GitHub de Référence :

* [kubernetes/kubernetes - GitHub](https://github.com/kubernetes/kubernetes) (pour les concepts de probes)

---

6. Database Connection Pooling : Optimisation des Accès PostgreSQL
------------------------------------------------------------------

Le *connection pooling* est une technique essentielle pour gérer les connexions à la base de données. Il permet de réutiliser des connexions existantes plutôt que d'en ouvrir et d'en fermer de nouvelles à chaque requête, ce qui réduit considérablement la latence et la charge sur le serveur de base de données.

### Code Python Complet : `app/db/connection.py`

```
# app/db/connection.py
import asyncpg
import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool # Pour les tests, utilisez NullPool
import structlog

logger = structlog.get_logger(__name__)

class DatabasePoolManager:
    _instance: Optional[asyncpg.pool.Pool] = None
    _engine = None
    _session_factory = None

    @classmethod
    async def initialize(
        cls,
        db_url: str,
        pool_min_size: int = 5,
        pool_max_size: int = 20,
        pool_timeout: int = 60, # seconds to wait for a connection from the pool
        pool_recycle: int = 3600, # seconds after which a connection is recycled
        max_overflow: int = 10, # additional connections to create beyond max_size
        connect_attempts: int = 5, # number of retry attempts
        retry_delay_base: int = 1, # base delay for exponential backoff
    ):
        if cls._instance is not None:
            return

        for attempt in range(connect_attempts):
            try:
                # Configuration pour asyncpg
                cls._instance = await asyncpg.create_pool(
                    db_url,
                    min_size=pool_min_size,
                    max_size=pool_max_size,
                    timeout=pool_timeout,
                    max_inactive_connection_lifetime=pool_recycle, # Equivalent de pool_recycle pour asyncpg
                    # Optionnel: 'setup' peut exécuter des commandes après chaque connexion
                    # setup=lambda conn: conn.set_type_codec(...)
                )
                logger.info("Database pool initialized successfully with asyncpg")

                # Configuration pour SQLAlchemy 2.0 Async
                # 'postgresql+asyncpg' indique d'utiliser asyncpg comme driver
                cls._engine = create_async_engine(
                    db_url,
                    pool_size=pool_min_size, # Taille initiale du pool SQLAlchemy
                    max_overflow=max_overflow, # Connexions additionnelles pour SQLAlchemy
                    pool_timeout=pool_timeout, # Timeout pour obtenir une connexion
                    pool_recycle=pool_recycle, # Recycler les connexions après cette durée
                    pool_pre_ping=True, # Vérifie la viabilité de la connexion avant usage
                    echo=False, # Mettre à True pour afficher les requêtes SQL
                    future=True
                )
                cls._session_factory = async_sessionmaker(
                    cls._engine, 
                    expire_on_commit=False, 
                    class_=AsyncSession
                )
                logger.info("SQLAlchemy Async Engine and Session Factory initialized successfully")
                return

            except asyncpg.exceptions.PostgresError as e:
                logger.warning(
                    f"Failed to connect to database (attempt {attempt + 1}/{connect_attempts}): {e}",
                    delay=retry_delay_base * (2 ** attempt)
                )
                if attempt < connect_attempts - 1:
                    await asyncio.sleep(retry_delay_base * (2 ** attempt))
                else:
                    logger.error("All database connection attempts failed. Exiting.")
                    raise

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            logger.info("Asyncpg database pool closed")
            cls._instance = None
        if cls._engine:
            await cls._engine.dispose()
            logger.info("SQLAlchemy Async Engine disposed")
            cls._engine = None
        cls._session_factory = None


    @classmethod
    def get_pool(cls) -> asyncpg.pool.Pool:
        if cls._instance is None:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        return cls._instance

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            raise RuntimeError("SQLAlchemy Async Engine not initialized. Call initialize() first.")
        return cls._engine

    @classmethod
    async def get_session(cls) -> AsyncGenerator[AsyncSession, None]:
        if cls._session_factory is None:
            raise RuntimeError("SQLAlchemy Async Session Factory not initialized. Call initialize() first.")
        async with cls._session_factory() as session:
            try:
                yield session
            finally:
                await session.close() # La connexion est retournée au pool

    # Méthode pour obtenir les métriques du pool (asyncpg seulement)
    @classmethod
    def get_pool_metrics(cls) -> dict:
        if cls._instance:
            return {
                "connections_total": cls._instance.get_size(),
                "connections_active": cls._instance.get_busy_size(),
                "connections_idle": cls._instance.get_idle_size(),
                "connections_waiting": cls._instance.get_waiters(),
            }
        return {}
```

### Intégration dans `main.py`

```
# main.py
from fastapi import FastAPI, Depends
from app.db.connection import DatabasePoolManager, AsyncSession
import os

app = FastAPI()

@app.on_event("startup")
async def startup_db_pool():
    # Récupérez l'URL de votre base de données depuis les variables d'environnement
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@host:port/dbname")
    await DatabasePoolManager.initialize(
        db_url=db_url,
        pool_min_size=5,
        pool_max_size=20,
        pool_timeout=60,
        pool_recycle=3600,
        max_overflow=10,
        connect_attempts=10, # Plus de tentatives au démarrage
        retry_delay_base=2
    )

@app.on_event("shutdown")
async def shutdown_db_pool():
    await DatabasePoolManager.close()

# Exemple d'utilisation dans une route
@app.get("/items")
async def read_items(session: AsyncSession = Depends(DatabasePoolManager.get_session)):
    # Utilisez la session pour interagir avec la base de données via SQLModel
    # from sqlmodel import select
    # result = await session.execute(select(YourSQLModelClass))
    # items = result.scalars().all()
    # return items
    return {"message": "Database access example"}

@app.get("/db-metrics")
async def get_db_metrics():
    return DatabasePoolManager.get_pool_metrics()
```

#### Astuce non-évidente :

L'utilisation de `pool_pre_ping=True` avec SQLAlchemy est essentielle pour s'assurer que les connexions dans le pool sont toujours viables avant d'être utilisées. Cela aide à gérer les scénarios où la base de données a fermé des connexions inactives. Pour `asyncpg`, l'équivalent est `max_inactive_connection_lifetime`. Le backoff exponentiel pour les tentatives de connexion au démarrage est également une bonne pratique pour ne pas surcharger la base de données si elle est temporairement indisponible.

#### Erreurs Courantes à Éviter :

* Oublier de fermer le pool de connexions lors de l'arrêt de l'application, entraînant des connexions "orphans".
* Des tailles de pool trop petites, provoquant des blocages par manque de connexions disponibles.
* Des tailles de pool trop grandes, surchargeant la base de données.
* Ne pas gérer les échecs de connexion initiaux avec des retries et un backoff.
* Utiliser des connexions bloquantes (`psycopg2`) dans un contexte asynchrone (FastAPI).

#### Repo GitHub de Référence :

* [sqlalchemy/sqlalchemy - GitHub](https://github.com/sqlalchemy/sqlalchemy)
* [MagicStack/asyncpg - GitHub](https://github.com/MagicStack/asyncpg)

---

7. Structured Logging Enterprise : Des Logs Clairs et Exploitables
------------------------------------------------------------------

Le logging structuré avec `structlog` transforme vos journaux en données exploitables, facilitant l'analyse, la recherche et le monitoring. L'intégration de contextvars permet d'enrichir chaque log avec des informations contextuelles clés comme le request ID ou l'ID utilisateur.

### Code Python Complet : `app/logging_config.py`

```
# app/logging_config.py
import logging
import os
import sys
import structlog
import time
import re
from typing import Any, Dict

# Liste des champs sensibles à filtrer
SENSITIVE_FIELDS = {"password", "token", "jwt", "api_key", "secret"}

def filter_sensitive_data(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Filtre les données sensibles des event_dict."""
    for key in list(event_dict.keys()):
        if any(sf in key.lower() for sf in SENSITIVE_FIELDS):
            event_dict[key] = "[FILTERED]"
    return event_dict

def add_request_duration(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Ajoute la durée de la requête aux logs."""
    start_time = structlog.contextvars.get_contextvars().get("start_time")
    if start_time:
        duration = time.perf_counter() - start_time
        event_dict["duration_ms"] = round(duration * 1000, 2)
    return event_dict

def add_user_id(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Injecte l'ID utilisateur depuis le contexte."""
    user_id = structlog.contextvars.get_contextvars().get("user_id")
    if user_id:
        event_dict["user_id"] = user_id
    return event_dict

def configure_logging(json_logs: bool = False, log_level: str = "INFO"):
    """Configure structlog pour l'application FastAPI."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_user_id, # Injecte l'ID utilisateur
        add_request_duration, # Calcule et injecte la durée de la requête
        filter_sensitive_data, # Filtre les données sensibles
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        # Configuration pour les logs JSON en production
        processor = structlog.processors.JSONRenderer()
    else:
        # Configuration pour les logs lisibles en développement
        processor = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [processor],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Capture les logs Python standard et les achemine via structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
        handlers=[
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter(
                logging.StreamHandler(sys.stdout),
                wrapper_class=structlog.stdlib.BoundLogger,
                processors=shared_processors + [
                    structlog.stdlib.ProcessorFormatter.drop_color_wrap, # Important pour éviter les caractères de couleur dans JSON
                    processor,
                ],
            )
        ]
    )

    # Définir les niveaux de log pour des modules spécifiques
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Moins verbeux pour l'accès uvicorn
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("asyncpg").setLevel(logging.INFO) # Ajustez si vous avez besoin de plus de détails sur la DB
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING) # Évitez les logs trop verbeux de SQLAlchemy

# Middleware pour le timing des requêtes et le nettoyage du contexte
class LoggingContextMiddleware:
    async def __call__(self, request, call_next):
        structlog.contextvars.clear_contextvars()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())) # Assurez-vous d'avoir le CorrelationIdMiddleware avant
        user_id = request.state.get("user_id") # Supposons que votre auth middleware a mis user_id dans request.state
        
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            user_id=user_id,
            path=request.url.path,
            method=request.method,
            start_time=time.perf_counter()
        )

        response = await call_next(request)
        return response
```

### Intégration dans `main.py`

```
# main.py
from fastapi import FastAPI, Request
from app.logging_config import configure_logging, LoggingContextMiddleware
from app.middleware.correlation_id import CorrelationIdMiddleware # Import pour l'ordre
import structlog
import os
import uuid

# Configure structlog TÔT
json_logs_enabled = os.getenv("ENVIRONMENT", "development") == "production"
log_level = os.getenv("LOG_LEVEL", "INFO")
configure_logging(json_logs=json_logs_enabled, log_level=log_level)

logger = structlog.get_logger(__name__)

app = FastAPI()

# Les middlewares structlog doivent être appelés dans l'ordre pour que les contextes soient bien définis.
# 1. CorrelationIdMiddleware doit venir en premier pour générer/récupérer le request_id
app.add_middleware(CorrelationIdMiddleware)
# 2. LoggingContextMiddleware pour bind d'autres infos et le timing
app.middleware("http")(LoggingContextMiddleware()) # Utilisation directe comme fonction décorateur
# ... (autres middlewares comme SecurityHeadersMiddleware, SmartCompressionMiddleware)

# Exemple de middleware d'authentification qui met l'user_id dans request.state
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Simuler l'extraction de user_id à partir du JWT
    # En production, vous auriez une logique de vérification JWT
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # decoded_token = decode_jwt(auth_header[7:])
        # request.state.user_id = decoded_token.get("sub") # 'sub' est souvent l'ID utilisateur
        request.state.user_id = "user_123" # Placeholder
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    logger.info("Root endpoint accessed", some_data="value")
    return {"message": "Hello from FastAPI"}
```

#### Astuce non-évidente :

L'utilisation de `structlog.contextvars.clear_contextvars()` au début de chaque requête dans `LoggingContextMiddleware` est cruciale pour éviter les fuites de contexte entre les requêtes. Sans cela, une requête pourrait hériter des informations d'une requête précédente (comme le `request_id` ou `user_id`), ce qui est un problème majeur de sécurité et de traçabilité. Assurez-vous que votre middleware d'authentification définit le `user_id` dans `request.state` pour qu'il soit disponible pour le middleware de logging.

#### Erreurs Courantes à Éviter :

* Oublier de configurer `structlog.contextvars.clear_contextvars()`, entraînant des contextes de logs incorrects.
* Ne pas capturer les logs des librairies standard via `logging.basicConfig` et `structlog.stdlib.ProcessorFormatter`.
* Des filtres de données sensibles incomplets, laissant des informations exposées.
* Des niveaux de log inappropriés, rendant les logs trop verbeux ou pas assez informatifs.

#### Repo GitHub de Référence :

* [hynek/structlog - GitHub](https://github.com/hynek/structlog)

---

8. Circuit Breaker pour AI Providers : Protéger Votre Application des Défaillances Externes
-------------------------------------------------------------------------------------------

Le pattern *Circuit Breaker* est une défense essentielle pour les applications distribuées. Il empêche une application de tenter continuellement d'accéder à un service externe défaillant, ce qui pourrait épuiser les ressources et entraîner des défaillances en cascade. Au lieu de cela, il échoue rapidement, permettant au service défaillant de récupérer et offrant des stratégies de fallback.

### Code Python Complet : `app/circuit_breaker.py`

```
# app/circuit_breaker.py
import time
import asyncio
from enum import Enum, auto
from typing import Callable, Any, Coroutine
import structlog

logger = structlog.get_logger(__name__)

class CircuitBreakerState(Enum):
    CLOSED = auto()    # Le service fonctionne normalement. Les requêtes passent.
    OPEN = auto()      # Le service est défaillant. Les requêtes sont bloquées.
    HALF_OPEN = auto() # Après une période, quelques requêtes sont autorisées à tester si le service a récupéré.

class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,  # Temps en secondes pour passer de OPEN à HALF_OPEN
        reset_timeout: int = 300,    # Temps en secondes pour réinitialiser le compteur de pannes en CLOSED
        fallback_function: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.reset_timeout = reset_timeout
        self.fallback_function = fallback_function

        self._state = CircuitBreakerState.CLOSED
        self._failures = 0
        self._last_failure_time = None
        self._last_open_time = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitBreakerState:
        # Logique pour passer de OPEN à HALF_OPEN
        if self._state == CircuitBreakerState.OPEN:
            if time.time() - self._last_open_time > self.recovery_timeout:
                self._state = CircuitBreakerState.HALF_OPEN
                logger.warning(f"Circuit Breaker '{self.name}' moved to HALF_OPEN state.", state="HALF_OPEN")
        
        # Logique pour réinitialiser le compteur de pannes si CLOSED depuis longtemps
        if self._state == CircuitBreakerState.CLOSED and self._failures > 0 and \
           self._last_failure_time and time.time() - self._last_failure_time > self.reset_timeout:
            self._failures = 0
            logger.info(f"Circuit Breaker '{self.name}' reset failure count.", state="CLOSED", failures=self._failures)

        return self._state

    async def __call__(self, func: Callable[..., Coroutine[Any, Any, Any]]):
        async def wrapper(*args, **kwargs):
            async with self._lock:
                current_state = self.state

                if current_state == CircuitBreakerState.OPEN:
                    logger.warning(
                        f"Circuit Breaker '{self.name}' is OPEN, blocking call to '{func.__name__}'.",
                        state="OPEN"
                    )
                    if self.fallback_function:
                        return await self.fallback_function(*args, **kwargs)
                    raise CircuitBreakerOpenException(
                        f"Circuit Breaker '{self.name}' is OPEN."
                    )
                
                if current_state == CircuitBreakerState.HALF_OPEN:
                    # Une seule requête est autorisée à passer pour tester la récupération
                    if self._failures == 0: # Si c'est la première requête en HALF_OPEN
                        logger.info(
                            f"Circuit Breaker '{self.name}' is HALF_OPEN, allowing a single test call to '{func.__name__}'.",
                            state="HALF_OPEN"
                        )
                    else: # Toutes les autres requêtes sont bloquées
                        logger.warning(
                            f"Circuit Breaker '{self.name}' is HALF_OPEN, but test call already in progress or failed. Blocking call to '{func.__name__}'.",
                            state="HALF_OPEN"
                        )
                        if self.fallback_function:
                            return await self.fallback_function(*args, **kwargs)
                        raise CircuitBreakerOpenException(
                            f"Circuit Breaker '{self.name}' is HALF_OPEN."
                        )

            try:
                result = await func(*args, **kwargs)
                async with self._lock:
                    if current_state != CircuitBreakerState.CLOSED:
                        # Si la requête en HALF_OPEN réussit, réinitialiser
                        self._state = CircuitBreakerState.CLOSED
                        self._failures = 0
                        self._last_failure_time = None
                        self._last_open_time = None
                        logger.info(
                            f"Circuit Breaker '{self.name}' moved to CLOSED state after successful call.",
                            state="CLOSED"
                        )
                return result
            except Exception as e:
                async with self._lock:
                    self._failures += 1
                    self._last_failure_time = time.time()
                    logger.error(
                        f"Circuit Breaker '{self.name}' recorded a failure calling '{func.__name__}'. "
                        f"Failures: {self._failures}/{self.failure_threshold}",
                        error=str(e), state=self._state
                    )
                    if self._failures >= self.failure_threshold and self._state != CircuitBreakerState.OPEN:
                        self._state = CircuitBreakerState.OPEN
                        self._last_open_time = time.time()
                        logger.error(
                            f"Circuit Breaker '{self.name}' moved to OPEN state due to excessive failures.",
                            state="OPEN"
                        )
                
                if self.fallback_function:
                    return await self.fallback_function(*args, **kwargs)
                raise CircuitBreakerFailedException(
                    f"Circuit Breaker '{self.name}' failed after {self._failures} attempts."
                ) from e
        return wrapper

class CircuitBreakerOpenException(Exception):
    """Exception levée lorsque le circuit breaker est en état OPEN."""
    pass

class CircuitBreakerFailedException(Exception):
    """Exception levée lorsque le circuit breaker a échoué (mais n'est pas OPEN)."""
    pass

# ---------- Gestion des Providers IA ----------
class AIProvider:
    def __init__(self, name: str, cb: CircuitBreaker):
        self.name = name
        self.circuit_breaker = cb

    @self.circuit_breaker
    async def call_ai_service(self, prompt: str) -> str:
        logger.info(f"Calling AI service {self.name} with prompt", prompt=prompt)
        # Simuler une défaillance ou un succès
        if time.time() % 10 < 3: # 30% de chance d'échec
            logger.error(f"AI service {self.name} failed!", provider=self.name)
            raise ValueError(f"AI service {self.name} temporarily unavailable")
        
        await asyncio.sleep(0.5) # Simuler le temps de réponse
        return f"Response from {self.name} for: {prompt}"

async def fallback_ai_response(prompt: str) -> str:
    logger.warning("Using fallback AI response", prompt=prompt)
    return f"Fallback response for: {prompt} (AI service unavailable)"

# Initialisation des Circuit Breakers et Providers
gemini_cb = CircuitBreaker(
    name="Gemini",
    failure_threshold=3,
    recovery_timeout=30, # 30s avant de passer en HALF_OPEN
    fallback_function=fallback_ai_response
)
gemini_provider = AIProvider("Gemini", gemini_cb)

claude_cb = CircuitBreaker(
    name="Claude",
    failure_threshold=5,
    recovery_timeout=60,
    fallback_function=fallback_ai_response
)
claude_provider = AIProvider("Claude", claude_cb)

groq_cb = CircuitBreaker(
    name="Groq",
    failure_threshold=2,
    recovery_timeout=15,
    fallback_function=fallback_ai_response
)
groq_provider = AIProvider("Groq", groq_cb)

# Liste des providers, par ordre de préférence (ou de coût, etc.)
AI_PROVIDERS = [gemini_provider, claude_provider, groq_provider]

async def call_with_provider_fallback(prompt: str) -> str:
    for provider in AI_PROVIDERS:
        try:
            return await provider.call_ai_service(prompt)
        except (CircuitBreakerOpenException, CircuitBreakerFailedException):
            logger.warning(f"Provider {provider.name} unavailable or circuit open, trying next one.")
            continue # Tente le prochain provider
        except Exception as e:
            # Gérer les autres exceptions non liées au circuit breaker ici
            logger.error(f"Error calling {provider.name}: {e}", provider=provider.name)
            continue
    
    logger.critical("All AI providers failed or are unavailable.")
    return await fallback_ai_response(prompt) # Si tous les providers échouent, utilisez le fallback global
```

### Intégration dans `main.py`

```
# main.py
from fastapi import FastAPI
from app.circuit_breaker import call_with_provider_fallback, gemini_cb, claude_cb, groq_cb
import structlog

logger = structlog.get_logger(__name__)
app = FastAPI()

@app.get("/generate-ai-text")
async def generate_ai_text(prompt: str):
    try:
        response = await call_with_provider_fallback(prompt)
        # Pour le monitoring, vous pouvez loguer l'état des breakers
        logger.info("AI Provider states",
                    gemini_state=str(gemini_cb.state.name),
                    claude_state=str(claude_cb.state.name),
                    groq_state=str(groq_cb.state.name))
        return {"response": response}
    except Exception as e:
        logger.error("Failed to generate AI text after all fallbacks", error=str(e))
        return {"error": "Could not generate AI text at this time."}, 500
```

*Comparaison des capacités architecturales : de l'état actuel à l'objectif S+++.*

Ce graphique radar illustre l'amélioration des caractéristiques clés de votre plateforme en passant d'une architecture fonctionnelle mais standard à une architecture S+++ de niveau entreprise. Chaque point représente une dimension cruciale où les pratiques proposées dans ce guide apportent des gains significatifs, transformant votre application en un système hautement optimisé et résilient.

#### Astuce non-évidente :

L'implémentation du `CircuitBreaker` en tant que décorateur asynchrone est puissante, mais elle doit être thread-safe. L'utilisation d'un `asyncio.Lock` est essentielle pour protéger les variables d'état du disjoncteur (`_state`, `_failures`, etc.) contre les accès concurrents, évitant ainsi les conditions de course dans un environnement FastAPI asynchrone. La gestion des différents providers avec une boucle et un fallback permet une grande flexibilité et une meilleure résilience.

#### Erreurs Courantes à Éviter :

* Oublier la synchronisation des états du disjoncteur dans un environnement concurrentiel.
* Définir des seuils de panne trop bas, ce qui pourrait faire passer le disjoncteur en état OPEN trop fréquemment.
* Des fonctions de fallback qui échouent également, ou qui sont trop lentes.
* Ne pas avoir de mécanisme de réinitialisation automatique du compteur de pannes en état CLOSED, même sans panne, pour éviter qu'une accumulation lente de pannes ne l'ouvre brusquement.

#### Repo GitHub de Référence :

* [Netflix/Hystrix - GitHub](https://github.com/Netflix/Hystrix) (bien que Hystrix soit en Java, c'est la référence historique pour les patterns de circuit breaker)

---

9. API Rate Limiting Avancé : Contrôle Granulaire du Trafic
-----------------------------------------------------------

Le *Rate Limiting* est essentiel pour protéger votre API contre les abus, les attaques par déni de service (DoS) et pour assurer une utilisation équitable des ressources. Un système avancé intègre des algorithmes plus sophistiqués et fournit des en-têtes de réponse standards.

### Code Python Complet : `app/middleware/rate_limiter.py`

```
# app/middleware/rate_limiter.py
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import redis.asyncio as redis
import time
import math
import os
from collections import deque
from typing import Dict, Deque, Any
import structlog

logger = structlog.get_logger(__name__)

# Config Redis (remplacez par votre configuration réelle)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client: Optional[redis.Redis] = None

async def get_redis_client_instance():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL)
    return redis_client

class SlidingWindowRateLimiter:
    def __init__(self, capacity: int, window_seconds: int, burst_capacity: int = 0):
        self.capacity = capacity
        self.window_seconds = window_seconds
        self.burst_capacity = burst_capacity
        self.timestamps: Dict[str, Deque[float]] = {}
        self.last_reset: Dict[str, float] = {}

    async def _cleanup_timestamps(self, key: str):
        now = time.time()
        # Supprimer les timestamps en dehors de la fenêtre glissante
        while self.timestamps[key] and self.timestamps[key][0] <= now - self.window_seconds:
            self.timestamps[key].popleft()

    async def allow_request(self, key: str) -> (bool, int, int, int):
        if key not in self.timestamps:
            self.timestamps[key] = deque()
            self.last_reset[key] = time.time()

        await self._cleanup_timestamps(key)
        
        now = time.time()
        current_requests = len(self.timestamps[key])
        
        # Logique pour le burst allowance (basé sur le Token Bucket, mais intégré ici)
        # Ici, une approche simplifiée: le burst est un dépassement temporaire de la capacité normale.
        # Nous allons vérifier si le nombre de requêtes dépasse la capacité normale
        # ET la capacité de burst.
        
        allowed_limit = self.capacity
        if self.burst_capacity > 0:
            # Pour un burst, nous permettons temporairement plus de requêtes
            # L'idée est que vous pouvez faire plus de requêtes en un court laps de temps
            # tant que le total sur la fenêtre reste gérable.
            # Une implémentation réelle de Token Bucket serait plus précise.
            # Ici, nous nous basons sur le fait que le nombre de requêtes "réelles"
            # ne dépasse pas la capacité + burst.
            allowed_limit = self.capacity + self.burst_capacity

        if current_requests < allowed_limit:
            self.timestamps[key].append(now)
            remaining = allowed_limit - len(self.timestamps[key])
            reset_after = max(0, self.window_seconds - (now - self.last_reset[key]))
            return True, allowed_limit, remaining, math.ceil(reset_after)
        else:
            remaining = allowed_limit - current_requests
            reset_after = max(0, self.window_seconds - (now - self.last_reset[key]))
            return False, allowed_limit, remaining, math.ceil(reset_after)

# Utilisation d'un dictionnaire pour gérer plusieurs limiteurs par endpoint/route
rate_limiters: Dict[str, SlidingWindowRateLimiter] = {}

class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp,
                 default_capacity: int = 100,
                 default_window_seconds: int = 60,
                 default_burst: int = 20,
                 whitelist_ips: list[str] = None,
                 config_per_path: Dict[str, Dict[str, Any]] = None):
        super().__init__(app)
        self.default_capacity = default_capacity
        self.default_window_seconds = default_window_seconds
        self.default_burst = default_burst
        self.whitelist_ips = whitelist_ips if whitelist_ips is not None else []
        self.config_per_path = config_per_path if config_per_path is not None else {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        if client_ip in self.whitelist_ips:
            return await call_next(request)

        # Déterminer la clé de limite (ici par IP, peut être par user_id, API Key, etc.)
        rate_limit_key = f"rate_limit:{client_ip}:{request.url.path}" # Rate limit par IP et par endpoint

        # Obtenir la configuration spécifique pour ce chemin, ou utiliser les valeurs par défaut
        path_config = self.config_per_path.get(request.url.path, {
            "capacity": self.default_capacity,
            "window_seconds": self.default_window_seconds,
            "burst_capacity": self.default_burst
        })
        
        capacity = path_config.get("capacity", self.default_capacity)
        window = path_config.get("window_seconds", self.default_window_seconds)
        burst = path_config.get("burst_capacity", self.default_burst)

        if rate_limit_key not in rate_limiters:
            # Crée un limiteur pour cette combinaison clé/chemin
            rate_limiters[rate_limit_key] = SlidingWindowRateLimiter(capacity, window, burst)
            
        allowed, limit, remaining, reset_after = await rate_limiters[rate_limit_key].allow_request(rate_limit_key)

        response = Response()
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(reset_after) # Temps en secondes jusqu'au reset

        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                ip=client_ip,
                path=request.url.path,
                limit=limit,
                remaining=remaining,
                reset_after=reset_after
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests"
            )
        
        response = await call_next(request)
        
        # S'assure que les headers sont ajoutés même si la réponse vient d'un autre middleware
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining -1 )) # -1 car la requête actuelle a consommé une ressource
        response.headers["X-RateLimit-Reset"] = str(reset_after)

        return response
```

### Intégration dans `main.py`

```
# main.py
from fastapi import FastAPI
from app.middleware.rate_limiter import RateLimitingMiddleware
import os

app = FastAPI()

# Initialisation du client Redis pour le rate limiter
@app.on_event("startup")
async def startup_event():
    from app.middleware.rate_limiter import get_redis_client_instance
    await get_redis_client_instance() # Initialise le client Redis

# Enregistrement du middleware de Rate Limiting
app.add_middleware(
    RateLimitingMiddleware,
    default_capacity=100,
    default_window_seconds=60,
    default_burst=20,
    whitelist_ips=["127.0.0.1", "::1", os.getenv("KUBERNETES_HEALTH_CHECK_IP", "")], # Ajoutez les IPs de vos probes K8s
    config_per_path={
        "/api/v1/auth/login": {"capacity": 10, "window_seconds": 30, "burst_capacity": 5}, # Plus restrictif
        "/api/v1/ai/generate": {"capacity": 50, "window_seconds": 60, "burst_capacity": 10},
    }
)

# ... vos routes
```

#### Astuce non-évidente :

L'implémentation d'un `SlidingWindowRateLimiter` sans Redis (pour la démo) stocke les horodatages en mémoire. Pour un environnement distribué (Kubernetes), l'utilisation de Redis est impérative pour un état partagé et cohérent entre les instances de l'API. Le `burst_capacity` est une clé de performance : il permet à l'application d'absorber des pics de trafic courts au-dessus de la capacité normale, sans déclencher le limiteur, tant que le taux moyen sur la fenêtre reste dans les limites. La gestion du `X-RateLimit-Remaining` après le `call_next(request)` assure que la valeur renvoyée reflète l'état après la consommation de la requête actuelle.

#### Erreurs Courantes à Éviter :

* Utiliser une fenêtre fixe qui peut pénaliser les utilisateurs au début d'une nouvelle fenêtre (le *burst effect*).
* Ne pas fournir les en-têtes `X-RateLimit-*`, ce qui rend la limite invisible pour les clients.
* Ne pas gérer correctement le `Retry-After`, ou fournir une valeur imprécise.
* Définir des limites trop agressives qui bloquent des utilisateurs légitimes.
* Implémenter le rate limiting en mémoire dans un environnement distribué (Kubernetes), ce qui rend le limiteur inefficace.

#### Repo GitHub de Référence :

* [encode/starlette-limiter - GitHub](https://github.com/encode/starlette-limiter) (bien qu'il s'agisse d'un wrapper, il implémente ces concepts)

---

10. Dockerfile Multi-Stage Optimisé : Des Images Légères et Sécurisées
----------------------------------------------------------------------

Un Dockerfile multi-stage réduit la taille de l'image finale en séparant les dépendances de build du runtime. Cela améliore la sécurité, réduit les temps de pull et de déploiement, et diminue la surface d'attaque.

### Code Complet : `Dockerfile` et `.dockerignore`

```
# Dockerfile
# --- Stage 1: Builder ---
FROM python:3.13-slim-bookworm AS builder

# Définir l'utilisateur non-root pour la sécurité
ARG UID=10001
RUN adduser --disabled-password --gecos "" --home /app --uid "${UID}" appuser

WORKDIR /app

# Installer Poetry (ou pip-tools)
# Utiliser Poetry pour gérer les dépendances de manière déclarative
RUN pip install poetry==1.8.2

# Copier les fichiers de définition de dépendances Poetry
COPY pyproject.toml poetry.lock ./

# Configuration de Poetry pour créer un environnement virtuel dans le conteneur
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main --no-interaction --no-ansi

# Nettoyage des caches pip et Poetry
RUN rm -rf /root/.cache/pip /root/.cache/pypoetry


# --- Stage 2: Runtime ---
FROM python:3.13-slim-bookworm AS runtime

ARG UID=10001
RUN adduser --disabled-password --gecos "" --home /app --uid "${UID}" appuser

WORKDIR /app

# Copier les dépendances installées depuis le stage builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copier le code de l'application
COPY . /app

# Assurez-vous que l'utilisateur non-root est le propriétaire des fichiers de l'application
RUN chown -R appuser:appuser /app

# Définir l'utilisateur d'exécution
USER appuser

# Exposer le port de l'application
EXPOSE 8000

# Labels OCI (Open Container Initiative) standards
LABEL org.opencontainers.image.authors="votre_nom@votre_entreprise.com"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/votre_repo/votre_app"
LABEL org.opencontainers.image.description="FastAPI AI SaaS platform"
LABEL org.opencontainers.image.url="https://votre_entreprise.com"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.created=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
LABEL org.opencontainers.image.revision=$(git rev-parse HEAD)


# HEALTHCHECK instruction (voir section 5 pour des checks plus avancés)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/health/live || exit 1

# STOPSIGNAL pour un arrêt gracieux (voir section 4)
STOPSIGNAL SIGTERM

# Commande pour exécuter l'application
# Utilisez Uvicorn avec Gunicorn pour la production pour une meilleure gestion des processus
# Assurez-vous d'avoir Gunicorn installé dans vos dépendances Poetry
# CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
# Ou directement Uvicorn si vous n'avez pas Gunicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "info", "--graceful-timeout", "30"]
```

### Code Complet : `.dockerignore`

```
# .dockerignore
# Ignorer les fichiers Python compilés
*.pyc
*.pyo
__pycache__
.pytest_cache

# Ignorer les fichiers liés à l'environnement de développement
.env
.venv
venv/
.mypy_cache/
.vscode/
.idea/
*.sqlite3

# Ignorer les répertoires et fichiers Git
.git
.gitignore

# Ignorer les fichiers de logs
*.log
logs/

# Ignorer les fichiers de documentation, de tests (si non nécessaires au runtime)
docs/
tests/

# Ignorer les fichiers temporaires et de build
tmp/
dist/
build/
*.egg-info/
```

#### Astuce non-évidente :

L'utilisation de `poetry config virtualenvs.create false` dans le stage builder est cruciale pour que Poetry installe les dépendances directement dans l'environnement Python du conteneur (`/usr/local/lib/python3.13/site-packages`), ce qui les rend faciles à copier vers le stage runtime sans avoir à répliquer un environnement virtuel entier. L'argument `--no-root` lors de l'installation des dépendances Poetry évite d'installer le projet lui-même en mode éditable dans le builder, ce qui est généralement inutile pour le build d'une image Docker.

#### Erreurs Courantes à Éviter :

* Ne pas utiliser de Dockerfile multi-stage, résultant en des images Docker volumineuses.
* Exécuter le conteneur en tant que root, ce qui représente un risque de sécurité majeur.
* Ne pas utiliser `.dockerignore`, copiant des fichiers inutiles qui augmentent la taille de l'image.
* Ne pas optimiser l'ordre des instructions dans le Dockerfile, invalidant le cache Docker fréquemment.
* Oublier la commande `HEALTHCHECK` et `STOPSIGNAL` pour une bonne intégration Kubernetes.

#### Repo GitHub de Référence :

* [tiangolo/fastapi - GitHub](https://github.com/tiangolo/fastapi) (La documentation FastAPI a de bonnes sections sur Docker)

---

11. OpenTelemetry Integration : Traçabilité et Métriques Distribuées
--------------------------------------------------------------------

OpenTelemetry fournit un cadre standardisé pour instrumenter, générer, collecter et exporter des données de télémétrie (traces, métriques, logs). C'est un élément clé pour l'observabilité des systèmes distribués, permettant de comprendre le flux des requêtes à travers votre architecture.

### Code Python Complet : `app/observability/opentelemetry_config.py`

```
# app/observability/opentelemetry_config.py
import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    BatchSpanProcessor,
    SimpleSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
import structlog
from structlog.processors import JSONRenderer

logger = structlog.get_logger(__name__)

def configure_opentelemetry(app, service_name: str = "fastapi-ai-saas", environment: str = "development"):
    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": environment,
    })

    # --- Tracing ---
    provider = TracerProvider(resource=resource)
    
    if environment == "production":
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        span_processor = BatchSpanProcessor(span_exporter)
        logger.info("OpenTelemetry Tracing configured for OTLP export", endpoint=otlp_endpoint)
    else:
        span_exporter = ConsoleSpanExporter()
        span_processor = SimpleSpanProcessor(span_exporter)
        logger.info("OpenTelemetry Tracing configured for Console export (development mode)")

    provider.add_span_processor(span_processor)
    trace.set_tracer_provider(provider)

    # --- Metrics (example, more advanced setup typically involves custom metrics) ---
    # metrics_provider = MeterProvider(resource=resource)
    # if environment == "production":
    #     metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
    #     metrics_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
    #     logger.info("OpenTelemetry Metrics configured for OTLP export", endpoint=otlp_endpoint)
    # else:
    #     metric_exporter = ConsoleMetricExporter()
    #     metrics_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
    #     logger.info("OpenTelemetry Metrics configured for Console export (development mode)")
    # metrics_provider.add_metric_reader(metrics_reader)
    # set_meter_provider(metrics_provider)


    # --- Instrumentation ---
    # FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    logger.info("FastAPI Instrumented")

    # AsyncPG (pour PostgreSQL)
    AsyncPGInstrumentor().instrument()
    logger.info("AsyncPG Instrumented")

    # Redis
    RedisInstrumentor().instrument()
    logger.info("Redis Instrumented")

    # HTTPX (pour appels externes, ex: AI Providers)
    HTTPXClientInstrumentor().instrument()
    logger.info("HTTPX Instrumented")

    # --- Correlation avec Structlog ---
    # Pour injecter le trace_id et span_id d'OpenTelemetry dans les logs structlog
    # Créez un processor structlog pour cela.
    def add_otel_trace_info(logger, method_name, event_dict):
        current_span = trace.get_current_span()
        if current_span and current_span.get_span_context().is_valid:
            event_dict["trace_id"] = current_span.get_span_context().trace_id
            event_dict["span_id"] = current_span.get_span_context().span_id
        return event_dict
    
    # Ajoutez ce processor à la configuration de structlog
    # Assurez-vous qu'il est ajouté avant le JSONRenderer
    # Cette étape doit être faite dans la configuration de structlog, pas ici directement
    # car structlog.configure est appelé une seule fois.
    # Voir la section 7 pour l'intégration complète dans structlog_config.py
```

### Mise à jour de `app/logging_config.py` pour la corrélation

```
# app/logging_config.py (ajouts pour OpenTelemetry)
# ... (imports existants)
from opentelemetry import trace # Nouvel import

# Nouveau processor pour ajouter les IDs de trace OpenTelemetry
def add_otel_trace_info(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    current_span = trace.get_current_span()
    if current_span and current_span.get_span_context().is_valid:
        event_dict["otel.trace_id"] = format(current_span.get_span_context().trace_id, "032x") # Format hex
        event_dict["otel.span_id"] = format(current_span.get_span_context().span_id, "016x") # Format hex
    return event_dict

def configure_logging(json_logs: bool = False, log_level: str = "INFO"):
    """Configure structlog pour l'application FastAPI."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_user_id,
        add_request_duration,
        filter_sensitive_data,
        add_otel_trace_info, # AJOUTER CE PROCESSOR ICI
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    # ... (le reste de la fonction reste identique)
```

### Intégration dans `main.py`

```
# main.py
from fastapi import FastAPI
from app.observability.opentelemetry_config import configure_opentelemetry
from app.logging_config import configure_logging # Assurez-vous d'utiliser la version mise à jour
import os
import structlog

# Configurer structlog en premier
json_logs_enabled = os.getenv("ENVIRONMENT", "development") == "production"
log_level = os.getenv("LOG_LEVEL", "INFO")
configure_logging(json_logs=json_logs_enabled, log_level=log_level)

logger = structlog.get_logger(__name__)

app = FastAPI()

# Configurer OpenTelemetry après l'initialisation de FastAPI
environment = os.getenv("ENVIRONMENT", "development")
configure_opentelemetry(app, service_name="fastapi-ai-saas", environment=environment)

# ... (vos middlewares et routes)
```

#### Astuce non-évidente :

L'ordre d'initialisation est important : configurez `structlog` en premier, puis `OpenTelemetry`. Le processor `add_otel_trace_info` dans `structlog` doit être placé avant le `JSONRenderer` ou `ConsoleRenderer` pour que les IDs de trace et de span soient correctement ajoutés à l'`event_dict` avant le rendu final. Pour l'export OTLP, assurez-vous que votre collecteur OpenTelemetry est accessible et configuré pour recevoir les données sur le port par défaut (4317 pour gRPC).

#### Erreurs Courantes à Éviter :

* Oublier d'instrumenter une bibliothèque utilisée (ex: oubli de `RedisInstrumentor` si vous utilisez Redis).
* Ne pas configurer correctement l'exportateur (OTLP) en production, résultant en des traces qui ne sont pas envoyées.
* Des problèmes de corrélation (logs sans trace\_id) si le processor structlog est mal placé ou si les IDs ne sont pas correctement extraits.
* Surcharger l'application avec trop de métriques ou de traces si le niveau de détail n'est pas ajusté.

#### Repo GitHub de Référence :

* [open-telemetry/opentelemetry-python - GitHub](https://github.com/open-telemetry/opentelemetry-python)

---

12. Error Tracking (Sentry-like) : Capture Intelligente des Exceptions
----------------------------------------------------------------------

L'intégration d'un outil d'error tracking comme Sentry (ou une alternative open-source comme GlitchTip) est cruciale pour surveiller les erreurs en production. Il permet de détecter, de regrouper et de résoudre rapidement les problèmes, en fournissant un contexte détaillé de l'erreur.

### Code Python Complet : `app/error_tracking.py`

```
# app/error_tracking.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastAPIIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
import os
import structlog
from typing import Any, Dict

logger = structlog.get_logger(__name__)

def configure_sentry(app, dsn: Optional[str] = None, environment: str = "development", release: str = None):
    if not dsn:
        logger.info("Sentry DSN not provided, Sentry will not be initialized.")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        integrations=[
            FastAPIIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(), # Si Celery est dans le même processus ou bien configuré
        ],
        traces_sample_rate=1.0, # Ajustez le taux d'échantillonnage des traces en fonction de votre volume
        profiles_sample_rate=1.0, # Ajustez le taux d'échantillonnage des profils
        send_default_pii=True, # Envoyez les informations personnelles identifiables (PII) si nécessaire
        server_name_from_host=True, # Utilise le hostname comme nom de serveur
        max_breadcrumbs=50, # Nombre maximum de breadcrumbs à collecter
        attach_stacktrace=True, # Attacher une stacktrace complète aux événements
        # Filtrage de données sensibles (peut aussi être fait avec des Sentry.filters)
        # before_send=filter_sentry_event,
    )
    logger.info("Sentry initialized successfully.")

# Exemple de fonction pour ajouter du contexte utilisateur (à appeler après authentification)
def set_sentry_user_context(user_id: str, email: Optional[str] = None):
    sentry_sdk.set_user({"id": user_id, "email": email})

# Exemple de fonction pour ajouter un contexte global (ex: request_id)
def set_sentry_context(key: str, value: Any):
    sentry_sdk.set_context(key, value)

# Custom error handler for 500s (optional, Sentry handles most automatically)
async def custom_internal_server_error_handler(request, exc):
    # Sentry doit déjà avoir capturé l'erreur via l'intégration FastAPI
    # Vous pouvez ajouter ici une logique supplémentaire ou un rendu de page d'erreur personnalisé
    logger.error("Internal Server Error caught by custom handler", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred. Please try again later.", "request_id": request.headers.get("X-Request-ID")}
    )

# Fonction pour intégrer le request_id et user_id des contextvars structlog dans Sentry
def sentry_before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Tente de récupérer le request_id et user_id des contextvars de structlog
    # ou de l'état de la requête si cela a été bind par un middleware précédent
    request_id = structlog.contextvars.get_contextvars().get("request_id")
    user_id = structlog.contextvars.get_contextvars().get("user_id")

    if request_id:
        if "contexts" not in event:
            event["contexts"] = {}
        event["contexts"]["request"] = {"id": request_id} # Sentry convention pour request ID
    
    if user_id:
        if "user" not in event:
            event["user"] = {}
        event["user"]["id"] = user_id
    
    # Filtrer d'autres données sensibles avant d'envoyer à Sentry
    if "request" in event and "data" in event["request"]:
        if "password" in event["request"]["data"]:
            event["request"]["data"]["password"] = "[FILTERED]"
        if "token" in event["request"]["data"]:
            event["request"]["data"]["token"] = "[FILTERED]"
    
    return event
```

### Intégration dans `main.py`

```
# main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.error_tracking import configure_sentry, set_sentry_user_context, sentry_before_send, custom_internal_server_error_handler
import os
import sentry_sdk
import structlog
from sentry_sdk.integrations.logging import LoggingIntegration

logger = structlog.get_logger(__name__)
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Configure Sentry TÔT
    sentry_dsn = os.getenv("SENTRY_DSN")
    sentry_env = os.getenv("ENVIRONMENT", "development")
    app_version = os.getenv("APP_VERSION", "1.0.0")
    configure_sentry(app, dsn=sentry_dsn, environment=sentry_env, release=app_version)
    
    # Ajouter le processor sentry_before_send à Sentry
    if sentry_dsn:
        sentry_sdk.add_breadcrumb(
            category="startup",
            message="FastAPI application starting up",
            level="info",
        )
        sentry_sdk.flush() # S'assurer que le breadcrumb est envoyé si l'app crash juste après

    # Intégrer Sentry avec structlog (en envoyant les logs critiques à Sentry)
    # C'est une approche pour ne pas tout envoyer, mais plutôt les erreurs structlog
    # sentry_logging = LoggingIntegration(
    #     level=logging.INFO,        # Capture logs >= INFO
    #     event_level=logging.ERROR  # Envoie seulement ERROR et CRITICAL à Sentry en tant qu'événements
    # )
    # sentry_sdk.add_integration(sentry_logging) # Déjà fait dans configure_sentry via integrations=[...]


# Capture des exceptions non gérées
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Sentry captera les erreurs FastAPI/Starlette automatiquement avec FastAPIIntegration
    # Vous pouvez ajouter un logging structuré ici si nécessaire
    logger.warning("HTTP Exception", status_code=exc.status_code, detail=exc.detail, request_id=request.headers.get("X-Request-ID"))
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception):
    # Sentry captera cette exception automatiquement
    # Loggez l'erreur avec structlog avant de retourner la réponse d'erreur
    logger.error("Unhandled Exception", exc_info=True, request_id=request.headers.get("X-Request-ID"), error_message=str(exc))
    return await custom_internal_server_error_handler(request, exc)


# Exemple d'utilisation dans une route
@app.get("/trigger-error")
async def trigger_error():
    logger.info("Triggering a test error...")
    1 / 0 # Ceci déclenchera une ZeroDivisionError
```

#### Astuce non-évidente :

L'argument `before_send` dans `sentry_sdk.init` est un hook puissant pour manipuler l'événement Sentry avant qu'il ne soit envoyé. C'est l'endroit idéal pour injecter des informations contextuelles supplémentaires (comme le `request_id` ou le `user_id` provenant de `structlog.contextvars` ou `request.state`) et pour filtrer des données sensibles qui auraient pu échapper aux filtres par défaut de Sentry. Pensez également à utiliser `sentry_sdk.add_breadcrumb` pour enregistrer des étapes importantes du parcours utilisateur ou du traitement, ce qui aide à comprendre l'historique avant une erreur.

#### Erreurs Courantes à Éviter :

* Oublier de configurer le DSN (Data Source Name) de Sentry en production, désactivant de fait le tracking.
* Des taux d'échantillonnage des traces (`traces_sample_rate`) trop bas pour les environnements où vous avez besoin d'une visibilité complète.
* Ne pas intégrer les contextes importants (`request_id`, `user_id`) dans Sentry, rendant le débogage plus difficile.
* Ne pas utiliser `before_send` pour filtrer des données sensibles qui pourraient se retrouver dans les stack traces ou les variables locales.

#### Repo GitHub de Référence :

* [getsentry/sentry-python - GitHub](https://github.com/getsentry/sentry-python)

mindmap
root["Architecture FastAPI S+++ (2026)"]
Scalabilité
Database\_Pooling["Connection Pooling (asyncpg)"]
pool\_size["pool\_size, max\_overflow"]
pool\_recycle["pool\_recycle, pre\_ping"]
metrics\_pool["Metrics: active, idle, waiting"]
Rate\_Limiting["API Rate Limiting (Sliding Window)"]
headers\_ratelimit["X-RateLimit-\* Headers"]
burst\_allowance["Burst Allowance"]
whitelist\_ips["Whitelist IPs"]
Compression["Gzip/Brotli Compression"]
threshold\_size["Seuil de taille min"]
exclude\_endpoints["Exclusion SSE, /metrics"]
Sécurité
Security\_Headers["Security Headers Middleware"]
hsts["HSTS"]
csp["CSP"]
x\_options["X-Content-Type-Options, X-Frame-Options, X-XSS-Protection"]
referrer\_policy["Referrer-Policy"]
permissions\_policy["Permissions-Policy"]
JWT\_Auth["JWT Authentication"]
user\_id\_context["user\_id injection (structlog, Sentry)"]
Observabilité
Structured\_Logging["Structured Logging (structlog)"]
json\_output["JSON (prod), human-readable (dev)"]
request\_id\_log["Request ID automatique"]
user\_id\_log["User ID injection"]
timing\_perf["Performance Timing (duration)"]
sensitive\_filter["Sensitive Data Filtering"]
log\_levels["Log Levels par module"]
Request\_ID["Request/Correlation ID Middleware"]
uuid4\_generation["Génération UUID4"]
contextvars\_storage["Stockage contextvars"]
header\_propagation["X-Request-ID Header"]
celery\_propagation["Celery Task Propagation"]
OpenTelemetry\_Integration["OpenTelemetry (Traces & Metrics)"]
auto\_instrumentation["FastAPI, asyncpg, Redis, httpx"]
otlp\_exporter["OTLP Collector (prod)"]
trace\_log\_correlation["trace\_id/span\_id dans logs"]
Error\_Tracking["Error Tracking (Sentry-like)"]
auto\_capture\_500["Capture automatique 500"]
context\_enrichment["Contexte: user\_id, request\_id, module, endpoint"]
breadcrumbs["Breadcrumbs"]
sensitive\_data\_sentry["Filtrage données sensibles"]
Résilience
Graceful\_Shutdown["Arrêt Gracieux (FastAPI, Celery, asyncpg)"]
signal\_handling["Signal Handlers (SIGTERM, SIGINT)"]
drain\_http["Drain connexions HTTP"]
close\_pools["Fermeture pools asyncpg"]
celery\_warm\_shutdown["Celery Warm Shutdown"]
docker\_stopsignal["Docker STOPSIGNAL + grace\_period"]
Circuit\_Breaker["Circuit Breaker (AI Providers)"]
three\_states["Closed, Open, Half-Open"]
failure\_threshold["Seuil de défaillance configurable"]
fallback\_logic["Fallback automatique (autres providers)"]
metrics\_breaker["Metrics: circuit state, failure count"]
Health\_Checks["Health Checks Avancés (K8s-ready)"]
liveness\_probe["/health/live (app alive)"]
readiness\_probe["/health/ready (DB, Redis)"]
startup\_probe["/health/startup (migrations, modules chargés)"]

*Mindmap de l'architecture S+++ avec les composants clés et leurs interconnexions.*

Ce mindmap illustre l'interdépendance et le rôle de chaque composant architectural décrit dans ce guide. Il met en évidence comment les différentes couches (sécurité, observabilité, résilience, scalabilité) travaillent ensemble pour former une plateforme SaaS robuste et performante. La couleur des nœuds indique la catégorie générale d'amélioration, tandis que les sous-nœuds détaillent les fonctionnalités spécifiques.

---

FAQ (Foire Aux Questions)
-------------------------

Comment puis-je tester l'efficacité de ces middlewares ?

Pour tester l'efficacité des middlewares, utilisez des outils comme Postman ou curl pour vérifier les en-têtes de réponse (Security Headers, Rate Limiting, Correlation ID). Pour la compression, comparez la taille des réponses avec et sans le middleware. Pour le circuit breaker, simulez des défaillances des services tiers. Pour le logging et OpenTelemetry, examinez vos logs et vos traces dans votre système d'observabilité (ex: Grafana, Kibana, Jaeger). Des tests unitaires et d'intégration sont également essentiels pour valider la logique de chaque middleware.

Ces solutions sont-elles compatibles avec l'approche "modulaire" des 25 modules auto-découverts ?

Oui, absolument. Tous les middlewares et configurations proposés sont conçus pour être ajoutés à votre application FastAPI de manière modulaire, soit via `app.add_middleware()`, soit en incluant des routeurs spécifiques (pour les health checks), soit en configurant des initialisations au démarrage de l'application (lifespan, OpenTelemetry, Sentry). L'approche par `app.add_middleware()` ou `app.include_router()` assure que ces composants s'intègrent sans nécessiter de refactoring massif de vos modules existants.

Quel est l'impact de toutes ces améliorations sur les performances ?

Chaque amélioration ajoute une légère surcharge (overhead). Cependant, les bénéfices en termes de sécurité, de résilience et d'observabilité compensent largement cette surcharge. De plus, certaines améliorations (compression, connection pooling) sont des optimisations de performance directes. Il est crucial de surveiller les performances (avec Prometheus et OpenTelemetry) après chaque ajout pour identifier et optimifier les éventuels goulots d'étranglement. Un bon équilibre doit être trouvé entre la sécurité/robustesse et les performances pures.

Comment puis-je gérer les secrets (DSN Sentry, URL de base de données) de manière sécurisée ?

Utilisez des variables d'environnement (comme démontré avec `os.getenv()`) pour tous les secrets et configurations sensibles. En production, ces variables d'environnement doivent être injectées via votre orchestrateur (Kubernetes Secrets, Docker Compose secrets, HashiCorp Vault, AWS Secrets Manager, etc.). Ne jamais les commettre dans votre dépôt de code.

Y a-t-il une limite au nombre de middlewares que l'on peut ajouter ?

Techniquement, il n'y a pas de limite stricte. Cependant, chaque middleware ajoute une couche de traitement à chaque requête, augmentant la latence. Une bonne pratique est de n'ajouter que les middlewares absolument nécessaires et d'optimiser leur ordre d'exécution pour minimiser l'impact. Les middlewares qui nécessitent des informations "propres" (ex: pas encore compressées, pas encore routées) devraient venir en premier, tandis que ceux qui agissent sur la réponse finale (ex: compression, security headers) peuvent venir plus tard.

---

Conclusion
----------

La transformation de votre plateforme SaaS IA en une architecture S+++ de niveau entreprise est un voyage qui implique une attention minutieuse aux détails, une compréhension approfondie des meilleures pratiques et une implémentation rigoureuse. Les solutions fournies dans ce guide, couvrant la sécurité, la scalabilité, l'observabilité et la résilience, sont des étapes concrètes vers cet objectif. En adoptant ces patterns et en les adaptant à votre contexte spécifique, vous construirez une application FastAPI capable de gérer des charges élevées, de résister aux défaillances et de fournir une expérience utilisateur exceptionnelle, tout en restant facile à maintenir et à déboguer.

---

Recommandations
---------------

* [Optimisation des performances FastAPI avec Gunicorn et Uvicorn](/?query=Optimisation des performances FastAPI avec Gunicorn et Uvicorn)
* [Mise en place d'un pipeline CI/CD pour FastAPI avec Kubernetes](/?query=Mise en place d'un pipeline CI/CD pour FastAPI avec Kubernetes)
* [Sécurisation avancée des API FastAPI avec OAuth2 et JWT](/?query=Sécurisation avancée des API FastAPI avec OAuth2 et JWT)
* [Stratégies de monitoring et d'alerting pour FastAPI avec Prometheus et Grafana](/?query=Stratégies de monitoring et d'alerting pour FastAPI avec Prometheus et Grafana)

---

Résultats de recherche référencés
---------------------------------

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://gist.github.com)
gist.github.com

[Logging setup for FastAPI, Uvicorn and Structlog (with Datadog ... - Gist](https://gist.github.com/joshschmelzle/e44b4476261d3bc641ceda89aa29f00d)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://wazaari.dev)
wazaari.dev

[Integrating FastAPI with Structlog - Yet Another Techblog](https://wazaari.dev/blog/fastapi-structlog-integration)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://oneuptime.com)
oneuptime.com

[How to Add Structured Logging to FastAPI - OneUptime](https://oneuptime.com/blog/post/2026-02-02-fastapi-structured-logging/view)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://apitally.io)
apitally.io

[A complete guide to logging in FastAPI - Apitally Blog](https://apitally.io/blog/fastapi-logging-guide)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://github.com)
github.com

[snok/asgi-correlation-id: Request ID propagation for ASGI apps - GitHub](https://github.com/snok/asgi-correlation-id)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://ouassim.tech)
ouassim.tech

[Setting Up Structured Logging in FastAPI with structlog - Ouassim G.](https://ouassim.tech/notes/setting-up-structured-logging-in-fastapi-with-structlog/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://fastapi.tiangolo.com)
fastapi.tiangolo.com

[Advanced Middleware - FastAPI](https://fastapi.tiangolo.com/advanced/middleware/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://github.com)
github.com

[fullonic/brotli-asgi: A compression AGSI middleware using brotli. - GitHub](https://github.com/fullonic/brotli-asgi)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://oneuptime.com)
oneuptime.com

[How to Use Async Database Connections in FastAPI - OneUptime](https://oneuptime.com/blog/post/2026-02-02-fastapi-async-database/view)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://python.plainenglish.io)
python.plainenglish.io

[Database Connections in FastAPI: Best Practices for Efficient and ... - Plainenglish.io](https://python.plainenglish.io/database-connections-in-fastapi-best-practices-for-efficient-and-scalable-apis-eb0867ed9e7c)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://dba.stackexchange.com)
dba.stackexchange.com

[How to best use connection pooling in SQLAlchemy for PgBouncer ...](https://dba.stackexchange.com/questions/36828/how-to-best-use-connection-pooling-in-sqlalchemy-for-pgbouncer-transaction-level)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://davidmuraya.com)
davidmuraya.com

[A Practical Guide to FastAPI Security](https://davidmuraya.com/blog/fastapi-security-guide/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://gealber.com)
gealber.com

[Building a Brotli Middleware with FastAPI - Gealber el calvo lindo](https://gealber.com/building-brotli-middleware-fastapi)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://stackoverflow.com)
stackoverflow.com

[asyncpg/fastapi creating more connection than pool limit](https://stackoverflow.com/questions/69967439/asyncpg-fastapi-creating-more-connection-than-pool-limit)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://signoz.io)
signoz.io

[Complete Guide to Logging with StructLog in Python | SigNoz](https://signoz.io/guides/structlog/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://reddit.com)
reddit.com

[How to use a database connection pool effectively?[long \*\*\* post]](https://www.reddit.com/r/learnpython/comments/w5glaa/how_to_use_a_database_connection_pool/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://fastapi.tiangolo.com)
fastapi.tiangolo.com

[Concurrency and async / await - FastAPI](https://fastapi.tiangolo.com/async/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://fastapi.tiangolo.com)
fastapi.tiangolo.com

[Security - FastAPI](https://fastapi.tiangolo.com/tutorial/security/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://fastapi-guard.com)
fastapi-guard.com

[FastAPI Guard - Enterprise Security Middleware for FastAPI](https://fastapi-guard.com/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://asifmuhammad.com)
asifmuhammad.com

[Database Connection Pooling in FastAPI with SQLAlchemy](https://asifmuhammad.com/articles/database-pooling-fastapi)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://davidmuraya.com)
davidmuraya.com

[6 Essential FastAPI Middlewares for Production-Ready Apps](https://www.davidmuraya.com/blog/adding-middleware-to-fastapi-applications/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://gist.github.com)
gist.github.com

[Logging setup for FastAPI, Uvicorn and Structlog (with Datadog ...](https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://medium.com)
medium.com

[Securing Your FastAPI Application with Middleware: A Production-Ready Guide (Part 2) | by Sizan Mahmud | Medium](https://medium.com/@sizanmahmud08/securing-your-fastapi-application-with-middleware-a-production-ready-guide-part-2-8a6914f56e24)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://shiladityamajumder.medium.com)
shiladityamajumder.medium.com

[Async APIs with FastAPI: Patterns, Pitfalls & Best Practices](https://shiladityamajumder.medium.com/async-apis-with-fastapi-patterns-pitfalls-best-practices-2d72b2b66f25)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://propelauth.com)
propelauth.com

[FastAPI Auth with Dependency Injection | PropelAuth](https://www.propelauth.com/post/fastapi-auth-with-dependency-injection)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://medium.com)
medium.com

[Setting up request ID logging for your FastAPI application | Medium](https://medium.com/@sondrelg_12432/setting-up-request-id-logging-for-your-fastapi-application-4dc190aac0ea)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://angelospanag.me)
angelospanag.me

[Structured logging using structlog and FastAPI](https://www.angelospanag.me/blog/structured-logging-using-structlog-and-fastapi)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://ssojet.com)
ssojet.com

[Compress Files with gzip in FastAPI - SSOJet](https://ssojet.com/compression/compress-files-with-gzip-in-fastapi)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://medium.com)
medium.com

[FastAPI Best Practices: A Complete Guide for Building Production ...](https://medium.com/@abipoongodi1211/fastapi-best-practices-a-complete-guide-for-building-production-ready-apis-bb27062d7617)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://reddit.com)
reddit.com

[Enabling Gzip + Brotli gave me ~30–40% faster API responses : r/node](https://www.reddit.com/r/node/comments/1px3bog/enabling_gzip_brotli_gave_me_3040_faster_api/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://dev.to)
dev.to

[Asynchronous Database Sessions in FastAPI with SQLAlchemy](https://dev.to/akarshan/asynchronous-database-sessions-in-fastapi-with-sqlalchemy-1o7e)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://pysolutions.dev)
pysolutions.dev

[FastAPI Performance Deep Dive: Async vs Sync Operations for ...](https://pysolutions.dev/blog/fastapi-async-vs-sync-performance)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://blog.stackademic.com)
blog.stackademic.com

[A Deep Dive into Asynchronous Request Handling ... - Stackademic](https://blog.stackademic.com/a-deep-dive-into-asynchronous-request-handling-and-concurrency-patterns-in-fastapi-699393bb3845)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://github.com)
github.com

[How to maintain global pool of db connection and use it in each and ...](https://github.com/fastapi/fastapi/discussions/9097)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://dev.to)
dev.to

[Gzip Middleware recipe for FastAPI - DEV Community](https://dev.to/gealber/gzip-middleware-recipe-for-fastapi-4b14)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://linkedin.com)
linkedin.com

[Best Practices for Creating a FastAPI and PostgreSQL Connection](https://www.linkedin.com/pulse/best-practices-creating-fastapi-postgresql-connection-parasuraman-359uc)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://blog.danielclayton.co.uk)
blog.danielclayton.co.uk

[Psycopg Database Connections with FastAPI - Dan Clayton's Blog](https://blog.danielclayton.co.uk/posts/database-connections-with-fastapi/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://leapcell.io)
leapcell.io

[Building High-Performance Async APIs with FastAPI, SQLAlchemy ...](https://leapcell.io/blog/building-high-performance-async-apis-with-fastapi-sqlalchemy-2-0-and-asyncpg)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://oneuptime.com)
oneuptime.com

[How to Add Middleware to FastAPI - OneUptime](https://oneuptime.com/blog/post/2026-02-02-fastapi-middleware/view)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://pypi.org)
pypi.org

[fastapi-structlog · PyPI](https://pypi.org/project/fastapi-structlog/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://spwoodcock.dev)
spwoodcock.dev

[FastAPI, Pydantic, Psycopg3: The Ultimate Trio for Python Web APIs](https://spwoodcock.dev/blog/2024-10-fastapi-pydantic-psycopg/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://oneuptime.com)
oneuptime.com

[How to Implement Connection Pooling in Python for PostgreSQL](https://oneuptime.com/blog/post/2025-01-06-python-connection-pooling-postgresql/view)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://stackoverflow.com)
stackoverflow.com

[What is the good way to provide an authentication in FASTAPI? - Stack Overflow](https://stackoverflow.com/questions/61153498/what-is-the-good-way-to-provide-an-authentication-in-fastapi)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://structlog.org)
structlog.org

[Context Variables — structlog UNRELEASED documentation](https://www.structlog.org/en/latest/contextvars.html)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://github.com)
github.com

[How can I implement a Correlation ID middleware? · Issue #397 ...](https://github.com/fastapi/fastapi/issues/397)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://oneuptime.com)
oneuptime.com

[How to Configure Compression for APIs - OneUptime](https://oneuptime.com/blog/post/2026-01-24-configure-api-compression/view)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://weirdsheeplabs.com)
weirdsheeplabs.com

[Fast and furious: async testing with FastAPI and pytest](https://weirdsheeplabs.com/blog/fast-and-furious-async-testing-with-fastapi-and-pytest)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://pypi.org)
pypi.org

[structlog-config · PyPI](https://pypi.org/project/structlog-config/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://shipsafer.app)
shipsafer.app

[FastAPI Security Guide: Auth, Input Validation, and OWASP Best Practices — ShipSafer](https://www.shipsafer.app/blog/fastapi-security-guide)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://fastapi.tiangolo.com)
fastapi.tiangolo.com

[Security - First Steps - FastAPI](https://fastapi.tiangolo.com/tutorial/security/first-steps/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://medium.com)
medium.com

[FastAPI with AsyncPostgres: Lower Latency Through Native Drivers](https://medium.com/@bhagyarana80/fastapi-with-asyncpostgres-lower-latency-through-native-drivers-ca69ad941cb8)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://github.com)
github.com

[code-specialist/fastapi-auth-middleware - GitHub](https://github.com/code-specialist/fastapi-auth-middleware)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://reddit.com)
reddit.com

[Best approach for async SQLAlchemy in FastAPI - Reddit](https://www.reddit.com/r/FastAPI/comments/pi0zdy/best_approach_for_async_sqlalchemy_in_fastapi/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://dev.to)
dev.to

[Supercharge Your FastAPI Security with fastapi-guard! - DEV Community](https://dev.to/githubopensource/supercharge-your-fastapi-security-with-fastapi-guard-46b9)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://medium.com)
medium.com

[Building a Bulletproof FastAPI Middleware Stack: From ... - Medium](https://medium.com/@diwasb54/building-a-bulletproof-fastapi-middleware-stack-from-development-to-production-in-one-framework-36227c7cc5a3)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://medium.com)
medium.com

[How I Achieved Millisecond-Level Latency in FastAPI with HTTP/3 ...](https://medium.com/@bhagyarana80/how-i-achieved-millisecond-level-latency-in-fastapi-with-http-3-and-brotli-compression-c1f686cf5c42)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://oneuptime.com)
oneuptime.com

[How to Build Authentication Middleware in FastAPI](https://oneuptime.com/blog/post/2026-01-25-fastapi-authentication-middleware/view)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://medium.com)
medium.com

[Securing FastAPI: Implementing Token Authentication with Custom Middleware | by Chandan p | Medium](https://medium.com/@chandanp20k/leveraging-custom-middleware-in-python-fastapi-for-enhanced-web-development-09ba72b5ddc6)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://medium.com)
medium.com

[FastAPI + Brotli/Gzip Negotiation: Smaller Payloads, Faster APIs ...](https://medium.com/@hadiyolworld007/fastapi-brotli-gzip-negotiation-smaller-payloads-faster-apis-zero-client-changes-e648b2a1b0d5)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://auth0.com)
auth0.com

[Build and Secure a FastAPI Server with Auth0](https://auth0.com/blog/build-and-secure-fastapi-server-with-auth0/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://testdriven.io)
testdriven.io

[FastAPI with Async SQLAlchemy, SQLModel, and Alembic](https://testdriven.io/blog/fastapi-sqlmodel/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://medium.com)
medium.com

[Starlette With FastAPI - And Adding Correlation IDs for… - Medium](https://medium.com/@devendra631995/starlette-with-fastapi-understanding-the-foundation-and-adding-correlation-ids-for-179c5c65b2d1)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://reddit.com)
reddit.com

[r/Python on Reddit: FastAPI Guard - A FastAPI extension to secure your APIs](https://www.reddit.com/r/Python/comments/1ilhbkk/fastapi_guard_a_fastapi_extension_to_secure_your/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://escape.tech)
escape.tech

[How to secure APIs built with FastAPI: A complete guide](https://escape.tech/blog/how-to-secure-fastapi-api/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://linkedin.com)
linkedin.com

[Best Practices to Create Middleware in FastAPI - LinkedIn](https://www.linkedin.com/pulse/best-practices-create-middleware-fastapi-manikandan-parasuraman-smt8c)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://fastapi.tiangolo.com)
fastapi.tiangolo.com

[Middleware - FastAPI](https://fastapi.tiangolo.com/tutorial/middleware/)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://semaphore.io)
semaphore.io

[Building Custom Middleware in FastAPI - Semaphore](https://semaphore.io/blog/custom-middleware-fastapi)

![](https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://github.com)
github.com

[GitHub - rennf93/fastapi-guard: A security library for FastAPI that provides middleware to control IPs, log requests, and detect penetration attempts. It integrates seamlessly with FastAPI to offer robust protection against various security threats. · GitHub](https://github.com/rennf93/fastapi-guard)

Last updated March 24, 2026

---

## Source: Gemini - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md

Chemin d'origine: `C:\Users\ibzpc\Git\SaaS-IA\mvp\docs\Architecture_backend_FastAPI_SaaS_2026\Gemini - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md`

Guide d'Ingénierie de Haute Disponibilité pour Architectures SaaS IA sous FastAPI et Python 3.13 : Standards S+++ 2026
L'évolution fulgurante des services basés sur l'intelligence artificielle en 2026 a redéfini les exigences opérationnelles pour les plateformes SaaS de classe entreprise. Alors que les infrastructures traditionnelles se contentaient d'une disponibilité de trois neuf, les engagements contractuels modernes exigent une résilience S+++, capable de supporter des charges asynchrones massives tout en garantissant une sécurité proactive et une observabilité granulaire. L'adoption de Python 3.13, avec ses optimisations majeures pour la boucle d'événements asyncio et sa gestion mémoire affinée, offre le socle idéal pour ces systèmes. Ce rapport technique détaille douze piliers architecturaux essentiels, transformant une application standard en une forteresse numérique scalable et résiliente, conçue pour opérer sans interruption au sein d'environnements Kubernetes ou Docker Compose complexes.   

1. Middleware de Sécurité des En-têtes HTTP (Security Headers)
Le durcissement de la couche applicative commence par une politique stricte d'en-têtes de sécurité. En 2026, la simple protection contre l'injection ne suffit plus ; il s'agit d'empêcher l'exfiltration de données vers des domaines non autorisés et de limiter la surface d'attaque des navigateurs clients pour les interfaces d'IA générative. Une implémentation centralisée via un middleware FastAPI garantit que chaque réponse, sans exception, porte les garanties de sécurité requises par les audits SOC2 et ISO27001.   

Implémentation technique du middleware
Le code ci-dessous utilise une approche d'injection directe pour minimiser la latence de traitement des requêtes, en évitant les calculs de chaînes de caractères à la volée pour les politiques statiques.

Python
# app/middleware/security_headers.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware d'entreprise pour l'injection des en-têtes de sécurité OWASP 2026.
    Gère la protection contre le clickjacking, XSS, et les politiques de cache API.
    """
    def __init__(self, app, csp_policy: str = None):
        super().__init__(app)
        # Définition d'une CSP stricte par défaut
        self.csp = csp_policy or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://trusted.cdn.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "frame-ancestors 'none'; "
            "connect-src 'self' https://api.openai.com https://api.anthropic.com; "
            "upgrade-insecure-requests;"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)
        
        # En-têtes de transport et d'intégrité
        response.headers = "max-age=63072000; includeSubDomains; preload"
        response.headers = self.csp
        response.headers = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers = "1; mode=block"
        response.headers = "strict-origin-when-cross-origin"
        
        # Politique de permissions restreignant l'accès au matériel client
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "usb=(), bluetooth=(), payment=()"
        )
        
        # Désactivation du cache pour les endpoints API contenant des données PII/IA
        if "application/json" in response.headers.get("content-type", ""):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            
        return response
Configuration et intégration
Fichier cible : app/middleware/security_headers.py.
Ligne à ajouter dans main.py pour l'activation :
app.add_middleware(SecurityHeadersMiddleware)

En-tête	Valeur Recommandée	Objectif de Sécurité
HSTS	max-age=63072000	Empêche le déclassement SSL/TLS (Downgrade)
CSP	default-src 'self'	Bloque le chargement de scripts malveillants tiers
X-Frame-Options	DENY	Atténue les attaques par détournement de clic
Permissions-Policy	camera=()	Interdit l'accès silencieux aux périphériques
Le dépôt GitHub de référence est VolkanSah/Securing-FastAPI-Applications (>1000 stars), qui fournit des schémas de configuration exhaustifs pour les environnements de production. Une erreur fréquente consiste à appliquer une CSP trop permissive sur les environnements de développement, masquant ainsi des problèmes d'accès aux ressources tierces (comme les CDNs de documentation) qui ne se manifestent qu'en production. L'astuce non-évidente réside dans l'utilisation de Content-Security-Policy-Report-Only pendant les phases de migration pour identifier les blocages sans interrompre le service utilisateur.   

2. ID de Corrélation et Traçabilité End-to-End
Dans un système composé de 160 endpoints et de tâches Celery distribuées, isoler les logs relatifs à une seule transaction devient impossible sans un identifiant unique traversant toutes les couches. Le middleware de corrélation doit assurer la persistence de cet identifiant via contextvars, garantissant que chaque appel asynchrone ou tâche de fond reste lié à la requête originelle.   

Implémentation technique du Request ID
Python
# app/middleware/correlation.py
import uuid
from contextvars import ContextVar
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

# Variable globale pour le stockage du contexte de requête
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Réutilisation de l'ID entrant pour le chaînage inter-services
        correlation_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_var.set(correlation_id)
        
        # Liaison automatique avec structlog
        structlog.contextvars.bind_contextvars(request_id=correlation_id)
        
        try:
            response: Response = await call_next(request)
            response.headers = correlation_id
            return response
        finally:
            # Nettoyage du contexte pour éviter les fuites de variables
            request_id_var.reset(token)

# app/core/celery_utils.py
def inject_correlation_into_celery(task, args, kwargs):
    """Utilitaire pour passer l'ID aux tâches Celery via les headers."""
    rid = request_id_var.get()
    kwargs.setdefault("headers", {})["request_id"] = rid
    return task.apply_async(args=args, kwargs=kwargs)
Fichier cible : app/middleware/correlation.py.
Ligne à ajouter dans main.py :
app.add_middleware(CorrelationIdMiddleware)

Le dépôt de référence est snok/asgi-correlation-id. Une erreur commune est de ne pas réinitialiser la variable de contexte (request_id_var.reset(token)), ce qui peut corrompre les logs des requêtes suivantes sur le même thread worker dans des conditions de haute concurrence. L'astuce cruciale est d'utiliser le format W3C traceparent en complément de X-Request-ID pour assurer une compatibilité native avec les collecteurs OpenTelemetry.   

3. Optimisation de la Compression (Gzip et Brotli)
La réduction de la bande passante est un levier critique de performance, surtout pour les payloads JSON d'IA souvent verbeux. Si Gzip est universel, Brotli offre une compression 20% plus dense pour les fichiers textes à CPU constant. Il est impératif d'exclure les endpoints de streaming SSE (Server-Sent Events) pour éviter la mise en buffer qui détruirait l'expérience de "frappe en temps réel" des chatbots.   

Configuration du middleware de compression
Python
# app/middleware/compression.py
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from brotli_asgi import BrotliMiddleware

def setup_compression(app: FastAPI):
    # Brotli en priorité (si supporté par le client)
    app.add_middleware(
        BrotliMiddleware,
        quality=4,           # Compromis optimal vitesse/densité
        minimum_size=500,     # Pas de compression pour les petits paquets
        gzip_fallback=True
    )
    
    # Gzip en fallback pour compatibilité totale
    app.add_middleware(GZipMiddleware, minimum_size=500)

# Dans main.py, appliquer un filtrage sur les routes SSE et Metrics
# if request.url.path in ["/metrics", "/stream"]: skip compression
Le dépôt GitHub de référence est fullonic/brotli-asgi. Une erreur fréquente est de compresser des ressources déjà compressées (comme les images ou les fichiers .gz), ce qui augmente l'usage CPU sans gain de taille. L'astuce non-évidente consiste à désactiver la compression pour les requêtes provenant d'agents de monitoring internes (Prometheus), car ces derniers supportent souvent mal les en-têtes de transfert encodés et gèrent déjà la compression au niveau du collecteur.   

4. Gestion de l'Arrêt Progressif (Graceful Shutdown)
Dans un environnement Kubernetes, les pods sont éphémères. Un arrêt brutal sans drainage des connexions provoque des erreurs 502 chez les clients et des tâches Celery corrompues. Le pattern de "lifespan" de FastAPI 0.93+ est le standard pour orchestrer ce processus, couplé à une configuration Docker précise pour la transmission des signaux.   

Implémentation du pattern Lifespan
Python
# app/main.py
import asyncio
import signal
from contextlib import asynccontextmanager
from fastapi import FastAPI
import structlog
from app.db import database_pool

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Phase de démarrage
    await database_pool.connect()
    logger.info("service_started", status="healthy")
    yield
    # Phase d'arrêt (SIGTERM reçu)
    logger.info("shutdown_initiated", message="Draining connections...")
    
    # Marquer l'app comme non-prête pour K8s (readiness = 503)
    app.state.shutting_down = True
    
    # Attente pour finir le traitement des requêtes HTTP en cours (drainage)
    await asyncio.sleep(10) # Délai de sécurité avant fermeture ressources
    
    # Fermeture propre des pools
    await database_pool.disconnect()
    await asyncio.wait_for(database_pool.close(), timeout=15.0)
    
    logger.info("shutdown_complete")

app = FastAPI(lifespan=lifespan)
Configuration Docker :
STOPSIGNAL SIGTERM dans le Dockerfile.
stop_grace_period: 30s dans docker-compose.yml.

Le dépôt de référence est encode/uvicorn, qui définit les standards de gestion des signaux pour ASGI. Une erreur majeure est d'utiliser reload=True ou workers > 1 via uvicorn de manière directe sans passer par un gestionnaire de processus comme Gunicorn, car certains signaux ne sont pas propagés aux sous-processus, laissant des connexions SQL orphelines. L'astuce réside dans l'utilisation de exec dans l'entrypoint Docker pour que le processus Python remplace le shell et reçoive directement le signal SIGTERM.   

5. Sondes de Santé Avancées (Kubernetes-ready)
Les health checks ne doivent pas se limiter à un simple return 200. Ils doivent refléter l'état réel des dépendances critiques (PostgreSQL, Redis) et l'avancement du cycle de vie de l'application (migrations, chargement de modèles).   

Structure des endpoints de santé
Python
# app/api/health.py
from fastapi import APIRouter, Response, status
from app.db import db_check
from app.redis import redis_check

router = APIRouter(prefix="/health")

@router.get("/live")
async def liveness():
    """Vérifie que le processus n'est pas bloqué (boucle infinie)."""
    return {"status": "ok"}

@router.get("/ready")
async def readiness(response: Response):
    """Vérifie la connectivité aux bases de données."""
    db_ok = await db_check()
    redis_ok = await redis_check()
    
    if not (db_ok and redis_ok):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unready", "db": db_ok, "redis": redis_ok}
    return {"status": "ready"}

@router.get("/startup")
async def startup():
    """Vérifie que l'init est fini (migrations Alembic ok)."""
    # Logique de vérification de version de schéma DB
    return {"status": "started"}
Intégration Kubernetes :

YAML
livenessProbe:
  httpGet: { path: /health/live, port: 8000 }
readinessProbe:
  httpGet: { path: /health/ready, port: 8000 }
startupProbe:
  httpGet: { path: /health/startup, port: 8000 }
  failureThreshold: 30
  periodSeconds: 10
Le dépôt de référence est fastapi-healthchecks. Une erreur critique est d'inclure des vérifications de dépendances (DB/Redis) dans la sonde de liveness : si la base de données subit une latence passagère, Kubernetes redémarrera tous les pods, créant un "thundering herd effect" lors de la reconnexion massive. L'astuce consiste à faire échouer la sonde de readiness dès le début du signal de shutdown pour sortir prématurément du load balancer.   

6. Pooling de Connexions PostgreSQL avec AsyncPG
L'usage d'asyncpg permet des performances jusqu'à 3x supérieures à psycopg2 grâce à son protocole binaire natif. Cependant, un pool mal configuré peut saturer les ressources du serveur PostgreSQL en quelques secondes lors d'un pic de trafic.   

Configuration optimale du moteur asynchrone
Python
# app/db/session.py
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,               # Connexions maintenues ouvertes
    max_overflow=10,            # Surplus autorisé lors des pics
    pool_timeout=30,            # Temps max d'attente pour une connexion
    pool_recycle=1800,          # Ferme les connexions vieilles de 30min
    pool_pre_ping=True,         # Teste la connexion avant chaque usage
    connect_args={
        "command_timeout": 60,  # Évite les requêtes bloquantes infinies
        "server_settings": {
            "application_name": "saas_ia_prod"
        }
    }
)
La règle mathématique pour dimensionner le pool est la suivante :

pool_size≈ 
Nombre total d’instances
Nombre de vCPUs×2
​
 

.   

Le dépôt de référence est sqlalchemy/sqlalchemy (section asyncio). L'erreur classique est de ne pas limiter le max_overflow, ce qui peut amener le total des connexions à dépasser le paramètre max_connections de PostgreSQL (souvent fixé à 100 par défaut), bloquant ainsi l'accès même aux administrateurs via psql. L'astuce est d'utiliser max_queries=50000 au niveau d'asyncpg pour prévenir les fuites de mémoire potentielles sur les connexions de très longue durée.   

7. Journalisation Structurée pour la Production
La journalisation d'entreprise en 2026 doit être orientée vers l'agrégation de données (ELK, Datadog). Chaque log doit être un objet JSON riche, contenant l'identifiant utilisateur, le temps d'exécution et le module concerné, tout en masquant les informations sensibles (tokens, passwords).   

Configuration Structlog
Python
# app/core/logging.py
import structlog
import logging
import sys

def setup_logging(is_prod: bool = True):
    shared_processors =

    if is_prod:
        processors = shared_processors +
    else:
        processors = shared_processors +

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Utilisation dans un middleware pour injecter l'User ID
# user_id = decode_jwt(request.headers.get("Authorization")).get("sub")
# structlog.contextvars.bind_contextvars(user_id=user_id)
Le dépôt de référence est hynek/structlog. Une erreur fréquente est de laisser les logs d'accès d'Uvicorn dans leur format texte standard, ce qui rend l'analyse de trafic impossible dans un dashboard Grafana. L'astuce non-évidente est d'utiliser un processeur personnalisé pour supprimer sélectivement les clés password ou api_key de n'importe quel dictionnaire passé en log, garantissant la conformité RGPD par design.   

8. Circuit Breaker pour les Fournisseurs d'IA
Les appels aux APIs externes (OpenAI, Claude, Groq) sont par nature instables (timeouts, quotas dépassés). Un Circuit Breaker empêche l'application de s'effondrer en cascade en "ouvrant" le circuit dès qu'un seuil d'échec est atteint, redirigeant le trafic vers un fournisseur de secours.   

Implémentation du pattern Circuit Breaker
Python
# app/utils/resilience.py
import time
import asyncio
from enum import Enum

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.threshold = failure_threshold
        self.timeout = recovery_timeout

    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                return await self.fallback()

        try:
            result = await func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.reset()
            return result
        except Exception:
            self.handle_failure()
            raise

    def handle_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()

    async def fallback(self):
        # Logique de basculement vers Groq si Claude échoue
        return {"error": "Primary provider unavailable", "fallback": True}
Le dépôt de référence est YeonwooSung/fastapi-cb. Une erreur commune est de mettre un seuil trop bas (ex: 2 échecs), déclenchant le circuit sur des erreurs réseau passagères. L'astuce consiste à utiliser un Circuit Breaker par modèle d'IA et non par provider, car GPT-4 peut être indisponible alors que GPT-3.5 reste fonctionnel sur la même API.   

9. Rate Limiting par Fenêtre Glissante (Sliding Window)
Le rate limiting classique par fenêtre fixe (fixed window) permet des rafales de trafic aux frontières des fenêtres (ex: 100 requêtes à 59s et 100 à 01s). L'algorithme de fenêtre glissante, implémenté via Redis Sorted Sets, offre une équité totale en comptant exactement les requêtes sur les N dernières secondes.   

Script Lua pour Rate Limiting Atomique
Python
# app/core/rate_limit.py
import time
from app.redis import redis_client

async def is_rate_limited(user_id: str, limit: int, window: int) -> bool:
    now = time.time()
    key = f"ratelimit:{user_id}"
    
    # Script Lua pour garantir l'atomicité sans race conditions
    lua_script = """
    local key = KEYS
    local now = tonumber(ARGV)
    local window = tonumber(ARGV)
    local limit = tonumber(ARGV)
    
    redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
    local current_count = redis.call('ZCARD', key)
    
    if current_count < limit then
        redis.call('ZADD', key, now, now)
        redis.call('EXPIRE', key, window)
        return 0
    else
        return 1
    end
    """
    return await redis_client.eval(lua_script, 1, key, now, window, limit) == 1
Headers de réponse à inclure :
X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset.

Le dépôt de référence est laurentS/slowapi (>1000 stars) pour l'intégration FastAPI. Une erreur fréquente est de ne pas whitelister les IPs de l'infrastructure (K8s probes, Prometheus), ce qui finit par bloquer l'orchestrateur lui-même lors de périodes de forte charge. L'astuce consiste à renvoyer un en-tête Retry-After précis en secondes, calculé via le timestamp du plus vieil élément restant dans le Sorted Set Redis.   

10. Dockerfile Multi-Stage Haute Performance
Un Dockerfile d'entreprise en 2026 doit privilégier la sécurité (non-root) et la vitesse de build (usage de uv). La réduction de la taille de l'image de 1.5GB à <500MB diminue radicalement le temps de cold start lors d'un autoscaling Kubernetes.   

Structure du Dockerfile Optimisé
Dockerfile
# Stage 1: Builder
FROM python:3.13-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_HTTP_TIMEOUT=60
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock./
# Installation gelée pour garantir la reproductibilité
RUN uv sync --frozen --no-dev --no-install-project

# Stage 2: Runtime
FROM python:3.13-slim
LABEL org.opencontainers.image.source="https://github.com/org/saas-ia"
WORKDIR /app

# Sécurité : Création utilisateur sans privilèges
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY..
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health/live |

| exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--access-log"]
Le dépôt de référence est astral-sh/uv-docker-example. Une erreur majeure est d'inclure les outils de compilation (gcc, build-essential) dans l'image finale, augmentant inutilement la surface d'attaque. L'astuce réside dans l'utilisation de ENV UV_COMPILE_BYTECODE=1, qui pré-compile les fichiers .py en .pyc lors du build, accélérant le temps de démarrage du premier endpoint de 15%.   

11. Instrumentation OpenTelemetry Unifiée
L'observabilité moderne exige de corréler les traces (flux de requête) avec les métriques et les logs. L'intégration d'OpenTelemetry permet de visualiser les goulots d'étranglement dans les requêtes SQL complexes ou les temps de réponse des modèles d'IA.   

Setup de l'Instrumentation
Python
# app/core/telemetry.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def init_telemetry(app):
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    
    # Export vers Jaeger ou Tempo en production
    # provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="otel-collector:4317")))
    
    FastAPIInstrumentor.instrument_app(app)
    AsyncPGInstrumentor().instrument()
    RedisInstrumentor().instrument()
    # Instrumentation HTTPX pour les appels OpenAI/Claude
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    HTTPXClientInstrumentor().instrument()
Le dépôt de référence est open-telemetry/opentelemetry-python-contrib. Une erreur fréquente est d'instrumenter les endpoints de health check, ce qui pollue inutilement les systèmes de stockage de traces (Honeycomb/Datadog) avec des milliers de spans vides. L'astuce est d'injecter le trace_id dans chaque log structlog pour pouvoir passer d'un log d'erreur à la trace complète en un clic.   

12. Error Tracking et Observabilité des Exceptions
Le capture des erreurs 500 doit inclure l'état complet du système : variables locales, identifiant utilisateur et "breadcrumbs" (derniers événements avant le crash) pour permettre une résolution en moins de 15 minutes.   

Intégration Custom Tracker (Sentry-like)
Python
# app/core/errors.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastAPIIntegration
from app.core.config import settings

def setup_error_tracking():
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastAPIIntegration()],
        traces_sample_rate=0.1,        # 10% des traces en prod
        profiles_sample_rate=0.1,
        environment=settings.ENV,
        send_default_pii=False,        # Sécurité : pas de données perso par défaut
        before_send=strip_sensitive_data # Filtre custom
    )

def strip_sensitive_data(event, hint):
    # Suppression des headers Authorization des logs d'erreur
    if 'request' in event:
        event['request']['headers'].pop('authorization', None)
    return event
L'implémentation d'une architecture "Enterprise S+++" en 2026 repose sur la synergie de ces douze briques techniques. La robustesse ne provient pas d'un outil unique, mais de la capacité du système à absorber les chocs (Circuit Breaker), à informer sur son état (OTel/Health) et à se protéger intelligemment (Security Headers/Rate Limit). L'usage de Python 3.13 et de FastAPI 0.135 fournit le socle asynchrone nécessaire pour soutenir ces mécanismes sans sacrifier la vélocité de développement.   


github.com
zhanymkanov/fastapi-best-practices: FastAPI Best Practices ... - GitHub
S'ouvre dans une nouvelle fenêtre

reddit.com
When should you make a method async in FastAPI? - Reddit
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Set Up a FastAPI + PostgreSQL + Celery Stack with Docker Compose - OneUptime
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Build a Graceful Shutdown Handler in Python - OneUptime
S'ouvre dans une nouvelle fenêtre

pypi.org
fastapi-guard - PyPI
S'ouvre dans une nouvelle fenêtre

medium.com
FastAPI Security Headers That Don't Slow You Down | by Nexumo - Medium
S'ouvre dans une nouvelle fenêtre

github.com
mahdijafaridev/fastapi-middlewares - GitHub
S'ouvre dans une nouvelle fenêtre

github.com
VolkanSah/Securing-FastAPI-Applications - GitHub
S'ouvre dans une nouvelle fenêtre

medium.com
10 Advanced Logging Correlation (trace IDs) in Python | by Thinking ...
S'ouvre dans une nouvelle fenêtre

apitally.io
A complete guide to logging in FastAPI - Apitally Blog
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Add Structured Logging to FastAPI - OneUptime
S'ouvre dans une nouvelle fenêtre

github.com
snok/asgi-correlation-id: Request ID propagation for ASGI apps - GitHub
S'ouvre dans une nouvelle fenêtre

ouassim.tech
Setting Up Structured Logging in FastAPI with structlog - Ouassim G.
S'ouvre dans une nouvelle fenêtre

ssojet.com
Compress Files with brotli in FastAPI | Compression Algorithms in Programming - SSOJet
S'ouvre dans une nouvelle fenêtre

reddit.com
Enabling Gzip + Brotli gave me ~30–40% faster API responses : r/node - Reddit
S'ouvre dans une nouvelle fenêtre

fastapi.tiangolo.com
Server-Sent Events (SSE) - FastAPI
S'ouvre dans une nouvelle fenêtre

github.com
fullonic/brotli-asgi: A compression AGSI middleware using brotli. - GitHub
S'ouvre dans une nouvelle fenêtre

python.plainenglish.io
Essential Middlewares Every FastAPI Developer Should Know - Python in Plain English
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Implement Custom Middleware in FastAPI - OneUptime
S'ouvre dans une nouvelle fenêtre

github.com
How to gracefully stop FastAPI app ? #6912 - GitHub
S'ouvre dans une nouvelle fenêtre

fastapi.tiangolo.com
Lifespan Events - FastAPI
S'ouvre dans une nouvelle fenêtre

github.com
Do some stuff on SIGTERM *before* the app shuts down #11756 - GitHub
S'ouvre dans une nouvelle fenêtre

github.com
timeout-graceful-shutdown not behaving as expected · Kludex uvicorn · Discussion #2098
S'ouvre dans une nouvelle fenêtre

stackoverflow.com
docker-compose and graceful Celery shutdown - Stack Overflow
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Configure Kubernetes Liveness, Readiness, and Startup Probes - OneUptime
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Build Health Checks and Readiness Probes in Python for Kubernetes - OneUptime
S'ouvre dans une nouvelle fenêtre

socket.dev
fastapi-healthchecks - PyPI Package Security Analysis - Sock... - Socket.dev
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Use Async Database Connections in FastAPI - OneUptime
S'ouvre dans une nouvelle fenêtre

medium.com
FastAPI with AsyncPostgres: Lower Latency Through Native Drivers | by Bhagya Rana
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Implement Connection Pooling in Python for PostgreSQL - OneUptime
S'ouvre dans une nouvelle fenêtre

github.com
GitHub - litestar-org/litestar: Light, flexible and extensible ASGI framework | Built to scale
S'ouvre dans une nouvelle fenêtre

medium.com
Production-Grade Logging for FastAPI Applications: A Complete Guide - Medium
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Configure FastAPI Logging - OneUptime
S'ouvre dans une nouvelle fenêtre

github.com
YeonwooSung/fastapi-cb: Python implementation of the Circuit Breaker pattern - GitHub
S'ouvre dans une nouvelle fenêtre

aritro.in
FastAPI Resiliency: Circuit Breakers, Rate Limiting, and External API Management
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Implement Circuit Breakers in Python - OneUptime
S'ouvre dans une nouvelle fenêtre

reddit.com
Is Anyone Else Using FastAPI with AI Agents - Reddit
S'ouvre dans une nouvelle fenêtre

blog.stackademic.com
System Design (1) — Implementing the Circuit Breaker Pattern in FastAPI - Stackademic
S'ouvre dans une nouvelle fenêtre

redis.io
Build 5 Rate Limiters with Redis: Algorithm Comparison Guide
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Implement Sliding Window Rate Limiting in Python - OneUptime
S'ouvre dans une nouvelle fenêtre

github.com
rate limit · fastapi-practices fastapi-best-architecture · Discussion #70 - GitHub
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Implement Rate Limiting in FastAPI Without External Services - OneUptime
S'ouvre dans une nouvelle fenêtre

github.com
GitHub - rennf93/fastapi-guard: A security library for FastAPI that provides middleware to control IPs, log requests, and detect penetration attempts. It integrates seamlessly with FastAPI to offer robust protection against various security threats.
S'ouvre dans une nouvelle fenêtre

medium.com
FastAPI + Rate Limiting with Redis: Fair-Use APIs Without User Rage - Medium
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Implement Rate Limiting APIs Using Memorystore Redis with Lua Scripts
S'ouvre dans une nouvelle fenêtre

davidmuraya.com
Slimmer FastAPI Docker Images with Multi-Stage Builds - David Muraya
S'ouvre dans une nouvelle fenêtre

digon.io
Build Multistage Python Docker Images Using UV - Digon.IO
S'ouvre dans une nouvelle fenêtre

openobserve.ai
Monitoring Your FastAPI Application with OpenTelemetry and OpenObserve
S'ouvre dans une nouvelle fenêtre

docs.base14.io
Instrument FastAPI with OpenTelemetry - Traces, Metrics & Logs in 5 Min | base14 Scout
S'ouvre dans une nouvelle fenêtre

opentelemetry.io
Logs Auto-Instrumentation Example - Python - OpenTelemetry
S'ouvre dans une nouvelle fenêtre

pub.towardsai.net
FastAPI Observability Lab with Prometheus and Grafana: Complete Guide - Towards AI
S'ouvre dans une nouvelle fenêtre

oneuptime.com
How to Structure Logs Properly in Python with OpenTelemetry - OneUptime
S'ouvre dans une nouvelle fenêtre

gist.github.com
Logging setup for FastAPI, Uvicorn and Structlog (with Datadog integration) - GitHub Gist
S'ouvre dans une nouvelle fenêtre

github.com
DanielPopoola/fastapi-microservice-health-check - GitHub
S'ouvre dans une nouvelle fenêtre

reddit.com
FastAPI Guard - A FastAPI extension to secure your APIs : r/Python - Reddit
S'ouvre dans une nouvelle fenêtre

github.com
FastAPI framework, high performance, easy to learn, fast to code, ready for production - GitHu

---

## Source: Perplexity - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md

Chemin d'origine: `C:\Users\ibzpc\Git\SaaS-IA\mvp\docs\Architecture_backend_FastAPI_SaaS_2026\Perplexity - Architecture backend FastAPI SaaS – Enterprise S++ (2026).md`

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

---

## Source: ithy-article-fastapi-saas-architecture-s-plus-plus-plus-yr3917x2v5.html

Chemin d'origine: `C:\Users\ibzpc\Git\SaaS-IA\mvp\docs\Architecture_backend_FastAPI_SaaS_2026\ithy-article-fastapi-saas-architecture-s-plus-plus-plus-yr3917x2v5.html`

_Export HTML conserve tel quel en annexe brute._

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Élevez Votre FastAPI au Rang S+++ : Le Guide Ultime de l'Architecture Enterprise-Grade</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script defer id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<script defer type="module">import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({ startOnLoad: true });</script>
<style>
      body {
        max-width: 600px;
      }
      .canvas {
        margin-left: -20%;
      }
      .ask-more-box {
        display: none;
      }
      iframe {
        display: none;
      }

      .faq-question {
        color: black;
        margin: 10px;
        border-radius: 10px;
        padding: 10px 5px 10px 15px;
        font-size: 18px;
        border: 2px solid #388278;
      }
      .faq-answer {
        color: black;
        margin: 10px;
        margin-bottom: 20px;
        border-radius: 10px;
        padding :30px;
        border: 2px solid rgba(56,130,120,0.2)
      }
      /* Add RTL support styles */
      .rtl-support {
        direction: rtl !important;
        text-align: right !important;
      }

      img {
        max-width: 50% !important;
      }

      .rtl-support pre,
      .rtl-support code {
        direction: ltr !important;
        text-align: left !important;
      }
      
      /* RTL list styling */
      .rtl-support li {
        padding-right: 1.5em;
        padding-left: 0;
      }
      
      .rtl-support li:before {
        right: 0;
        left: auto;
      }

      .article-date {
        display: block;
        text-align: center;
        color: #aaa;
        margin: 64px auto;
      }

</style>
</head>
<body>

<div class="article-title-background" style="background-image: linear-gradient(rgba(26,28,31, 0.7), rgb(26, 28, 31) 80%), url('');">
<div class="article-title-container">
<h1 data-in-title-background="true" style="color: #fff">Élevez Votre FastAPI au Rang S+++ : Le Guide Ultime de l'Architecture Enterprise-Grade</h1>
<h3 data-in-title-background="true" style="color: #fff">Transformez votre plateforme SaaS IA avec FastAPI 0.135, Python 3.13, et des pratiques d'ingénierie logicielle de pointe pour une scalabilité, une sécurité et une observabilité inégalées.</h3><div class="source-box with-sources" onclick="popupPro()" style="width: fit-content; margin-bottom: 40px;"><div class="pro-label">PRO</div><div class="favicon-container"><img alt="" class="favicon" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://medium.com" style="z-index: 3;"/><img alt="" class="favicon" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://github.com" style="z-index: 2;"/><img alt="" class="favicon" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://oneuptime.com" style="z-index: 1;"/></div><div class="source-count">68+ Sources</div></div><div class="table-of-contents" data-in-title-background="true"><ol class="toc-list"><li><a class="toc-link" href="#heading-1"><span class="toc-number">1.</span><span class="toc-text">Points Saillants pour une Architecture S+++</span></a></li><li><a class="toc-link" href="#heading-2"><span class="toc-number">2.</span><span class="toc-text">1. Security Headers Middleware : Une Muraille Numérique pour Votre API</span></a></li><li><a class="toc-link" href="#heading-3"><span class="toc-number">3.</span><span class="toc-text">2. Request ID / Correlation ID Middleware : Tracer le Parcours de Chaque Requête</span></a></li><li><a class="toc-link" href="#heading-4"><span class="toc-number">4.</span><span class="toc-text">3. Gzip/Brotli Compression Middleware : Accélérer les Réponses API</span></a></li><li><a class="toc-link" href="#heading-5"><span class="toc-number">5.</span><span class="toc-text">4. Graceful Shutdown : Des Arrêts Propres pour une Disponibilité Continue</span></a></li><li><a class="toc-link" href="#heading-6"><span class="toc-number">6.</span><span class="toc-text">5. Health Checks Avancés (Kubernetes-ready) : Surveillance Intelligente</span></a></li><li><a class="toc-link" href="#heading-7"><span class="toc-number">7.</span><span class="toc-text">6. Database Connection Pooling : Optimisation des Accès PostgreSQL</span></a></li><li><a class="toc-link" href="#heading-8"><span class="toc-number">8.</span><span class="toc-text">7. Structured Logging Enterprise : Des Logs Clairs et Exploitables</span></a></li><li><a class="toc-link" href="#heading-9"><span class="toc-number">9.</span><span class="toc-text">8. Circuit Breaker pour AI Providers : Protéger Votre Application des Défaillances Externes</span></a></li><li><a class="toc-link" href="#heading-10"><span class="toc-number">10.</span><span class="toc-text">9. API Rate Limiting Avancé : Contrôle Granulaire du Trafic</span></a></li><li><a class="toc-link" href="#heading-11"><span class="toc-number">11.</span><span class="toc-text">10. Dockerfile Multi-Stage Optimisé : Des Images Légères et Sécurisées</span></a></li><li><a class="toc-link" href="#heading-12"><span class="toc-number">12.</span><span class="toc-text">11. OpenTelemetry Integration : Traçabilité et Métriques Distribuées</span></a></li><li><a class="toc-link" href="#heading-13"><span class="toc-number">13.</span><span class="toc-text">12. Error Tracking (Sentry-like) : Capture Intelligente des Exceptions</span></a></li><li><a class="toc-link" href="#heading-14"><span class="toc-number">14.</span><span class="toc-text">FAQ (Foire Aux Questions)</span></a></li><li><a class="toc-link" href="#heading-15"><span class="toc-number">15.</span><span class="toc-text">Conclusion</span></a></li><li><a class="toc-link" href="#heading-16"><span class="toc-number">16.</span><span class="toc-text">Recommandations</span></a></li><li><a class="toc-link" href="#heading-17"><span class="toc-number">17.</span><span class="toc-text">Résultats de recherche référencés</span></a></li></ol></div>
</div>
</div>
<div>
<p>En tant qu'expert en architecture backend Python pour les plateformes SaaS de qualité entreprise, je comprends l'importance de construire des systèmes non seulement fonctionnels mais aussi robustes, sécurisés, observables et résilients. Votre plateforme SaaS IA, avec FastAPI, Python 3.13, PostgreSQL, Redis, Celery et Docker Compose, est déjà sur une bonne voie. Mon objectif est de vous fournir les stratégies et le code exacts pour élever votre architecture au niveau "S+++".</p>
<hr/><h2 id="heading-1" style="color: #cc9900">Points Saillants pour une Architecture S+++</h2>
<ul style="background: rgba(56,130,120,0.1);padding: 30px 10%;border-radius: 8px;width: 80%; border-left: 4px solid #388278;">
<li><b>Sécurité Renforcée et Observabilité Détaillée :</b> Implémentez des middlewares de sécurité avancés et un système de logging structuré avec des IDs de corrélation, couplés à OpenTelemetry pour une traçabilité complète, afin d'assurer une défense robuste et une visibilité sans précédent sur le comportement de votre application.</li>
<li><b>Gestion Intelligente des Ressources et Résilience Accrue :</b> Optimisez la gestion des connexions à la base de données avec des pools sophistiqués et intégrez des patterns de disjoncteur pour vos appels à des services tiers, garantissant ainsi une performance stable et une meilleure tolérance aux pannes.</li>
<li><b>Déploiement Robuste et Efficace :</b> Utilisez des Dockerfiles multi-étapes pour des images légères et sécurisées, et mettez en œuvre un mécanisme d'arrêt gracieux pour des mises à jour sans interruption, assurant la continuité et l'efficacité de vos opérations en environnement conteneurisé.</li>
</ul>
<p>Chaque section ci-dessous détaille les implémentations spécifiques, le code, les références et les pièges à éviter pour atteindre cet objectif.</p>
<hr/><h2 id="heading-2" style="color: #cc9900">1. Security Headers Middleware : Une Muraille Numérique pour Votre API</h2>
<p>Les en-têtes de sécurité HTTP sont une première ligne de défense cruciale contre de nombreuses vulnérabilités web courantes. Ce middleware s'assure que chaque réponse de votre API inclut les directives de sécurité recommandées, protégeant vos utilisateurs et vos données.</p>
<h3 style="color: #388278">Code Python Complet : <code>app/middleware/security_headers.py</code></h3>
<pre><code>
# app/middleware/security_headers.py
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp,
                 hsts_max_age: int = 31536000,
                 csp_policy: str = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'",
                 permissions_policy: str = "camera=(), microphone=(), geolocation=()",
                 cache_control_api: str = "no-store, no-cache, must-revalidate, proxy-revalidate",
                 cache_control_static: str = "public, max-age=31536000, immutable"):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.csp_policy = csp_policy
        self.permissions_policy = permissions_policy
        self.cache_control_api = cache_control_api
        self.cache_control_static = cache_control_static

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Strict-Transport-Security (HSTS)
        response.headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains; preload"

        # Content-Security-Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # X-Content-Type-Options: nosniff
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: DENY
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: 1; mode=block
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: strict-origin-when-cross-origin
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy
        response.headers["Permissions-Policy"] = self.permissions_policy

        # Cache-Control for API endpoints vs. static assets
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = self.cache_control_api
        elif request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = self.cache_control_static

        return response
</code></pre>
<h3 style="color: #388278">Intégration dans <code>main.py</code></h3>
<pre><code>
# main.py
from fastapi import FastAPI
from app.middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI()

# Enregistrement du middleware
app.add_middleware(
    SecurityHeadersMiddleware,
    # Personnalisez les politiques si nécessaire
    csp_policy="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self' ws:",
    permissions_policy="camera=(), microphone=(), geolocation=(), clipboard-write=()",
    cache_control_api="no-store, no-cache, must-revalidate, proxy-revalidate",
    cache_control_static="public, max-age=31536000, immutable"
)

# ... vos autres routes et configurations
</code></pre>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>La directive <code>preload</code> dans HSTS indique aux navigateurs d'ajouter votre domaine à une liste de préchargement HSTS, garantissant que les futures visites seront toujours via HTTPS, même la première. Cela nécessite cependant que votre domaine soit approuvé et listé par le projet Chromium HSTS preload list. Pour les politiques de cache, assurez-vous que les en-têtes sont appropriés pour chaque type de ressource. Par exemple, les API ne devraient généralement pas être mises en cache par les clients, d'où <code>no-store</code>, tandis que les assets statiques peuvent avoir un cache long.</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Une CSP trop restrictive peut casser des fonctionnalités (ex: intégration avec des outils tiers, CDNs). Testez minutieusement.</li>
<li>Une CSP trop permissive est inefficace. Visez la spécificité.</li>
<li>Oublier de configurer <code>preload</code> pour HSTS ou de le renouveler après expiration.</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/fastapi/fastapi" target="_blank">tiangolo/fastapi - GitHub</a> (bien que les middlewares de sécurité soient souvent personnalisés, FastAPI lui-même est la base)</li>
</ul>
<hr/><h2 id="heading-3" style="color: #cc9900">2. Request ID / Correlation ID Middleware : Tracer le Parcours de Chaque Requête</h2>
<p>Le <i>correlation ID</i> est essentiel pour la traçabilité des requêtes à travers un système distribué. Il permet de lier tous les logs, les traces et les événements à une transaction unique, simplifiant le débogage et l'analyse des incidents.</p>
<h3 style="color: #388278">Code Python Complet : <code>app/middleware/correlation_id.py</code> et Intégration Structlog/Celery</h3>
<pre><code>
# app/middleware/correlation_id.py
import uuid
from contextvars import ContextVar
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

# ContextVar pour stocker le Request ID
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

def get_request_id() -&gt; Optional[str]:
    return request_id_var.get()

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Request-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        token = request_id_var.set(correlation_id) # Stocke l'ID dans le contextvars

        # Injecter dans structlog pour cette requête
        structlog.contextvars.bind_contextvars(request_id=correlation_id)

        response = await call_next(request)

        response.headers["X-Request-ID"] = correlation_id
        
        structlog.contextvars.unbind_contextvars("request_id") # Nettoyer
        request_id_var.reset(token) # Réinitialiser le contextvars

        return response

# Pour Celery: propagation du Request ID
# Dans votre task Celery, vous devrez extraire le request_id du header
# et le re-bind dans structlog.contextvars si vous voulez qu'il apparaisse dans les logs de Celery.
# Exemple dans une task:
# from celery import Celery
# from structlog.contextvars import bind_contextvars
#
# celery_app = Celery('my_app')
#
# @celery_app.task(bind=True)
# def my_celery_task(self, *args, **kwargs):
#     request_id = self.request.headers.get('X-Request-ID') # Assurez-vous que Celery transmet les headers
#     if request_id:
#         bind_contextvars(request_id=request_id)
#     # ... votre logique de tâche
</code></pre>
<h3 style="color: #388278">Intégration dans <code>main.py</code></h3>
<pre><code>
# main.py
from fastapi import FastAPI
from app.middleware.correlation_id import CorrelationIdMiddleware
import structlog
import structlog.contextvars

app = FastAPI()

# Assurez-vous que ce middleware est ajouté tôt dans la pile
app.add_middleware(CorrelationIdMiddleware)

# Configuration de structlog pour inclure request_id (détaillée plus loin)
# ...
</code></pre>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>L'utilisation de <code>contextvars</code> est cruciale en programmation asynchrone pour stocker des données contextuelles spécifiques à la requête sans les passer explicitement à chaque fonction. Pour Celery, la propagation du <code>request_id</code> nécessite de configurer votre broker (ex: RabbitMQ ou Redis) pour qu'il transmette les en-têtes personnalisés, puis de les récupérer et de les re-binder dans le contexte de la tâche Celery. Cela assure une traçabilité de bout en bout.</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Oublier de réinitialiser le <code>contextvars</code> après la requête, ce qui peut entraîner des fuites d'ID entre les requêtes.</li>
<li>Ne pas propager le <code>request_id</code> aux services en aval (microservices, bases de données, queues de messages), brisant ainsi la chaîne de traçabilité.</li>
<li>Ne pas configurer correctement Celery pour transmettre les en-têtes et les lier dans les workers.</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/snok/asgi-correlation-id" target="_blank">snok/asgi-correlation-id - GitHub</a></li>
</ul>
<hr/><h2 id="heading-4" style="color: #cc9900">3. Gzip/Brotli Compression Middleware : Accélérer les Réponses API</h2>
<p>La compression HTTP réduit la taille des données transférées, ce qui améliore la vitesse des requêtes et réduit la consommation de bande passante. Brotli offre généralement de meilleurs taux de compression que Gzip.</p>
<h3 style="color: #388278">Code Python Complet : <code>app/middleware/compression.py</code></h3>
<pre><code>
# app/middleware/compression.py
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import StreamingResponse
import brotli
import gzip
import io
import re

class SmartCompressionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, minimum_size: int = 500, exclude_paths: list[str] = None):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.exclude_paths = exclude_paths if exclude_paths is not None else []

    async def dispatch(self, request: Request, call_next):
        if any(re.match(pattern, request.url.path) for pattern in self.exclude_paths):
            return await call_next(request)

        response: Response = await call_next(request)

        if response.status_code &lt; 200 or response.status_code &gt;= 300:
            return response

        if not response.headers.get("content-type", "").startswith("application/json") and \
           not response.headers.get("content-type", "").startswith("text/"):
            return response
        
        if isinstance(response, StreamingResponse):
            return response

        response_body = b''
        async for chunk in response.body_iterator:
            response_body += chunk

        if len(response_body) &lt; self.minimum_size:
            # Si le corps est trop petit, ne pas compresser
            response.headers["Content-Length"] = str(len(response_body))
            return Response(content=response_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)

        accept_encoding = request.headers.get("Accept-Encoding", "")
        
        # Préférer Brotli si supporté
        if "br" in accept_encoding and brotli:
            compressed_body = brotli.compress(response_body)
            response.headers["Content-Encoding"] = "br"
        elif "gzip" in accept_encoding:
            compressed_body = gzip.compress(response_body)
            response.headers["Content-Encoding"] = "gzip"
        else:
            response.headers["Content-Length"] = str(len(response_body))
            return Response(content=response_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)

        response.headers["Content-Length"] = str(len(compressed_body))
        # Supprime l'en-tête ETag original car le contenu compressé est différent
        if "ETag" in response.headers:
            del response.headers["ETag"]
        return Response(content=compressed_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)

</code></pre>
<h3 style="color: #388278">Intégration dans <code>main.py</code></h3>
<pre><code>
# main.py
from fastapi import FastAPI
from app.middleware.compression import SmartCompressionMiddleware

app = FastAPI()

# Enregistrement du middleware de compression
app.add_middleware(
    SmartCompressionMiddleware,
    minimum_size=500,  # Compresser seulement si la taille est &gt;= 500 octets
    exclude_paths=[
        "/metrics",        # Exclure les métriques Prometheus
        "/sse.*",          # Exclure les endpoints SSE (streaming)
        "/health/.*"       # Exclure les health checks
    ]
)

# ... vos autres routes
</code></pre>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>L'ordre des middlewares est important. Le middleware de compression doit se situer après tout middleware qui pourrait modifier le corps de la réponse, mais avant les middlewares qui pourraient avoir besoin du corps final (non compressé) pour leur logique (ex: logging de la taille réelle du body). La vérification de <code>brotli</code> en tant que module est importante car il n'est pas toujours installé par défaut. S'assurer d'exclure les endpoints de streaming (SSE) et les métriques (Prometheus) est crucial pour éviter des comportements inattendus ou des performances dégradées.</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Compresser des fichiers déjà compressés (images, vidéos) ce qui peut augmenter la taille au lieu de la réduire.</li>
<li>Compresser des très petits fichiers où le coût de la compression/décompression dépasse le gain en bande passante.</li>
<li>Ne pas exclure les endpoints de streaming ou les métriques, entraînant des problèmes.</li>
<li>Oublier de supprimer l'en-tête ETag après compression, ce qui peut induire les caches en erreur.</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/fullonic/brotli-asgi" target="_blank">fullonic/brotli-asgi - GitHub</a></li>
</ul>
<hr/><h2 id="heading-5" style="color: #cc9900">4. Graceful Shutdown : Des Arrêts Propres pour une Disponibilité Continue</h2>
<p>Un arrêt gracieux permet à une application de terminer les tâches en cours et de libérer les ressources avant de s'arrêter complètement, minimisant ainsi les interruptions de service et la perte de données.</p>
<h3 style="color: #388278">Code Python Complet : <code>app/lifespan.py</code> et Config Docker</h3>
<pre><code>
# app/lifespan.py
import asyncio
import signal
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
import asyncpg.pool
import structlog
from celery import Celery

logger = structlog.get_logger(__name__)

# Simule un pool asyncpg
# Remplacez par votre instance réelle de pool asyncpg
# from app.db.connection import database_pool_manager (exemple)
class MockAsyncpgPool:
    def __init__(self):
        self.connections = 0
        self.is_closed = False
    
    async def connect(self):
        self.connections += 1
        logger.info("Database connection opened", current_connections=self.connections)
    
    async def close(self):
        self.connections -= 1
        logger.info("Database connection closed", current_connections=self.connections)

    async def terminate(self):
        self.is_closed = True
        logger.info("Asyncpg pool terminated")

# Remplacez par l'initialisation de votre app Celery
celery_app = Celery('my_app') 

@asynccontextmanager
async def lifespan(app: FastAPI) -&gt; AsyncGenerator[None, None]:
    logger.info("FastAPI application startup")

    # ----- Initialisation des ressources -----
    # Exemple: Connexion à la base de données
    # Supposons que votre pool est géré globalement ou via une classe Singleton
    app.state.db_pool = MockAsyncpgPool() # Remplacez par votre pool réel
    logger.info("Database pool initialized")

    # ----- Gestion des signaux pour l'arrêt gracieux -----
    shutdown_event = asyncio.Event()

    def handle_signal():
        logger.info("Shutdown signal received, initiating graceful shutdown...")
        shutdown_event.set()

    # Capture SIGTERM et SIGINT (Ctrl+C)
    # Note: Uvicorn gère déjà SIGTERM/SIGINT de base pour son propre processus
    # Ceci est plus pour des logiques d'arrêt spécifiques à l'application
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, handle_signal)
    loop.add_signal_handler(signal.SIGINT, handle_signal)
    
    # Démarrage des workers Celery (si non démarrés séparément)
    # Si Celery est un service distinct, cette partie n'est pas nécessaire ici
    # Si vous voulez un warm shutdown, Celery doit être configuré pour cela.
    # celery_app.control.enable_events() # Pour surveiller les tâches
    # logger.info("Celery worker events enabled")

    yield

    # ----- Nettoyage des ressources lors de l'arrêt -----
    logger.info("FastAPI application shutdown initiated")

    # Attendre que toutes les requêtes HTTP en cours soient terminées (max 30s)
    # Uvicorn gère cela en interne via son &lt;code&gt;graceful_timeout</code>.
    # Pour une logique plus fine, vous pourriez utiliser des compteurs de requêtes actives.
    # await shutdown_event.wait() # Si vous voulez attendre un signal explicite

    # Fermeture propre du pool asyncpg
    if hasattr(app.state, 'db_pool') and app.state.db_pool:
        logger.info("Closing database pool...")
        await app.state.db_pool.terminate()
        logger.info("Database pool closed")

    # Celery worker: warm shutdown
    # Si Celery est géré par un autre processus (ex: en dehors de FastAPI),
    # il doit avoir sa propre logique de warm shutdown.
    # Exemple de commande pour un warm shutdown de Celery:
    # celery -A proj worker -P solo -c 1 --loglevel=info --pool=solo --time-limit=30 --max-tasks-per-child=1 --max-memory-per-child=1000 --shutdown-when-finished
    # Pour déclencher un shutdown via l'application FastAPI, cela dépend de votre architecture.
    # Souvent, Celery workers reçoivent un SIGTERM directement de Kubernetes/Docker.
    # Pour une approche in-app si Celery tourne avec FastAPI, vous pouvez simuler
    # un warm shutdown pour les tâches en cours si vous les gérez.
    # logger.info("Initiating warm shutdown for Celery workers (if running within this process)...")
    # celery_app.control.broadcast('shutdown', destination=[]) # Cela envoie un signal de shutdown
    #                                                       # mais les tâches en cours peuvent finir.
    # asyncio.sleep(5) # Attendre un peu pour que les messages soient traités
    logger.info("FastAPI application shutdown complete")

</pre>
<h3 style="color: #388278">Intégration dans <code>main.py</code></h3>
<pre><code>
# main.py
from fastapi import FastAPI
from app.lifespan import lifespan # Importer votre fonction lifespan

app = FastAPI(lifespan=lifespan)

# ... vos routes
</code></pre>
<h3 style="color: #388278">Configuration Docker</h3>
<pre><code>
# Dockerfile
# ... votre Dockerfile optimisé (voir section 10)
STOPSIGNAL SIGTERM
# Pour Uvicorn, le paramètre --graceful-timeout gère le temps d'attente
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--graceful-timeout", "30"]

# docker-compose.yml
services:
  fastapi_app:
    build: .
    ports:
      - "8000:8000"
    stop_signal: SIGTERM
    stop_grace_period: 30s # Donne 30 secondes au conteneur pour s'arrêter
  celery_worker:
    build: .
    command: celery -A app.celery_worker.celery_app worker -P gevent -c 1 --loglevel=info --time-limit=300 --max-tasks-per-child=1 # Exemple de commande
    stop_signal: SIGTERM
    stop_grace_period: 60s # Plus long pour Celery car les tâches peuvent être longues
</code></pre>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>Pour Celery, un "warm shutdown" signifie que le worker arrête d'accepter de nouvelles tâches, mais termine celles qui sont déjà en cours. La commande <code>celery multi stop --wait</code> ou l'envoi d'un <code>SIGTERM</code> au worker Celery permet cette approche. Le <code>--time-limit</code> et <code>--max-tasks-per-child</code> de Celery sont également cruciaux pour éviter que des tâches individuelles ne bloquent le shutdown. Dans Docker Compose et Kubernetes, <code>stop_grace_period</code> et le <code>STOPSIGNAL</code> travaillent ensemble pour permettre un arrêt en douceur.</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Ne pas libérer les ressources ouvertes (connexions DB, fichiers, etc.) lors du shutdown.</li>
<li>Dépendre uniquement du <code>SIGKILL</code> par défaut, qui coupe brutalement l'application.</li>
<li>Ne pas donner suffisamment de temps aux workers Celery pour terminer leurs tâches.</li>
<li>Oublier de configurer le <code>graceful-timeout</code> d'Uvicorn pour FastAPI.</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/fastapi/fastapi" target="_blank">tiangolo/fastapi - GitHub</a> (pour le <code>lifespan</code>)</li>
</ul>
<hr/><h2 id="heading-6" style="color: #cc9900">5. Health Checks Avancés (Kubernetes-ready) : Surveillance Intelligente</h2>
<p>Les probes Kubernetes (liveness, readiness, startup) sont fondamentales pour une gestion efficace des pods. Des checks avancés garantissent que l'état rapporté reflète précisément la capacité du service à fonctionner.</p>
<h3 style="color: #388278">Code Python Complet : <code>app/routers/health.py</code></h3>
<pre><code>
# app/routers/health.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import asyncpg
import redis.asyncio as redis
import os
import asyncio
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)

# Dépendances pour les checks de connectivité (mock pour l'exemple)
# Remplacez par vos fonctions de connexion réelles
async def get_db_pool():
    # Ici, vous retournerez votre pool de connexion asyncpg réel
    class MockDBPool:
        async def fetchval(self, query):
            # Simule une requête simple à la DB
            await asyncio.sleep(0.01)
            return 1
    return MockDBPool()

async def get_redis_client():
    # Ici, vous retournerez votre client Redis réel
    class MockRedisClient:
        async def ping(self):
            await asyncio.sleep(0.01)
            return True
    return MockRedisClient()


@router.get("/health/live", summary="Liveness Probe", status_code=status.HTTP_200_OK)
async def liveness_probe() -&gt; Dict[str, str]:
    """
    Indique si l'application est en cours d'exécution.
    Ne devrait échouer qu'en cas de crash majeur (ex: blocage de l'event loop).
    """
    return {"status": "alive"}

@router.get("/health/ready", summary="Readiness Probe", status_code=status.HTTP_200_OK)
async def readiness_probe(
    db_pool: object = Depends(get_db_pool), # Typez avec votre pool réel (ex: asyncpg.pool.Pool)
    redis_client: object = Depends(get_redis_client) # Typez avec votre client réel (ex: redis.asyncio.Redis)
) -&gt; Dict[str, str]:
    """
    Indique si l'application est prête à servir des requêtes.
    Vérifie les dépendances critiques (DB, Redis).
    """
    checks = {}
    try:
        # Check PostgreSQL
        # Exemple: exécutez une requête légère
        await db_pool.fetchval("SELECT 1")
        checks["postgresql"] = "ok"
    except Exception as e:
        logger.error("Readiness check failed: PostgreSQL", error=str(e))
        checks["postgresql"] = f"failed: {e}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="PostgreSQL unavailable")

    try:
        # Check Redis
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        logger.error("Readiness check failed: Redis", error=str(e))
        checks["redis"] = f"failed: {e}"
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis unavailable")

    return {"status": "ready", "dependencies": checks}

@router.get("/health/startup", summary="Startup Probe", status_code=status.HTTP_200_OK)
async def startup_probe() -&gt; Dict[str, str]:
    """
    Indique si l'application a terminé son initialisation coûteuse (migrations, chargement modules).
    """
    # Exemple: Vérifier l'état d'une variable globale ou d'un fichier de lock
    # qui indique que les migrations ont été appliquées et que les modules sont chargés.
    # Dans un environnement réel, cela pourrait impliquer:
    # - La vérification de la version de la base de données après migrations
    # - La confirmation du chargement de modèles ML ou de configurations complexes
    
    # Placeholder: Implémentez votre logique réelle ici
    # Par exemple, si vous avez un flag global &lt;code&gt;app.state.startup_complete = True</code>
    if not os.path.exists("/tmp/app_startup_complete"): # Exemple de flag via fichier
         raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Application still starting up")
    
    # Simulate async operations
    await asyncio.sleep(0.1) 
    
    return {"status": "startup_complete"}

</pre>
<h3 style="color: #388278">Intégration dans <code>main.py</code></h3>
<pre><code>
# main.py
from fastapi import FastAPI
from app.routers import health

app = FastAPI()

app.include_router(health.router)

# Pour la startup probe, vous devrez signaler la complétion après vos initialisations
# Par exemple, dans votre fonction lifespan ou après les migrations
@app.on_event("startup")
async def app_startup_event():
    # Exemple: exécuter les migrations ici ou charger des modules lourds
    # await run_migrations()
    # await load_ml_models()
    # Une fois tout terminé:
    with open("/tmp/app_startup_complete", "w") as f:
        f.write("ready")
    print("Application startup process complete.") # Output pour debug
</code></pre>
<h3 style="color: #388278">Configuration Docker/K8s</h3>
<pre><code>
# Dockerfile
# Ajoutez une instruction HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/health/live || exit 1
</code></pre>
<pre><code>
# Kubernetes Deployment YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-fastapi-app
spec:
  # ...
  template:
    # ...
    spec:
      containers:
      - name: fastapi-container
        image: my-fastapi-image:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 15 # Démarrer la vérification après 15s
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 30 # Démarrer la vérification après 30s
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        startupProbe:
          httpGet:
            path: /health/startup
            port: 8000
          initialDelaySeconds: 0
          periodSeconds: 5
          failureThreshold: 20 # Permettre 20 * 5 = 100 secondes pour le démarrage
          timeoutSeconds: 5
</code></pre>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>Pour la <code>startupProbe</code>, l'utilisation d'un fichier temporaire (comme <code>/tmp/app_startup_complete</code>) est une méthode simple pour signaler la complétion. Dans des environnements plus complexes, vous pourriez utiliser une entrée Redis ou une petite table dans PostgreSQL pour stocker l'état de démarrage. Il est crucial d'ajuster <code>initialDelaySeconds</code> et <code>failureThreshold</code> pour donner à votre application suffisamment de temps pour démarrer, surtout si des migrations ou des chargements de données sont longs.</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Utiliser le même endpoint pour toutes les probes (<code>/health</code> qui renvoie toujours 200).</li>
<li>Des checks trop longs ou coûteux dans les probes de liveness/readiness, qui peuvent bloquer l'application.</li>
<li>Des seuils de <code>failureThreshold</code> trop bas pour la <code>startupProbe</code>, ce qui peut tuer l'application avant qu'elle n'ait eu le temps de démarrer.</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/kubernetes/kubernetes" target="_blank">kubernetes/kubernetes - GitHub</a> (pour les concepts de probes)</li>
</ul>
<hr/><h2 id="heading-7" style="color: #cc9900">6. Database Connection Pooling : Optimisation des Accès PostgreSQL</h2>
<p>Le <i>connection pooling</i> est une technique essentielle pour gérer les connexions à la base de données. Il permet de réutiliser des connexions existantes plutôt que d'en ouvrir et d'en fermer de nouvelles à chaque requête, ce qui réduit considérablement la latence et la charge sur le serveur de base de données.</p>
<h3 style="color: #388278">Code Python Complet : <code>app/db/connection.py</code></h3>
<pre><code>
# app/db/connection.py
import asyncpg
import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool # Pour les tests, utilisez NullPool
import structlog

logger = structlog.get_logger(__name__)

class DatabasePoolManager:
    _instance: Optional[asyncpg.pool.Pool] = None
    _engine = None
    _session_factory = None

    @classmethod
    async def initialize(
        cls,
        db_url: str,
        pool_min_size: int = 5,
        pool_max_size: int = 20,
        pool_timeout: int = 60, # seconds to wait for a connection from the pool
        pool_recycle: int = 3600, # seconds after which a connection is recycled
        max_overflow: int = 10, # additional connections to create beyond max_size
        connect_attempts: int = 5, # number of retry attempts
        retry_delay_base: int = 1, # base delay for exponential backoff
    ):
        if cls._instance is not None:
            return

        for attempt in range(connect_attempts):
            try:
                # Configuration pour asyncpg
                cls._instance = await asyncpg.create_pool(
                    db_url,
                    min_size=pool_min_size,
                    max_size=pool_max_size,
                    timeout=pool_timeout,
                    max_inactive_connection_lifetime=pool_recycle, # Equivalent de pool_recycle pour asyncpg
                    # Optionnel: 'setup' peut exécuter des commandes après chaque connexion
                    # setup=lambda conn: conn.set_type_codec(...)
                )
                logger.info("Database pool initialized successfully with asyncpg")

                # Configuration pour SQLAlchemy 2.0 Async
                # 'postgresql+asyncpg' indique d'utiliser asyncpg comme driver
                cls._engine = create_async_engine(
                    db_url,
                    pool_size=pool_min_size, # Taille initiale du pool SQLAlchemy
                    max_overflow=max_overflow, # Connexions additionnelles pour SQLAlchemy
                    pool_timeout=pool_timeout, # Timeout pour obtenir une connexion
                    pool_recycle=pool_recycle, # Recycler les connexions après cette durée
                    pool_pre_ping=True, # Vérifie la viabilité de la connexion avant usage
                    echo=False, # Mettre à True pour afficher les requêtes SQL
                    future=True
                )
                cls._session_factory = async_sessionmaker(
                    cls._engine, 
                    expire_on_commit=False, 
                    class_=AsyncSession
                )
                logger.info("SQLAlchemy Async Engine and Session Factory initialized successfully")
                return

            except asyncpg.exceptions.PostgresError as e:
                logger.warning(
                    f"Failed to connect to database (attempt {attempt + 1}/{connect_attempts}): {e}",
                    delay=retry_delay_base * (2 ** attempt)
                )
                if attempt &lt; connect_attempts - 1:
                    await asyncio.sleep(retry_delay_base * (2 ** attempt))
                else:
                    logger.error("All database connection attempts failed. Exiting.")
                    raise

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            logger.info("Asyncpg database pool closed")
            cls._instance = None
        if cls._engine:
            await cls._engine.dispose()
            logger.info("SQLAlchemy Async Engine disposed")
            cls._engine = None
        cls._session_factory = None


    @classmethod
    def get_pool(cls) -&gt; asyncpg.pool.Pool:
        if cls._instance is None:
            raise RuntimeError("Database pool not initialized. Call initialize() first.")
        return cls._instance

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            raise RuntimeError("SQLAlchemy Async Engine not initialized. Call initialize() first.")
        return cls._engine

    @classmethod
    async def get_session(cls) -&gt; AsyncGenerator[AsyncSession, None]:
        if cls._session_factory is None:
            raise RuntimeError("SQLAlchemy Async Session Factory not initialized. Call initialize() first.")
        async with cls._session_factory() as session:
            try:
                yield session
            finally:
                await session.close() # La connexion est retournée au pool

    # Méthode pour obtenir les métriques du pool (asyncpg seulement)
    @classmethod
    def get_pool_metrics(cls) -&gt; dict:
        if cls._instance:
            return {
                "connections_total": cls._instance.get_size(),
                "connections_active": cls._instance.get_busy_size(),
                "connections_idle": cls._instance.get_idle_size(),
                "connections_waiting": cls._instance.get_waiters(),
            }
        return {}

</code></pre>
<h3 style="color: #388278">Intégration dans <code>main.py</code></h3>
<pre><code>
# main.py
from fastapi import FastAPI, Depends
from app.db.connection import DatabasePoolManager, AsyncSession
import os

app = FastAPI()

@app.on_event("startup")
async def startup_db_pool():
    # Récupérez l'URL de votre base de données depuis les variables d'environnement
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@host:port/dbname")
    await DatabasePoolManager.initialize(
        db_url=db_url,
        pool_min_size=5,
        pool_max_size=20,
        pool_timeout=60,
        pool_recycle=3600,
        max_overflow=10,
        connect_attempts=10, # Plus de tentatives au démarrage
        retry_delay_base=2
    )

@app.on_event("shutdown")
async def shutdown_db_pool():
    await DatabasePoolManager.close()

# Exemple d'utilisation dans une route
@app.get("/items")
async def read_items(session: AsyncSession = Depends(DatabasePoolManager.get_session)):
    # Utilisez la session pour interagir avec la base de données via SQLModel
    # from sqlmodel import select
    # result = await session.execute(select(YourSQLModelClass))
    # items = result.scalars().all()
    # return items
    return {"message": "Database access example"}

@app.get("/db-metrics")
async def get_db_metrics():
    return DatabasePoolManager.get_pool_metrics()
</code></pre>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>L'utilisation de <code>pool_pre_ping=True</code> avec SQLAlchemy est essentielle pour s'assurer que les connexions dans le pool sont toujours viables avant d'être utilisées. Cela aide à gérer les scénarios où la base de données a fermé des connexions inactives. Pour <code>asyncpg</code>, l'équivalent est <code>max_inactive_connection_lifetime</code>. Le backoff exponentiel pour les tentatives de connexion au démarrage est également une bonne pratique pour ne pas surcharger la base de données si elle est temporairement indisponible.</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Oublier de fermer le pool de connexions lors de l'arrêt de l'application, entraînant des connexions "orphans".</li>
<li>Des tailles de pool trop petites, provoquant des blocages par manque de connexions disponibles.</li>
<li>Des tailles de pool trop grandes, surchargeant la base de données.</li>
<li>Ne pas gérer les échecs de connexion initiaux avec des retries et un backoff.</li>
<li>Utiliser des connexions bloquantes (<code>psycopg2</code>) dans un contexte asynchrone (FastAPI).</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/sqlalchemy/sqlalchemy" target="_blank">sqlalchemy/sqlalchemy - GitHub</a></li>
<li><a href="https://github.com/MagicStack/asyncpg" target="_blank">MagicStack/asyncpg - GitHub</a></li>
</ul>
<hr/><h2 id="heading-8" style="color: #cc9900">7. Structured Logging Enterprise : Des Logs Clairs et Exploitables</h2>
<p>Le logging structuré avec <code>structlog</code> transforme vos journaux en données exploitables, facilitant l'analyse, la recherche et le monitoring. L'intégration de contextvars permet d'enrichir chaque log avec des informations contextuelles clés comme le request ID ou l'ID utilisateur.</p>
<h3 style="color: #388278">Code Python Complet : <code>app/logging_config.py</code></h3>
<pre><code>
# app/logging_config.py
import logging
import os
import sys
import structlog
import time
import re
from typing import Any, Dict

# Liste des champs sensibles à filtrer
SENSITIVE_FIELDS = {"password", "token", "jwt", "api_key", "secret"}

def filter_sensitive_data(logger, method_name, event_dict: Dict[str, Any]) -&gt; Dict[str, Any]:
    """Filtre les données sensibles des event_dict."""
    for key in list(event_dict.keys()):
        if any(sf in key.lower() for sf in SENSITIVE_FIELDS):
            event_dict[key] = "[FILTERED]"
    return event_dict

def add_request_duration(logger, method_name, event_dict: Dict[str, Any]) -&gt; Dict[str, Any]:
    """Ajoute la durée de la requête aux logs."""
    start_time = structlog.contextvars.get_contextvars().get("start_time")
    if start_time:
        duration = time.perf_counter() - start_time
        event_dict["duration_ms"] = round(duration * 1000, 2)
    return event_dict

def add_user_id(logger, method_name, event_dict: Dict[str, Any]) -&gt; Dict[str, Any]:
    """Injecte l'ID utilisateur depuis le contexte."""
    user_id = structlog.contextvars.get_contextvars().get("user_id")
    if user_id:
        event_dict["user_id"] = user_id
    return event_dict

def configure_logging(json_logs: bool = False, log_level: str = "INFO"):
    """Configure structlog pour l'application FastAPI."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_user_id, # Injecte l'ID utilisateur
        add_request_duration, # Calcule et injecte la durée de la requête
        filter_sensitive_data, # Filtre les données sensibles
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        # Configuration pour les logs JSON en production
        processor = structlog.processors.JSONRenderer()
    else:
        # Configuration pour les logs lisibles en développement
        processor = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [processor],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Capture les logs Python standard et les achemine via structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
        handlers=[
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter(
                logging.StreamHandler(sys.stdout),
                wrapper_class=structlog.stdlib.BoundLogger,
                processors=shared_processors + [
                    structlog.stdlib.ProcessorFormatter.drop_color_wrap, # Important pour éviter les caractères de couleur dans JSON
                    processor,
                ],
            )
        ]
    )

    # Définir les niveaux de log pour des modules spécifiques
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Moins verbeux pour l'accès uvicorn
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("asyncpg").setLevel(logging.INFO) # Ajustez si vous avez besoin de plus de détails sur la DB
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING) # Évitez les logs trop verbeux de SQLAlchemy

# Middleware pour le timing des requêtes et le nettoyage du contexte
class LoggingContextMiddleware:
    async def __call__(self, request, call_next):
        structlog.contextvars.clear_contextvars()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())) # Assurez-vous d'avoir le CorrelationIdMiddleware avant
        user_id = request.state.get("user_id") # Supposons que votre auth middleware a mis user_id dans request.state
        
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            user_id=user_id,
            path=request.url.path,
            method=request.method,
            start_time=time.perf_counter()
        )

        response = await call_next(request)
        return response

</code></pre>
<h3 style="color: #388278">Intégration dans <code>main.py</code></h3>
<pre><code>
# main.py
from fastapi import FastAPI, Request
from app.logging_config import configure_logging, LoggingContextMiddleware
from app.middleware.correlation_id import CorrelationIdMiddleware # Import pour l'ordre
import structlog
import os
import uuid

# Configure structlog TÔT
json_logs_enabled = os.getenv("ENVIRONMENT", "development") == "production"
log_level = os.getenv("LOG_LEVEL", "INFO")
configure_logging(json_logs=json_logs_enabled, log_level=log_level)

logger = structlog.get_logger(__name__)

app = FastAPI()

# Les middlewares structlog doivent être appelés dans l'ordre pour que les contextes soient bien définis.
# 1. CorrelationIdMiddleware doit venir en premier pour générer/récupérer le request_id
app.add_middleware(CorrelationIdMiddleware)
# 2. LoggingContextMiddleware pour bind d'autres infos et le timing
app.middleware("http")(LoggingContextMiddleware()) # Utilisation directe comme fonction décorateur
# ... (autres middlewares comme SecurityHeadersMiddleware, SmartCompressionMiddleware)

# Exemple de middleware d'authentification qui met l'user_id dans request.state
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Simuler l'extraction de user_id à partir du JWT
    # En production, vous auriez une logique de vérification JWT
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # decoded_token = decode_jwt(auth_header[7:])
        # request.state.user_id = decoded_token.get("sub") # 'sub' est souvent l'ID utilisateur
        request.state.user_id = "user_123" # Placeholder
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    logger.info("Root endpoint accessed", some_data="value")
    return {"message": "Hello from FastAPI"}

</code></pre>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>L'utilisation de <code>structlog.contextvars.clear_contextvars()</code> au début de chaque requête dans <code>LoggingContextMiddleware</code> est cruciale pour éviter les fuites de contexte entre les requêtes. Sans cela, une requête pourrait hériter des informations d'une requête précédente (comme le <code>request_id</code> ou <code>user_id</code>), ce qui est un problème majeur de sécurité et de traçabilité. Assurez-vous que votre middleware d'authentification définit le <code>user_id</code> dans <code>request.state</code> pour qu'il soit disponible pour le middleware de logging.</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Oublier de configurer <code>structlog.contextvars.clear_contextvars()</code>, entraînant des contextes de logs incorrects.</li>
<li>Ne pas capturer les logs des librairies standard via <code>logging.basicConfig</code> et <code>structlog.stdlib.ProcessorFormatter</code>.</li>
<li>Des filtres de données sensibles incomplets, laissant des informations exposées.</li>
<li>Des niveaux de log inappropriés, rendant les logs trop verbeux ou pas assez informatifs.</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/hynek/structlog" target="_blank">hynek/structlog - GitHub</a></li>
</ul>
<hr/><h2 id="heading-9" style="color: #cc9900">8. Circuit Breaker pour AI Providers : Protéger Votre Application des Défaillances Externes</h2>
<p>Le pattern <i>Circuit Breaker</i> est une défense essentielle pour les applications distribuées. Il empêche une application de tenter continuellement d'accéder à un service externe défaillant, ce qui pourrait épuiser les ressources et entraîner des défaillances en cascade. Au lieu de cela, il échoue rapidement, permettant au service défaillant de récupérer et offrant des stratégies de fallback.</p>
<h3 style="color: #388278">Code Python Complet : <code>app/circuit_breaker.py</code></h3>
<pre><code>
# app/circuit_breaker.py
import time
import asyncio
from enum import Enum, auto
from typing import Callable, Any, Coroutine
import structlog

logger = structlog.get_logger(__name__)

class CircuitBreakerState(Enum):
    CLOSED = auto()    # Le service fonctionne normalement. Les requêtes passent.
    OPEN = auto()      # Le service est défaillant. Les requêtes sont bloquées.
    HALF_OPEN = auto() # Après une période, quelques requêtes sont autorisées à tester si le service a récupéré.

class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,  # Temps en secondes pour passer de OPEN à HALF_OPEN
        reset_timeout: int = 300,    # Temps en secondes pour réinitialiser le compteur de pannes en CLOSED
        fallback_function: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.reset_timeout = reset_timeout
        self.fallback_function = fallback_function

        self._state = CircuitBreakerState.CLOSED
        self._failures = 0
        self._last_failure_time = None
        self._last_open_time = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -&gt; CircuitBreakerState:
        # Logique pour passer de OPEN à HALF_OPEN
        if self._state == CircuitBreakerState.OPEN:
            if time.time() - self._last_open_time &gt; self.recovery_timeout:
                self._state = CircuitBreakerState.HALF_OPEN
                logger.warning(f"Circuit Breaker '{self.name}' moved to HALF_OPEN state.", state="HALF_OPEN")
        
        # Logique pour réinitialiser le compteur de pannes si CLOSED depuis longtemps
        if self._state == CircuitBreakerState.CLOSED and self._failures &gt; 0 and \
           self._last_failure_time and time.time() - self._last_failure_time &gt; self.reset_timeout:
            self._failures = 0
            logger.info(f"Circuit Breaker '{self.name}' reset failure count.", state="CLOSED", failures=self._failures)

        return self._state

    async def __call__(self, func: Callable[..., Coroutine[Any, Any, Any]]):
        async def wrapper(*args, **kwargs):
            async with self._lock:
                current_state = self.state

                if current_state == CircuitBreakerState.OPEN:
                    logger.warning(
                        f"Circuit Breaker '{self.name}' is OPEN, blocking call to '{func.__name__}'.",
                        state="OPEN"
                    )
                    if self.fallback_function:
                        return await self.fallback_function(*args, **kwargs)
                    raise CircuitBreakerOpenException(
                        f"Circuit Breaker '{self.name}' is OPEN."
                    )
                
                if current_state == CircuitBreakerState.HALF_OPEN:
                    # Une seule requête est autorisée à passer pour tester la récupération
                    if self._failures == 0: # Si c'est la première requête en HALF_OPEN
                        logger.info(
                            f"Circuit Breaker '{self.name}' is HALF_OPEN, allowing a single test call to '{func.__name__}'.",
                            state="HALF_OPEN"
                        )
                    else: # Toutes les autres requêtes sont bloquées
                        logger.warning(
                            f"Circuit Breaker '{self.name}' is HALF_OPEN, but test call already in progress or failed. Blocking call to '{func.__name__}'.",
                            state="HALF_OPEN"
                        )
                        if self.fallback_function:
                            return await self.fallback_function(*args, **kwargs)
                        raise CircuitBreakerOpenException(
                            f"Circuit Breaker '{self.name}' is HALF_OPEN."
                        )

            try:
                result = await func(*args, **kwargs)
                async with self._lock:
                    if current_state != CircuitBreakerState.CLOSED:
                        # Si la requête en HALF_OPEN réussit, réinitialiser
                        self._state = CircuitBreakerState.CLOSED
                        self._failures = 0
                        self._last_failure_time = None
                        self._last_open_time = None
                        logger.info(
                            f"Circuit Breaker '{self.name}' moved to CLOSED state after successful call.",
                            state="CLOSED"
                        )
                return result
            except Exception as e:
                async with self._lock:
                    self._failures += 1
                    self._last_failure_time = time.time()
                    logger.error(
                        f"Circuit Breaker '{self.name}' recorded a failure calling '{func.__name__}'. "
                        f"Failures: {self._failures}/{self.failure_threshold}",
                        error=str(e), state=self._state
                    )
                    if self._failures &gt;= self.failure_threshold and self._state != CircuitBreakerState.OPEN:
                        self._state = CircuitBreakerState.OPEN
                        self._last_open_time = time.time()
                        logger.error(
                            f"Circuit Breaker '{self.name}' moved to OPEN state due to excessive failures.",
                            state="OPEN"
                        )
                
                if self.fallback_function:
                    return await self.fallback_function(*args, **kwargs)
                raise CircuitBreakerFailedException(
                    f"Circuit Breaker '{self.name}' failed after {self._failures} attempts."
                ) from e
        return wrapper

class CircuitBreakerOpenException(Exception):
    """Exception levée lorsque le circuit breaker est en état OPEN."""
    pass

class CircuitBreakerFailedException(Exception):
    """Exception levée lorsque le circuit breaker a échoué (mais n'est pas OPEN)."""
    pass

# ---------- Gestion des Providers IA ----------
class AIProvider:
    def __init__(self, name: str, cb: CircuitBreaker):
        self.name = name
        self.circuit_breaker = cb

    @self.circuit_breaker
    async def call_ai_service(self, prompt: str) -&gt; str:
        logger.info(f"Calling AI service {self.name} with prompt", prompt=prompt)
        # Simuler une défaillance ou un succès
        if time.time() % 10 &lt; 3: # 30% de chance d'échec
            logger.error(f"AI service {self.name} failed!", provider=self.name)
            raise ValueError(f"AI service {self.name} temporarily unavailable")
        
        await asyncio.sleep(0.5) # Simuler le temps de réponse
        return f"Response from {self.name} for: {prompt}"

async def fallback_ai_response(prompt: str) -&gt; str:
    logger.warning("Using fallback AI response", prompt=prompt)
    return f"Fallback response for: {prompt} (AI service unavailable)"

# Initialisation des Circuit Breakers et Providers
gemini_cb = CircuitBreaker(
    name="Gemini",
    failure_threshold=3,
    recovery_timeout=30, # 30s avant de passer en HALF_OPEN
    fallback_function=fallback_ai_response
)
gemini_provider = AIProvider("Gemini", gemini_cb)

claude_cb = CircuitBreaker(
    name="Claude",
    failure_threshold=5,
    recovery_timeout=60,
    fallback_function=fallback_ai_response
)
claude_provider = AIProvider("Claude", claude_cb)

groq_cb = CircuitBreaker(
    name="Groq",
    failure_threshold=2,
    recovery_timeout=15,
    fallback_function=fallback_ai_response
)
groq_provider = AIProvider("Groq", groq_cb)

# Liste des providers, par ordre de préférence (ou de coût, etc.)
AI_PROVIDERS = [gemini_provider, claude_provider, groq_provider]

async def call_with_provider_fallback(prompt: str) -&gt; str:
    for provider in AI_PROVIDERS:
        try:
            return await provider.call_ai_service(prompt)
        except (CircuitBreakerOpenException, CircuitBreakerFailedException):
            logger.warning(f"Provider {provider.name} unavailable or circuit open, trying next one.")
            continue # Tente le prochain provider
        except Exception as e:
            # Gérer les autres exceptions non liées au circuit breaker ici
            logger.error(f"Error calling {provider.name}: {e}", provider=provider.name)
            continue
    
    logger.critical("All AI providers failed or are unavailable.")
    return await fallback_ai_response(prompt) # Si tous les providers échouent, utilisez le fallback global

</code></pre>
<h3 style="color: #388278">Intégration dans <code>main.py</code></h3>
<pre><code>
# main.py
from fastapi import FastAPI
from app.circuit_breaker import call_with_provider_fallback, gemini_cb, claude_cb, groq_cb
import structlog

logger = structlog.get_logger(__name__)
app = FastAPI()

@app.get("/generate-ai-text")
async def generate_ai_text(prompt: str):
    try:
        response = await call_with_provider_fallback(prompt)
        # Pour le monitoring, vous pouvez loguer l'état des breakers
        logger.info("AI Provider states",
                    gemini_state=str(gemini_cb.state.name),
                    claude_state=str(claude_cb.state.name),
                    groq_state=str(groq_cb.state.name))
        return {"response": response}
    except Exception as e:
        logger.error("Failed to generate AI text after all fallbacks", error=str(e))
        return {"error": "Could not generate AI text at this time."}, 500

</code></pre>
<div style="height: 500px;"><canvas id="radarCanvas"></canvas></div>
<script id="site_chart_radar">
const ctxRadar = document.getElementById("radarCanvas");
const radarChart = new Chart(ctxRadar, {
    type: 'radar',
    data: {
        labels: ['Fiabilité', 'Scalabilité', 'Performance', 'Résilience', 'Observabilité', 'Sécurité'],
        datasets: [{
            label: 'Architecture Actuelle',
            data: [3, 3, 4, 3, 3, 3],
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderColor: 'rgba(255, 99, 132, 1)',
            pointBackgroundColor: 'rgba(255, 99, 132, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1,
            fill: true
        }, {
            label: 'Architecture Cible S+++',
            data: [5, 5, 5, 5, 5, 5],
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            pointBackgroundColor: 'rgba(54, 162, 235, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1,
            fill: true
        }]
    },
    options: {
        maintainAspectRatio: false,
        lineTension: 0.2,
        scales: {
            r: {
                beginAtZero: true,
                min: 0,
                max: 5,
                ticks: {
                    backdropColor: 'rgba(0, 0, 0, 0)',
                    color: '#888888',
                    stepSize: 1
                },
                pointLabels: {
                    color: '#888888'
                },
                grid: {
                    color: '#888888'
                },
                angleLines: {
                    color: '#888888'
                }
            }
        },
        plugins: {
            legend: {
                labels: {
                    color: '#888888'
                }
            }
        }
    }
});
radarChart.update();
</script>
<p style="text-align: center;"><i>Comparaison des capacités architecturales : de l'état actuel à l'objectif S+++.</i></p>
<p>Ce graphique radar illustre l'amélioration des caractéristiques clés de votre plateforme en passant d'une architecture fonctionnelle mais standard à une architecture S+++ de niveau entreprise. Chaque point représente une dimension cruciale où les pratiques proposées dans ce guide apportent des gains significatifs, transformant votre application en un système hautement optimisé et résilient.</p>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>L'implémentation du <code>CircuitBreaker</code> en tant que décorateur asynchrone est puissante, mais elle doit être thread-safe. L'utilisation d'un <code>asyncio.Lock</code> est essentielle pour protéger les variables d'état du disjoncteur (<code>_state</code>, <code>_failures</code>, etc.) contre les accès concurrents, évitant ainsi les conditions de course dans un environnement FastAPI asynchrone. La gestion des différents providers avec une boucle et un fallback permet une grande flexibilité et une meilleure résilience.</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Oublier la synchronisation des états du disjoncteur dans un environnement concurrentiel.</li>
<li>Définir des seuils de panne trop bas, ce qui pourrait faire passer le disjoncteur en état OPEN trop fréquemment.</li>
<li>Des fonctions de fallback qui échouent également, ou qui sont trop lentes.</li>
<li>Ne pas avoir de mécanisme de réinitialisation automatique du compteur de pannes en état CLOSED, même sans panne, pour éviter qu'une accumulation lente de pannes ne l'ouvre brusquement.</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/Netflix/Hystrix" target="_blank">Netflix/Hystrix - GitHub</a> (bien que Hystrix soit en Java, c'est la référence historique pour les patterns de circuit breaker)</li>
</ul>
<hr/><h2 id="heading-10" style="color: #cc9900">9. API Rate Limiting Avancé : Contrôle Granulaire du Trafic</h2>
<p>Le <i>Rate Limiting</i> est essentiel pour protéger votre API contre les abus, les attaques par déni de service (DoS) et pour assurer une utilisation équitable des ressources. Un système avancé intègre des algorithmes plus sophistiqués et fournit des en-têtes de réponse standards.</p>
<h3 style="color: #388278">Code Python Complet : <code>app/middleware/rate_limiter.py</code></h3>
<pre><code>
# app/middleware/rate_limiter.py
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import redis.asyncio as redis
import time
import math
import os
from collections import deque
from typing import Dict, Deque, Any
import structlog

logger = structlog.get_logger(__name__)

# Config Redis (remplacez par votre configuration réelle)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client: Optional[redis.Redis] = None

async def get_redis_client_instance():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL)
    return redis_client

class SlidingWindowRateLimiter:
    def __init__(self, capacity: int, window_seconds: int, burst_capacity: int = 0):
        self.capacity = capacity
        self.window_seconds = window_seconds
        self.burst_capacity = burst_capacity
        self.timestamps: Dict[str, Deque[float]] = {}
        self.last_reset: Dict[str, float] = {}

    async def _cleanup_timestamps(self, key: str):
        now = time.time()
        # Supprimer les timestamps en dehors de la fenêtre glissante
        while self.timestamps[key] and self.timestamps[key][0] &lt;= now - self.window_seconds:
            self.timestamps[key].popleft()

    async def allow_request(self, key: str) -&gt; (bool, int, int, int):
        if key not in self.timestamps:
            self.timestamps[key] = deque()
            self.last_reset[key] = time.time()

        await self._cleanup_timestamps(key)
        
        now = time.time()
        current_requests = len(self.timestamps[key])
        
        # Logique pour le burst allowance (basé sur le Token Bucket, mais intégré ici)
        # Ici, une approche simplifiée: le burst est un dépassement temporaire de la capacité normale.
        # Nous allons vérifier si le nombre de requêtes dépasse la capacité normale
        # ET la capacité de burst.
        
        allowed_limit = self.capacity
        if self.burst_capacity &gt; 0:
            # Pour un burst, nous permettons temporairement plus de requêtes
            # L'idée est que vous pouvez faire plus de requêtes en un court laps de temps
            # tant que le total sur la fenêtre reste gérable.
            # Une implémentation réelle de Token Bucket serait plus précise.
            # Ici, nous nous basons sur le fait que le nombre de requêtes "réelles"
            # ne dépasse pas la capacité + burst.
            allowed_limit = self.capacity + self.burst_capacity

        if current_requests &lt; allowed_limit:
            self.timestamps[key].append(now)
            remaining = allowed_limit - len(self.timestamps[key])
            reset_after = max(0, self.window_seconds - (now - self.last_reset[key]))
            return True, allowed_limit, remaining, math.ceil(reset_after)
        else:
            remaining = allowed_limit - current_requests
            reset_after = max(0, self.window_seconds - (now - self.last_reset[key]))
            return False, allowed_limit, remaining, math.ceil(reset_after)

# Utilisation d'un dictionnaire pour gérer plusieurs limiteurs par endpoint/route
rate_limiters: Dict[str, SlidingWindowRateLimiter] = {}

class RateLimitingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp,
                 default_capacity: int = 100,
                 default_window_seconds: int = 60,
                 default_burst: int = 20,
                 whitelist_ips: list[str] = None,
                 config_per_path: Dict[str, Dict[str, Any]] = None):
        super().__init__(app)
        self.default_capacity = default_capacity
        self.default_window_seconds = default_window_seconds
        self.default_burst = default_burst
        self.whitelist_ips = whitelist_ips if whitelist_ips is not None else []
        self.config_per_path = config_per_path if config_per_path is not None else {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        if client_ip in self.whitelist_ips:
            return await call_next(request)

        # Déterminer la clé de limite (ici par IP, peut être par user_id, API Key, etc.)
        rate_limit_key = f"rate_limit:{client_ip}:{request.url.path}" # Rate limit par IP et par endpoint

        # Obtenir la configuration spécifique pour ce chemin, ou utiliser les valeurs par défaut
        path_config = self.config_per_path.get(request.url.path, {
            "capacity": self.default_capacity,
            "window_seconds": self.default_window_seconds,
            "burst_capacity": self.default_burst
        })
        
        capacity = path_config.get("capacity", self.default_capacity)
        window = path_config.get("window_seconds", self.default_window_seconds)
        burst = path_config.get("burst_capacity", self.default_burst)

        if rate_limit_key not in rate_limiters:
            # Crée un limiteur pour cette combinaison clé/chemin
            rate_limiters[rate_limit_key] = SlidingWindowRateLimiter(capacity, window, burst)
            
        allowed, limit, remaining, reset_after = await rate_limiters[rate_limit_key].allow_request(rate_limit_key)

        response = Response()
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(reset_after) # Temps en secondes jusqu'au reset

        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                ip=client_ip,
                path=request.url.path,
                limit=limit,
                remaining=remaining,
                reset_after=reset_after
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too Many Requests"
            )
        
        response = await call_next(request)
        
        # S'assure que les headers sont ajoutés même si la réponse vient d'un autre middleware
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining -1 )) # -1 car la requête actuelle a consommé une ressource
        response.headers["X-RateLimit-Reset"] = str(reset_after)

        return response

</code></pre>
<h3 style="color: #388278">Intégration dans <code>main.py</code></h3>
<pre><code>
# main.py
from fastapi import FastAPI
from app.middleware.rate_limiter import RateLimitingMiddleware
import os

app = FastAPI()

# Initialisation du client Redis pour le rate limiter
@app.on_event("startup")
async def startup_event():
    from app.middleware.rate_limiter import get_redis_client_instance
    await get_redis_client_instance() # Initialise le client Redis

# Enregistrement du middleware de Rate Limiting
app.add_middleware(
    RateLimitingMiddleware,
    default_capacity=100,
    default_window_seconds=60,
    default_burst=20,
    whitelist_ips=["127.0.0.1", "::1", os.getenv("KUBERNETES_HEALTH_CHECK_IP", "")], # Ajoutez les IPs de vos probes K8s
    config_per_path={
        "/api/v1/auth/login": {"capacity": 10, "window_seconds": 30, "burst_capacity": 5}, # Plus restrictif
        "/api/v1/ai/generate": {"capacity": 50, "window_seconds": 60, "burst_capacity": 10},
    }
)

# ... vos routes
</code></pre>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>L'implémentation d'un <code>SlidingWindowRateLimiter</code> sans Redis (pour la démo) stocke les horodatages en mémoire. Pour un environnement distribué (Kubernetes), l'utilisation de Redis est impérative pour un état partagé et cohérent entre les instances de l'API. Le <code>burst_capacity</code> est une clé de performance : il permet à l'application d'absorber des pics de trafic courts au-dessus de la capacité normale, sans déclencher le limiteur, tant que le taux moyen sur la fenêtre reste dans les limites. La gestion du <code>X-RateLimit-Remaining</code> après le <code>call_next(request)</code> assure que la valeur renvoyée reflète l'état après la consommation de la requête actuelle.</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Utiliser une fenêtre fixe qui peut pénaliser les utilisateurs au début d'une nouvelle fenêtre (le <i>burst effect</i>).</li>
<li>Ne pas fournir les en-têtes <code>X-RateLimit-*</code>, ce qui rend la limite invisible pour les clients.</li>
<li>Ne pas gérer correctement le <code>Retry-After</code>, ou fournir une valeur imprécise.</li>
<li>Définir des limites trop agressives qui bloquent des utilisateurs légitimes.</li>
<li>Implémenter le rate limiting en mémoire dans un environnement distribué (Kubernetes), ce qui rend le limiteur inefficace.</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/encode/starlette-limiter" target="_blank">encode/starlette-limiter - GitHub</a> (bien qu'il s'agisse d'un wrapper, il implémente ces concepts)</li>
</ul>
<hr/><h2 id="heading-11" style="color: #cc9900">10. Dockerfile Multi-Stage Optimisé : Des Images Légères et Sécurisées</h2>
<p>Un Dockerfile multi-stage réduit la taille de l'image finale en séparant les dépendances de build du runtime. Cela améliore la sécurité, réduit les temps de pull et de déploiement, et diminue la surface d'attaque.</p>
<h3 style="color: #388278">Code Complet : <code>Dockerfile</code> et <code>.dockerignore</code></h3>
<pre><code>
# Dockerfile
# --- Stage 1: Builder ---
FROM python:3.13-slim-bookworm AS builder

# Définir l'utilisateur non-root pour la sécurité
ARG UID=10001
RUN adduser --disabled-password --gecos "" --home /app --uid "${UID}" appuser

WORKDIR /app

# Installer Poetry (ou pip-tools)
# Utiliser Poetry pour gérer les dépendances de manière déclarative
RUN pip install poetry==1.8.2

# Copier les fichiers de définition de dépendances Poetry
COPY pyproject.toml poetry.lock ./

# Configuration de Poetry pour créer un environnement virtuel dans le conteneur
RUN poetry config virtualenvs.create false \
    &amp;&amp; poetry install --no-root --only main --no-interaction --no-ansi

# Nettoyage des caches pip et Poetry
RUN rm -rf /root/.cache/pip /root/.cache/pypoetry


# --- Stage 2: Runtime ---
FROM python:3.13-slim-bookworm AS runtime

ARG UID=10001
RUN adduser --disabled-password --gecos "" --home /app --uid "${UID}" appuser

WORKDIR /app

# Copier les dépendances installées depuis le stage builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copier le code de l'application
COPY . /app

# Assurez-vous que l'utilisateur non-root est le propriétaire des fichiers de l'application
RUN chown -R appuser:appuser /app

# Définir l'utilisateur d'exécution
USER appuser

# Exposer le port de l'application
EXPOSE 8000

# Labels OCI (Open Container Initiative) standards
LABEL org.opencontainers.image.authors="votre_nom@votre_entreprise.com"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/votre_repo/votre_app"
LABEL org.opencontainers.image.description="FastAPI AI SaaS platform"
LABEL org.opencontainers.image.url="https://votre_entreprise.com"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.created=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
LABEL org.opencontainers.image.revision=$(git rev-parse HEAD)


# HEALTHCHECK instruction (voir section 5 pour des checks plus avancés)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:8000/health/live || exit 1

# STOPSIGNAL pour un arrêt gracieux (voir section 4)
STOPSIGNAL SIGTERM

# Commande pour exécuter l'application
# Utilisez Uvicorn avec Gunicorn pour la production pour une meilleure gestion des processus
# Assurez-vous d'avoir Gunicorn installé dans vos dépendances Poetry
# CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
# Ou directement Uvicorn si vous n'avez pas Gunicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "info", "--graceful-timeout", "30"]

</code></pre>
<h3 style="color: #388278">Code Complet : <code>.dockerignore</code></h3>
<pre><code>
# .dockerignore
# Ignorer les fichiers Python compilés
*.pyc
*.pyo
__pycache__
.pytest_cache

# Ignorer les fichiers liés à l'environnement de développement
.env
.venv
venv/
.mypy_cache/
.vscode/
.idea/
*.sqlite3

# Ignorer les répertoires et fichiers Git
.git
.gitignore

# Ignorer les fichiers de logs
*.log
logs/

# Ignorer les fichiers de documentation, de tests (si non nécessaires au runtime)
docs/
tests/

# Ignorer les fichiers temporaires et de build
tmp/
dist/
build/
*.egg-info/
</code></pre>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>L'utilisation de <code>poetry config virtualenvs.create false</code> dans le stage builder est cruciale pour que Poetry installe les dépendances directement dans l'environnement Python du conteneur (<code>/usr/local/lib/python3.13/site-packages</code>), ce qui les rend faciles à copier vers le stage runtime sans avoir à répliquer un environnement virtuel entier. L'argument <code>--no-root</code> lors de l'installation des dépendances Poetry évite d'installer le projet lui-même en mode éditable dans le builder, ce qui est généralement inutile pour le build d'une image Docker.</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Ne pas utiliser de Dockerfile multi-stage, résultant en des images Docker volumineuses.</li>
<li>Exécuter le conteneur en tant que root, ce qui représente un risque de sécurité majeur.</li>
<li>Ne pas utiliser <code>.dockerignore</code>, copiant des fichiers inutiles qui augmentent la taille de l'image.</li>
<li>Ne pas optimiser l'ordre des instructions dans le Dockerfile, invalidant le cache Docker fréquemment.</li>
<li>Oublier la commande <code>HEALTHCHECK</code> et <code>STOPSIGNAL</code> pour une bonne intégration Kubernetes.</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/tiangolo/fastapi" target="_blank">tiangolo/fastapi - GitHub</a> (La documentation FastAPI a de bonnes sections sur Docker)</li>
</ul>
<hr/><h2 id="heading-12" style="color: #cc9900">11. OpenTelemetry Integration : Traçabilité et Métriques Distribuées</h2>
<p>OpenTelemetry fournit un cadre standardisé pour instrumenter, générer, collecter et exporter des données de télémétrie (traces, métriques, logs). C'est un élément clé pour l'observabilité des systèmes distribués, permettant de comprendre le flux des requêtes à travers votre architecture.</p>
<h3 style="color: #388278">Code Python Complet : <code>app/observability/opentelemetry_config.py</code></h3>
<pre><code>
# app/observability/opentelemetry_config.py
import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    ConsoleSpanExporter,
    BatchSpanProcessor,
    SimpleSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
import structlog
from structlog.processors import JSONRenderer

logger = structlog.get_logger(__name__)

def configure_opentelemetry(app, service_name: str = "fastapi-ai-saas", environment: str = "development"):
    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": environment,
    })

    # --- Tracing ---
    provider = TracerProvider(resource=resource)
    
    if environment == "production":
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        span_processor = BatchSpanProcessor(span_exporter)
        logger.info("OpenTelemetry Tracing configured for OTLP export", endpoint=otlp_endpoint)
    else:
        span_exporter = ConsoleSpanExporter()
        span_processor = SimpleSpanProcessor(span_exporter)
        logger.info("OpenTelemetry Tracing configured for Console export (development mode)")

    provider.add_span_processor(span_processor)
    trace.set_tracer_provider(provider)

    # --- Metrics (example, more advanced setup typically involves custom metrics) ---
    # metrics_provider = MeterProvider(resource=resource)
    # if environment == "production":
    #     metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint)
    #     metrics_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
    #     logger.info("OpenTelemetry Metrics configured for OTLP export", endpoint=otlp_endpoint)
    # else:
    #     metric_exporter = ConsoleMetricExporter()
    #     metrics_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
    #     logger.info("OpenTelemetry Metrics configured for Console export (development mode)")
    # metrics_provider.add_metric_reader(metrics_reader)
    # set_meter_provider(metrics_provider)


    # --- Instrumentation ---
    # FastAPI
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    logger.info("FastAPI Instrumented")

    # AsyncPG (pour PostgreSQL)
    AsyncPGInstrumentor().instrument()
    logger.info("AsyncPG Instrumented")

    # Redis
    RedisInstrumentor().instrument()
    logger.info("Redis Instrumented")

    # HTTPX (pour appels externes, ex: AI Providers)
    HTTPXClientInstrumentor().instrument()
    logger.info("HTTPX Instrumented")

    # --- Correlation avec Structlog ---
    # Pour injecter le trace_id et span_id d'OpenTelemetry dans les logs structlog
    # Créez un processor structlog pour cela.
    def add_otel_trace_info(logger, method_name, event_dict):
        current_span = trace.get_current_span()
        if current_span and current_span.get_span_context().is_valid:
            event_dict["trace_id"] = current_span.get_span_context().trace_id
            event_dict["span_id"] = current_span.get_span_context().span_id
        return event_dict
    
    # Ajoutez ce processor à la configuration de structlog
    # Assurez-vous qu'il est ajouté avant le JSONRenderer
    # Cette étape doit être faite dans la configuration de structlog, pas ici directement
    # car structlog.configure est appelé une seule fois.
    # Voir la section 7 pour l'intégration complète dans structlog_config.py

</code></pre>
<h3 style="color: #388278">Mise à jour de <code>app/logging_config.py</code> pour la corrélation</h3>
<pre><code>
# app/logging_config.py (ajouts pour OpenTelemetry)
# ... (imports existants)
from opentelemetry import trace # Nouvel import

# Nouveau processor pour ajouter les IDs de trace OpenTelemetry
def add_otel_trace_info(logger, method_name, event_dict: Dict[str, Any]) -&gt; Dict[str, Any]:
    current_span = trace.get_current_span()
    if current_span and current_span.get_span_context().is_valid:
        event_dict["otel.trace_id"] = format(current_span.get_span_context().trace_id, "032x") # Format hex
        event_dict["otel.span_id"] = format(current_span.get_span_context().span_id, "016x") # Format hex
    return event_dict

def configure_logging(json_logs: bool = False, log_level: str = "INFO"):
    """Configure structlog pour l'application FastAPI."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_user_id,
        add_request_duration,
        filter_sensitive_data,
        add_otel_trace_info, # AJOUTER CE PROCESSOR ICI
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    # ... (le reste de la fonction reste identique)
</code></pre>
<h3 style="color: #388278">Intégration dans <code>main.py</code></h3>
<pre><code>
# main.py
from fastapi import FastAPI
from app.observability.opentelemetry_config import configure_opentelemetry
from app.logging_config import configure_logging # Assurez-vous d'utiliser la version mise à jour
import os
import structlog

# Configurer structlog en premier
json_logs_enabled = os.getenv("ENVIRONMENT", "development") == "production"
log_level = os.getenv("LOG_LEVEL", "INFO")
configure_logging(json_logs=json_logs_enabled, log_level=log_level)

logger = structlog.get_logger(__name__)

app = FastAPI()

# Configurer OpenTelemetry après l'initialisation de FastAPI
environment = os.getenv("ENVIRONMENT", "development")
configure_opentelemetry(app, service_name="fastapi-ai-saas", environment=environment)

# ... (vos middlewares et routes)
</code></pre>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>L'ordre d'initialisation est important : configurez <code>structlog</code> en premier, puis <code>OpenTelemetry</code>. Le processor <code>add_otel_trace_info</code> dans <code>structlog</code> doit être placé avant le <code>JSONRenderer</code> ou <code>ConsoleRenderer</code> pour que les IDs de trace et de span soient correctement ajoutés à l'<code>event_dict</code> avant le rendu final. Pour l'export OTLP, assurez-vous que votre collecteur OpenTelemetry est accessible et configuré pour recevoir les données sur le port par défaut (4317 pour gRPC).</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Oublier d'instrumenter une bibliothèque utilisée (ex: oubli de <code>RedisInstrumentor</code> si vous utilisez Redis).</li>
<li>Ne pas configurer correctement l'exportateur (OTLP) en production, résultant en des traces qui ne sont pas envoyées.</li>
<li>Des problèmes de corrélation (logs sans trace_id) si le processor structlog est mal placé ou si les IDs ne sont pas correctement extraits.</li>
<li>Surcharger l'application avec trop de métriques ou de traces si le niveau de détail n'est pas ajusté.</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/open-telemetry/opentelemetry-python" target="_blank">open-telemetry/opentelemetry-python - GitHub</a></li>
</ul>
<hr/><h2 id="heading-13" style="color: #cc9900">12. Error Tracking (Sentry-like) : Capture Intelligente des Exceptions</h2>
<p>L'intégration d'un outil d'error tracking comme Sentry (ou une alternative open-source comme GlitchTip) est cruciale pour surveiller les erreurs en production. Il permet de détecter, de regrouper et de résoudre rapidement les problèmes, en fournissant un contexte détaillé de l'erreur.</p>
<h3 style="color: #388278">Code Python Complet : <code>app/error_tracking.py</code></h3>
<pre><code>
# app/error_tracking.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastAPIIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
import os
import structlog
from typing import Any, Dict

logger = structlog.get_logger(__name__)

def configure_sentry(app, dsn: Optional[str] = None, environment: str = "development", release: str = None):
    if not dsn:
        logger.info("Sentry DSN not provided, Sentry will not be initialized.")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        integrations=[
            FastAPIIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            CeleryIntegration(), # Si Celery est dans le même processus ou bien configuré
        ],
        traces_sample_rate=1.0, # Ajustez le taux d'échantillonnage des traces en fonction de votre volume
        profiles_sample_rate=1.0, # Ajustez le taux d'échantillonnage des profils
        send_default_pii=True, # Envoyez les informations personnelles identifiables (PII) si nécessaire
        server_name_from_host=True, # Utilise le hostname comme nom de serveur
        max_breadcrumbs=50, # Nombre maximum de breadcrumbs à collecter
        attach_stacktrace=True, # Attacher une stacktrace complète aux événements
        # Filtrage de données sensibles (peut aussi être fait avec des Sentry.filters)
        # before_send=filter_sentry_event,
    )
    logger.info("Sentry initialized successfully.")

# Exemple de fonction pour ajouter du contexte utilisateur (à appeler après authentification)
def set_sentry_user_context(user_id: str, email: Optional[str] = None):
    sentry_sdk.set_user({"id": user_id, "email": email})

# Exemple de fonction pour ajouter un contexte global (ex: request_id)
def set_sentry_context(key: str, value: Any):
    sentry_sdk.set_context(key, value)

# Custom error handler for 500s (optional, Sentry handles most automatically)
async def custom_internal_server_error_handler(request, exc):
    # Sentry doit déjà avoir capturé l'erreur via l'intégration FastAPI
    # Vous pouvez ajouter ici une logique supplémentaire ou un rendu de page d'erreur personnalisé
    logger.error("Internal Server Error caught by custom handler", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred. Please try again later.", "request_id": request.headers.get("X-Request-ID")}
    )

# Fonction pour intégrer le request_id et user_id des contextvars structlog dans Sentry
def sentry_before_send(event: Dict[str, Any], hint: Dict[str, Any]) -&gt; Optional[Dict[str, Any]]:
    # Tente de récupérer le request_id et user_id des contextvars de structlog
    # ou de l'état de la requête si cela a été bind par un middleware précédent
    request_id = structlog.contextvars.get_contextvars().get("request_id")
    user_id = structlog.contextvars.get_contextvars().get("user_id")

    if request_id:
        if "contexts" not in event:
            event["contexts"] = {}
        event["contexts"]["request"] = {"id": request_id} # Sentry convention pour request ID
    
    if user_id:
        if "user" not in event:
            event["user"] = {}
        event["user"]["id"] = user_id
    
    # Filtrer d'autres données sensibles avant d'envoyer à Sentry
    if "request" in event and "data" in event["request"]:
        if "password" in event["request"]["data"]:
            event["request"]["data"]["password"] = "[FILTERED]"
        if "token" in event["request"]["data"]:
            event["request"]["data"]["token"] = "[FILTERED]"
    
    return event
</code></pre>
<h3 style="color: #388278">Intégration dans <code>main.py</code></h3>
<pre><code>
# main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.error_tracking import configure_sentry, set_sentry_user_context, sentry_before_send, custom_internal_server_error_handler
import os
import sentry_sdk
import structlog
from sentry_sdk.integrations.logging import LoggingIntegration

logger = structlog.get_logger(__name__)
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Configure Sentry TÔT
    sentry_dsn = os.getenv("SENTRY_DSN")
    sentry_env = os.getenv("ENVIRONMENT", "development")
    app_version = os.getenv("APP_VERSION", "1.0.0")
    configure_sentry(app, dsn=sentry_dsn, environment=sentry_env, release=app_version)
    
    # Ajouter le processor sentry_before_send à Sentry
    if sentry_dsn:
        sentry_sdk.add_breadcrumb(
            category="startup",
            message="FastAPI application starting up",
            level="info",
        )
        sentry_sdk.flush() # S'assurer que le breadcrumb est envoyé si l'app crash juste après

    # Intégrer Sentry avec structlog (en envoyant les logs critiques à Sentry)
    # C'est une approche pour ne pas tout envoyer, mais plutôt les erreurs structlog
    # sentry_logging = LoggingIntegration(
    #     level=logging.INFO,        # Capture logs &gt;= INFO
    #     event_level=logging.ERROR  # Envoie seulement ERROR et CRITICAL à Sentry en tant qu'événements
    # )
    # sentry_sdk.add_integration(sentry_logging) # Déjà fait dans configure_sentry via integrations=[...]


# Capture des exceptions non gérées
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Sentry captera les erreurs FastAPI/Starlette automatiquement avec FastAPIIntegration
    # Vous pouvez ajouter un logging structuré ici si nécessaire
    logger.warning("HTTP Exception", status_code=exc.status_code, detail=exc.detail, request_id=request.headers.get("X-Request-ID"))
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.exception_handler(Exception)
async def catch_all_exception_handler(request: Request, exc: Exception):
    # Sentry captera cette exception automatiquement
    # Loggez l'erreur avec structlog avant de retourner la réponse d'erreur
    logger.error("Unhandled Exception", exc_info=True, request_id=request.headers.get("X-Request-ID"), error_message=str(exc))
    return await custom_internal_server_error_handler(request, exc)


# Exemple d'utilisation dans une route
@app.get("/trigger-error")
async def trigger_error():
    logger.info("Triggering a test error...")
    1 / 0 # Ceci déclenchera une ZeroDivisionError
</code></pre>
<h4 style="color: #7FA86E">Astuce non-évidente :</h4>
<p>L'argument <code>before_send</code> dans <code>sentry_sdk.init</code> est un hook puissant pour manipuler l'événement Sentry avant qu'il ne soit envoyé. C'est l'endroit idéal pour injecter des informations contextuelles supplémentaires (comme le <code>request_id</code> ou le <code>user_id</code> provenant de <code>structlog.contextvars</code> ou <code>request.state</code>) et pour filtrer des données sensibles qui auraient pu échapper aux filtres par défaut de Sentry. Pensez également à utiliser <code>sentry_sdk.add_breadcrumb</code> pour enregistrer des étapes importantes du parcours utilisateur ou du traitement, ce qui aide à comprendre l'historique avant une erreur.</p>
<h4 style="color: #7FA86E">Erreurs Courantes à Éviter :</h4>
<ul>
<li>Oublier de configurer le DSN (Data Source Name) de Sentry en production, désactivant de fait le tracking.</li>
<li>Des taux d'échantillonnage des traces (<code>traces_sample_rate</code>) trop bas pour les environnements où vous avez besoin d'une visibilité complète.</li>
<li>Ne pas intégrer les contextes importants (<code>request_id</code>, <code>user_id</code>) dans Sentry, rendant le débogage plus difficile.</li>
<li>Ne pas utiliser <code>before_send</code> pour filtrer des données sensibles qui pourraient se retrouver dans les stack traces ou les variables locales.</li>
</ul>
<h4 style="color: #7FA86E">Repo GitHub de Référence :</h4>
<ul>
<li><a href="https://github.com/getsentry/sentry-python" target="_blank">getsentry/sentry-python - GitHub</a></li>
</ul>
<div class="mermaid" style="width: 100%;">
mindmap
  root["Architecture FastAPI S+++ (2026)"]
    Scalabilité
      Database_Pooling["Connection Pooling (asyncpg)"]
        pool_size["pool_size, max_overflow"]
        pool_recycle["pool_recycle, pre_ping"]
        metrics_pool["Metrics: active, idle, waiting"]
      Rate_Limiting["API Rate Limiting (Sliding Window)"]
        headers_ratelimit["X-RateLimit-* Headers"]
        burst_allowance["Burst Allowance"]
        whitelist_ips["Whitelist IPs"]
      Compression["Gzip/Brotli Compression"]
        threshold_size["Seuil de taille min"]
        exclude_endpoints["Exclusion SSE, /metrics"]
    Sécurité
      Security_Headers["Security Headers Middleware"]
        hsts["HSTS"]
        csp["CSP"]
        x_options["X-Content-Type-Options, X-Frame-Options, X-XSS-Protection"]
        referrer_policy["Referrer-Policy"]
        permissions_policy["Permissions-Policy"]
      JWT_Auth["JWT Authentication"]
        user_id_context["user_id injection (structlog, Sentry)"]
    Observabilité
      Structured_Logging["Structured Logging (structlog)"]
        json_output["JSON (prod), human-readable (dev)"]
        request_id_log["Request ID automatique"]
        user_id_log["User ID injection"]
        timing_perf["Performance Timing (duration)"]
        sensitive_filter["Sensitive Data Filtering"]
        log_levels["Log Levels par module"]
      Request_ID["Request/Correlation ID Middleware"]
        uuid4_generation["Génération UUID4"]
        contextvars_storage["Stockage contextvars"]
        header_propagation["X-Request-ID Header"]
        celery_propagation["Celery Task Propagation"]
      OpenTelemetry_Integration["OpenTelemetry (Traces &amp; Metrics)"]
        auto_instrumentation["FastAPI, asyncpg, Redis, httpx"]
        otlp_exporter["OTLP Collector (prod)"]
        trace_log_correlation["trace_id/span_id dans logs"]
      Error_Tracking["Error Tracking (Sentry-like)"]
        auto_capture_500["Capture automatique 500"]
        context_enrichment["Contexte: user_id, request_id, module, endpoint"]
        breadcrumbs["Breadcrumbs"]
        sensitive_data_sentry["Filtrage données sensibles"]
    Résilience
      Graceful_Shutdown["Arrêt Gracieux (FastAPI, Celery, asyncpg)"]
        signal_handling["Signal Handlers (SIGTERM, SIGINT)"]
        drain_http["Drain connexions HTTP"]
        close_pools["Fermeture pools asyncpg"]
        celery_warm_shutdown["Celery Warm Shutdown"]
        docker_stopsignal["Docker STOPSIGNAL + grace_period"]
      Circuit_Breaker["Circuit Breaker (AI Providers)"]
        three_states["Closed, Open, Half-Open"]
        failure_threshold["Seuil de défaillance configurable"]
        fallback_logic["Fallback automatique (autres providers)"]
        metrics_breaker["Metrics: circuit state, failure count"]
      Health_Checks["Health Checks Avancés (K8s-ready)"]
        liveness_probe["/health/live (app alive)"]
        readiness_probe["/health/ready (DB, Redis)"]
        startup_probe["/health/startup (migrations, modules chargés)"]
</div>
<script id="site_mindmap">mermaid.initialize({ startOnLoad: true });</script>
<p style="text-align: center;"><i>Mindmap de l'architecture S+++ avec les composants clés et leurs interconnexions.</i></p>
<p>Ce mindmap illustre l'interdépendance et le rôle de chaque composant architectural décrit dans ce guide. Il met en évidence comment les différentes couches (sécurité, observabilité, résilience, scalabilité) travaillent ensemble pour former une plateforme SaaS robuste et performante. La couleur des nœuds indique la catégorie générale d'amélioration, tandis que les sous-nœuds détaillent les fonctionnalités spécifiques.</p>
<hr/><h2 id="heading-14" style="color: #cc9900">FAQ (Foire Aux Questions)</h2>
<div class="faq-question">
Comment puis-je tester l'efficacité de ces middlewares ?
</div>
<div class="faq-answer">
Pour tester l'efficacité des middlewares, utilisez des outils comme Postman ou curl pour vérifier les en-têtes de réponse (Security Headers, Rate Limiting, Correlation ID). Pour la compression, comparez la taille des réponses avec et sans le middleware. Pour le circuit breaker, simulez des défaillances des services tiers. Pour le logging et OpenTelemetry, examinez vos logs et vos traces dans votre système d'observabilité (ex: Grafana, Kibana, Jaeger). Des tests unitaires et d'intégration sont également essentiels pour valider la logique de chaque middleware.
</div>
<div class="faq-question">
Ces solutions sont-elles compatibles avec l'approche "modulaire" des 25 modules auto-découverts ?
</div>
<div class="faq-answer">
Oui, absolument. Tous les middlewares et configurations proposés sont conçus pour être ajoutés à votre application FastAPI de manière modulaire, soit via <code>app.add_middleware()</code>, soit en incluant des routeurs spécifiques (pour les health checks), soit en configurant des initialisations au démarrage de l'application (lifespan, OpenTelemetry, Sentry). L'approche par <code>app.add_middleware()</code> ou <code>app.include_router()</code> assure que ces composants s'intègrent sans nécessiter de refactoring massif de vos modules existants.
</div>
<div class="faq-question">
Quel est l'impact de toutes ces améliorations sur les performances ?
</div>
<div class="faq-answer">
Chaque amélioration ajoute une légère surcharge (overhead). Cependant, les bénéfices en termes de sécurité, de résilience et d'observabilité compensent largement cette surcharge. De plus, certaines améliorations (compression, connection pooling) sont des optimisations de performance directes. Il est crucial de surveiller les performances (avec Prometheus et OpenTelemetry) après chaque ajout pour identifier et optimifier les éventuels goulots d'étranglement. Un bon équilibre doit être trouvé entre la sécurité/robustesse et les performances pures.
</div>
<div class="faq-question">
Comment puis-je gérer les secrets (DSN Sentry, URL de base de données) de manière sécurisée ?
</div>
<div class="faq-answer">
Utilisez des variables d'environnement (comme démontré avec <code>os.getenv()</code>) pour tous les secrets et configurations sensibles. En production, ces variables d'environnement doivent être injectées via votre orchestrateur (Kubernetes Secrets, Docker Compose secrets, HashiCorp Vault, AWS Secrets Manager, etc.). Ne jamais les commettre dans votre dépôt de code.
</div>
<div class="faq-question">
Y a-t-il une limite au nombre de middlewares que l'on peut ajouter ?
</div>
<div class="faq-answer">
Techniquement, il n'y a pas de limite stricte. Cependant, chaque middleware ajoute une couche de traitement à chaque requête, augmentant la latence. Une bonne pratique est de n'ajouter que les middlewares absolument nécessaires et d'optimiser leur ordre d'exécution pour minimiser l'impact. Les middlewares qui nécessitent des informations "propres" (ex: pas encore compressées, pas encore routées) devraient venir en premier, tandis que ceux qui agissent sur la réponse finale (ex: compression, security headers) peuvent venir plus tard.
</div>
<hr/><h2 id="heading-15" style="color: #cc9900">Conclusion</h2>
<p>La transformation de votre plateforme SaaS IA en une architecture S+++ de niveau entreprise est un voyage qui implique une attention minutieuse aux détails, une compréhension approfondie des meilleures pratiques et une implémentation rigoureuse. Les solutions fournies dans ce guide, couvrant la sécurité, la scalabilité, l'observabilité et la résilience, sont des étapes concrètes vers cet objectif. En adoptant ces patterns et en les adaptant à votre contexte spécifique, vous construirez une application FastAPI capable de gérer des charges élevées, de résister aux défaillances et de fournir une expérience utilisateur exceptionnelle, tout en restant facile à maintenir et à déboguer.</p>
<hr/><h2 id="heading-16" style="color: #cc9900">Recommandations</h2>
<ul style="list-style-type: none; padding: 20px; background: transparent; width: 100%; margin: -20px;">
<li class="no-bullet-item" style="margin: 15px 0; padding: 0; display: block;">
<a href="/?query=Optimisation des performances FastAPI avec Gunicorn et Uvicorn" onmouseout="this.style.backgroundColor=\'#c90\'; this.style.transform=\'scale(1)\'" onmouseover="this.style.backgroundColor=\'#e0a800\'; this.style.transform=\'scale(1.02)\'" rel="noreferrer noopener nofollow" style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; text-decoration: none; color: white; background-color: #c90; border-radius: 15px; width: 100%; box-sizing: border-box; transition: all 0.2s ease;" target="_blank">
<span>Optimisation des performances FastAPI avec Gunicorn et Uvicorn</span>
<i class="fas fa-arrow-right" style="color: white; margin-left: 15px; font-size: 1.2em;"></i>
</a>
</li>
<li class="no-bullet-item" style="margin: 15px 0; padding: 0; display: block;">
<a href="/?query=Mise en place d'un pipeline CI/CD pour FastAPI avec Kubernetes" onmouseout="this.style.backgroundColor=\'#c90\'; this.style.transform=\'scale(1)\'" onmouseover="this.style.backgroundColor=\'#e0a800\'; this.style.transform=\'scale(1.02)\'" rel="noreferrer noopener nofollow" style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; text-decoration: none; color: white; background-color: #c90; border-radius: 15px; width: 100%; box-sizing: border-box; transition: all 0.2s ease;" target="_blank">
<span>Mise en place d'un pipeline CI/CD pour FastAPI avec Kubernetes</span>
<i class="fas fa-arrow-right" style="color: white; margin-left: 15px; font-size: 1.2em;"></i>
</a>
</li>
<li class="no-bullet-item" style="margin: 15px 0; padding: 0; display: block;">
<a href="/?query=Sécurisation avancée des API FastAPI avec OAuth2 et JWT" onmouseout="this.style.backgroundColor=\'#c90\'; this.style.transform=\'scale(1)\'" onmouseover="this.style.backgroundColor=\'#e0a800\'; this.style.transform=\'scale(1.02)\'" rel="noreferrer noopener nofollow" style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; text-decoration: none; color: white; background-color: #c90; border-radius: 15px; width: 100%; box-sizing: border-box; transition: all 0.2s ease;" target="_blank">
<span>Sécurisation avancée des API FastAPI avec OAuth2 et JWT</span>
<i class="fas fa-arrow-right" style="color: white; margin-left: 15px; font-size: 1.2em;"></i>
</a>
</li>
<li class="no-bullet-item" style="margin: 15px 0; padding: 0; display: block;">
<a href="/?query=Stratégies de monitoring et d'alerting pour FastAPI avec Prometheus et Grafana" onmouseout="this.style.backgroundColor=\'#c90\'; this.style.transform=\'scale(1)\'" onmouseover="this.style.backgroundColor=\'#e0a800\'; this.style.transform=\'scale(1.02)\'" rel="noreferrer noopener nofollow" style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; text-decoration: none; color: white; background-color: #c90; border-radius: 15px; width: 100%; box-sizing: border-box; transition: all 0.2s ease;" target="_blank">
<span>Stratégies de monitoring et d'alerting pour FastAPI avec Prometheus et Grafana</span>
<i class="fas fa-arrow-right" style="color: white; margin-left: 15px; font-size: 1.2em;"></i>
</a>
</li>
</ul>
<hr/><h2 id="heading-17" style="color: #cc9900">Résultats de recherche référencés</h2>
<div class="search-results" style="margin: 30px 0; width: 100%;">
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://gist.github.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">gist.github.com</span>
</div>
<a class="search-result-description" href="https://gist.github.com/joshschmelzle/e44b4476261d3bc641ceda89aa29f00d" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Logging setup for FastAPI, Uvicorn and Structlog (with Datadog ... - Gist
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://wazaari.dev" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">wazaari.dev</span>
</div>
<a class="search-result-description" href="https://wazaari.dev/blog/fastapi-structlog-integration" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Integrating FastAPI with Structlog - Yet Another Techblog
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://oneuptime.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">oneuptime.com</span>
</div>
<a class="search-result-description" href="https://oneuptime.com/blog/post/2026-02-02-fastapi-structured-logging/view" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How to Add Structured Logging to FastAPI - OneUptime
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://apitally.io" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">apitally.io</span>
</div>
<a class="search-result-description" href="https://apitally.io/blog/fastapi-logging-guide" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    A complete guide to logging in FastAPI - Apitally Blog
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://github.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">github.com</span>
</div>
<a class="search-result-description" href="https://github.com/snok/asgi-correlation-id" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    snok/asgi-correlation-id: Request ID propagation for ASGI apps - GitHub
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://ouassim.tech" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">ouassim.tech</span>
</div>
<a class="search-result-description" href="https://ouassim.tech/notes/setting-up-structured-logging-in-fastapi-with-structlog/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Setting Up Structured Logging in FastAPI with structlog - Ouassim G.
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://fastapi.tiangolo.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">fastapi.tiangolo.com</span>
</div>
<a class="search-result-description" href="https://fastapi.tiangolo.com/advanced/middleware/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Advanced Middleware - FastAPI
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://github.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">github.com</span>
</div>
<a class="search-result-description" href="https://github.com/fullonic/brotli-asgi" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    fullonic/brotli-asgi: A compression AGSI middleware using brotli. - GitHub
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://oneuptime.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">oneuptime.com</span>
</div>
<a class="search-result-description" href="https://oneuptime.com/blog/post/2026-02-02-fastapi-async-database/view" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How to Use Async Database Connections in FastAPI - OneUptime
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://python.plainenglish.io" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">python.plainenglish.io</span>
</div>
<a class="search-result-description" href="https://python.plainenglish.io/database-connections-in-fastapi-best-practices-for-efficient-and-scalable-apis-eb0867ed9e7c" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Database Connections in FastAPI: Best Practices for Efficient and ... - Plainenglish.io
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://weirdsheeplabs.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">weirdsheeplabs.com</span>
</div>
<a class="search-result-description" href="https://weirdsheeplabs.com/blog/fast-and-furious-async-testing-with-fastapi-and-pytest" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Fast and furious: async testing with FastAPI and pytest
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://structlog.org" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">structlog.org</span>
</div>
<a class="search-result-description" href="https://www.structlog.org/en/latest/contextvars.html" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Context Variables — structlog UNRELEASED documentation
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://blog.stackademic.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">blog.stackademic.com</span>
</div>
<a class="search-result-description" href="https://blog.stackademic.com/a-deep-dive-into-asynchronous-request-handling-and-concurrency-patterns-in-fastapi-699393bb3845" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    A Deep Dive into Asynchronous Request Handling ... - Stackademic
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://stackoverflow.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">stackoverflow.com</span>
</div>
<a class="search-result-description" href="https://stackoverflow.com/questions/69967439/asyncpg-fastapi-creating-more-connection-than-pool-limit" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    asyncpg/fastapi creating more connection than pool limit
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://medium.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">medium.com</span>
</div>
<a class="search-result-description" href="https://medium.com/@bhagyarana80/how-i-achieved-millisecond-level-latency-in-fastapi-with-http-3-and-brotli-compression-c1f686cf5c42" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How I Achieved Millisecond-Level Latency in FastAPI with HTTP/3 ...
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://pypi.org" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">pypi.org</span>
</div>
<a class="search-result-description" href="https://pypi.org/project/fastapi-structlog/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    fastapi-structlog · PyPI
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://github.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">github.com</span>
</div>
<a class="search-result-description" href="https://github.com/rennf93/fastapi-guard" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    GitHub - rennf93/fastapi-guard: A security library for FastAPI that provides middleware to control IPs, log requests, and detect penetration attempts. It integrates seamlessly with FastAPI to offer robust protection against various security threats. · GitHub
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://github.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">github.com</span>
</div>
<a class="search-result-description" href="https://github.com/fastapi/fastapi/issues/397" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How can I implement a Correlation ID middleware? · Issue #397 ...
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://medium.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">medium.com</span>
</div>
<a class="search-result-description" href="https://medium.com/@sizanmahmud08/securing-your-fastapi-application-with-middleware-a-production-ready-guide-part-2-8a6914f56e24" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Securing Your FastAPI Application with Middleware: A Production-Ready Guide (Part 2) | by Sizan Mahmud | Medium
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://signoz.io" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">signoz.io</span>
</div>
<a class="search-result-description" href="https://signoz.io/guides/structlog/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Complete Guide to Logging with StructLog in Python | SigNoz
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://testdriven.io" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">testdriven.io</span>
</div>
<a class="search-result-description" href="https://testdriven.io/blog/fastapi-sqlmodel/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    FastAPI with Async SQLAlchemy, SQLModel, and Alembic
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://fastapi.tiangolo.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">fastapi.tiangolo.com</span>
</div>
<a class="search-result-description" href="https://fastapi.tiangolo.com/tutorial/middleware/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Middleware - FastAPI
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://leapcell.io" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">leapcell.io</span>
</div>
<a class="search-result-description" href="https://leapcell.io/blog/building-high-performance-async-apis-with-fastapi-sqlalchemy-2-0-and-asyncpg" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Building High-Performance Async APIs with FastAPI, SQLAlchemy ...
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://medium.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">medium.com</span>
</div>
<a class="search-result-description" href="https://medium.com/@abipoongodi1211/fastapi-best-practices-a-complete-guide-for-building-production-ready-apis-bb27062d7617" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    FastAPI Best Practices: A Complete Guide for Building Production ...
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://semaphore.io" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">semaphore.io</span>
</div>
<a class="search-result-description" href="https://semaphore.io/blog/custom-middleware-fastapi" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Building Custom Middleware in FastAPI - Semaphore
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://stackoverflow.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">stackoverflow.com</span>
</div>
<a class="search-result-description" href="https://stackoverflow.com/questions/61153498/what-is-the-good-way-to-provide-an-authentication-in-fastapi" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    What is the good way to provide an authentication in FASTAPI? - Stack Overflow
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://propelauth.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">propelauth.com</span>
</div>
<a class="search-result-description" href="https://www.propelauth.com/post/fastapi-auth-with-dependency-injection" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    FastAPI Auth with Dependency Injection | PropelAuth
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://davidmuraya.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">davidmuraya.com</span>
</div>
<a class="search-result-description" href="https://davidmuraya.com/blog/fastapi-security-guide/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    A Practical Guide to FastAPI Security
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://medium.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">medium.com</span>
</div>
<a class="search-result-description" href="https://medium.com/@hadiyolworld007/fastapi-brotli-gzip-negotiation-smaller-payloads-faster-apis-zero-client-changes-e648b2a1b0d5" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    FastAPI + Brotli/Gzip Negotiation: Smaller Payloads, Faster APIs ...
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://linkedin.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">linkedin.com</span>
</div>
<a class="search-result-description" href="https://www.linkedin.com/pulse/best-practices-creating-fastapi-postgresql-connection-parasuraman-359uc" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Best Practices for Creating a FastAPI and PostgreSQL Connection
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://shipsafer.app" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">shipsafer.app</span>
</div>
<a class="search-result-description" href="https://www.shipsafer.app/blog/fastapi-security-guide" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    FastAPI Security Guide: Auth, Input Validation, and OWASP Best Practices — ShipSafer
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://medium.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">medium.com</span>
</div>
<a class="search-result-description" href="https://medium.com/@diwasb54/building-a-bulletproof-fastapi-middleware-stack-from-development-to-production-in-one-framework-36227c7cc5a3" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Building a Bulletproof FastAPI Middleware Stack: From ... - Medium
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://medium.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">medium.com</span>
</div>
<a class="search-result-description" href="https://medium.com/@devendra631995/starlette-with-fastapi-understanding-the-foundation-and-adding-correlation-ids-for-179c5c65b2d1" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Starlette With FastAPI - And Adding Correlation IDs for… - Medium
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://oneuptime.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">oneuptime.com</span>
</div>
<a class="search-result-description" href="https://oneuptime.com/blog/post/2026-02-02-fastapi-middleware/view" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How to Add Middleware to FastAPI - OneUptime
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://fastapi-guard.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">fastapi-guard.com</span>
</div>
<a class="search-result-description" href="https://fastapi-guard.com/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    FastAPI Guard - Enterprise Security Middleware for FastAPI
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://github.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">github.com</span>
</div>
<a class="search-result-description" href="https://github.com/fastapi/fastapi/discussions/9097" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How to maintain global pool of db connection and use it in each and ...
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://medium.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">medium.com</span>
</div>
<a class="search-result-description" href="https://medium.com/@bhagyarana80/fastapi-with-asyncpostgres-lower-latency-through-native-drivers-ca69ad941cb8" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    FastAPI with AsyncPostgres: Lower Latency Through Native Drivers
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://dev.to" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">dev.to</span>
</div>
<a class="search-result-description" href="https://dev.to/akarshan/asynchronous-database-sessions-in-fastapi-with-sqlalchemy-1o7e" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Asynchronous Database Sessions in FastAPI with SQLAlchemy
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://angelospanag.me" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">angelospanag.me</span>
</div>
<a class="search-result-description" href="https://www.angelospanag.me/blog/structured-logging-using-structlog-and-fastapi" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Structured logging using structlog and FastAPI
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://linkedin.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">linkedin.com</span>
</div>
<a class="search-result-description" href="https://www.linkedin.com/pulse/best-practices-create-middleware-fastapi-manikandan-parasuraman-smt8c" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Best Practices to Create Middleware in FastAPI - LinkedIn
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://oneuptime.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">oneuptime.com</span>
</div>
<a class="search-result-description" href="https://oneuptime.com/blog/post/2026-01-24-configure-api-compression/view" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How to Configure Compression for APIs - OneUptime
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://medium.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">medium.com</span>
</div>
<a class="search-result-description" href="https://medium.com/@sondrelg_12432/setting-up-request-id-logging-for-your-fastapi-application-4dc190aac0ea" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Setting up request ID logging for your FastAPI application | Medium
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://pypi.org" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">pypi.org</span>
</div>
<a class="search-result-description" href="https://pypi.org/project/structlog-config/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    structlog-config · PyPI
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://reddit.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">reddit.com</span>
</div>
<a class="search-result-description" href="https://www.reddit.com/r/Python/comments/1ilhbkk/fastapi_guard_a_fastapi_extension_to_secure_your/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    r/Python on Reddit: FastAPI Guard - A FastAPI extension to secure your APIs
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://reddit.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">reddit.com</span>
</div>
<a class="search-result-description" href="https://www.reddit.com/r/FastAPI/comments/pi0zdy/best_approach_for_async_sqlalchemy_in_fastapi/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Best approach for async SQLAlchemy in FastAPI - Reddit
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://gealber.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">gealber.com</span>
</div>
<a class="search-result-description" href="https://gealber.com/building-brotli-middleware-fastapi" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Building a Brotli Middleware with FastAPI - Gealber el calvo lindo
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://ssojet.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">ssojet.com</span>
</div>
<a class="search-result-description" href="https://ssojet.com/compression/compress-files-with-gzip-in-fastapi" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Compress Files with gzip in FastAPI - SSOJet
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://medium.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">medium.com</span>
</div>
<a class="search-result-description" href="https://medium.com/@chandanp20k/leveraging-custom-middleware-in-python-fastapi-for-enhanced-web-development-09ba72b5ddc6" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Securing FastAPI: Implementing Token Authentication with Custom Middleware | by Chandan p | Medium
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://spwoodcock.dev" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">spwoodcock.dev</span>
</div>
<a class="search-result-description" href="https://spwoodcock.dev/blog/2024-10-fastapi-pydantic-psycopg/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    FastAPI, Pydantic, Psycopg3: The Ultimate Trio for Python Web APIs
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://fastapi.tiangolo.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">fastapi.tiangolo.com</span>
</div>
<a class="search-result-description" href="https://fastapi.tiangolo.com/tutorial/security/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Security - FastAPI
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://auth0.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">auth0.com</span>
</div>
<a class="search-result-description" href="https://auth0.com/blog/build-and-secure-fastapi-server-with-auth0/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Build and Secure a FastAPI Server with Auth0
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://dba.stackexchange.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">dba.stackexchange.com</span>
</div>
<a class="search-result-description" href="https://dba.stackexchange.com/questions/36828/how-to-best-use-connection-pooling-in-sqlalchemy-for-pgbouncer-transaction-level" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How to best use connection pooling in SQLAlchemy for PgBouncer ...
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://blog.danielclayton.co.uk" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">blog.danielclayton.co.uk</span>
</div>
<a class="search-result-description" href="https://blog.danielclayton.co.uk/posts/database-connections-with-fastapi/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Psycopg Database Connections with FastAPI - Dan Clayton's Blog
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://shiladityamajumder.medium.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">shiladityamajumder.medium.com</span>
</div>
<a class="search-result-description" href="https://shiladityamajumder.medium.com/async-apis-with-fastapi-patterns-pitfalls-best-practices-2d72b2b66f25" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Async APIs with FastAPI: Patterns, Pitfalls &amp; Best Practices
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://reddit.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">reddit.com</span>
</div>
<a class="search-result-description" href="https://www.reddit.com/r/node/comments/1px3bog/enabling_gzip_brotli_gave_me_3040_faster_api/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Enabling Gzip + Brotli gave me ~30–40% faster API responses : r/node
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://davidmuraya.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">davidmuraya.com</span>
</div>
<a class="search-result-description" href="https://www.davidmuraya.com/blog/adding-middleware-to-fastapi-applications/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    6 Essential FastAPI Middlewares for Production-Ready Apps
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://gist.github.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">gist.github.com</span>
</div>
<a class="search-result-description" href="https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Logging setup for FastAPI, Uvicorn and Structlog (with Datadog ...
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://github.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">github.com</span>
</div>
<a class="search-result-description" href="https://github.com/code-specialist/fastapi-auth-middleware" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    code-specialist/fastapi-auth-middleware - GitHub
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://oneuptime.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">oneuptime.com</span>
</div>
<a class="search-result-description" href="https://oneuptime.com/blog/post/2025-01-06-python-connection-pooling-postgresql/view" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How to Implement Connection Pooling in Python for PostgreSQL
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://fastapi.tiangolo.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">fastapi.tiangolo.com</span>
</div>
<a class="search-result-description" href="https://fastapi.tiangolo.com/tutorial/security/first-steps/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Security - First Steps - FastAPI
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://fastapi.tiangolo.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">fastapi.tiangolo.com</span>
</div>
<a class="search-result-description" href="https://fastapi.tiangolo.com/async/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Concurrency and async / await - FastAPI
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://dev.to" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">dev.to</span>
</div>
<a class="search-result-description" href="https://dev.to/gealber/gzip-middleware-recipe-for-fastapi-4b14" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Gzip Middleware recipe for FastAPI - DEV Community
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://escape.tech" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">escape.tech</span>
</div>
<a class="search-result-description" href="https://escape.tech/blog/how-to-secure-fastapi-api/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How to secure APIs built with FastAPI: A complete guide
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://pysolutions.dev" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">pysolutions.dev</span>
</div>
<a class="search-result-description" href="https://pysolutions.dev/blog/fastapi-async-vs-sync-performance" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    FastAPI Performance Deep Dive: Async vs Sync Operations for ...
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://dev.to" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">dev.to</span>
</div>
<a class="search-result-description" href="https://dev.to/githubopensource/supercharge-your-fastapi-security-with-fastapi-guard-46b9" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Supercharge Your FastAPI Security with fastapi-guard! - DEV Community
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://asifmuhammad.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">asifmuhammad.com</span>
</div>
<a class="search-result-description" href="https://asifmuhammad.com/articles/database-pooling-fastapi" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    Database Connection Pooling in FastAPI with SQLAlchemy
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://reddit.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">reddit.com</span>
</div>
<a class="search-result-description" href="https://www.reddit.com/r/learnpython/comments/w5glaa/how_to_use_a_database_connection_pool/" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How to use a database connection pool effectively?[long *** post]
                                </a>
</div>
<div class="search-result" style="margin-bottom: 20px; font-family: Arial, sans-serif;">
<div style="display: flex; align-items: center; margin-bottom: 3px;">
<img alt="" src="https://t3.gstatic.com/faviconV2?client=SOCIAL&amp;type=FAVICON&amp;fallback_opts=TYPE,SIZE,URL&amp;url=https://oneuptime.com" style="width: 16px; height: 16px; margin: auto 10px;"/>
<span class="search-result-title" style="font-size: 14px;">oneuptime.com</span>
</div>
<a class="search-result-description" href="https://oneuptime.com/blog/post/2026-01-25-fastapi-authentication-middleware/view" rel="noreferrer noopener nofollow" style="font-size: 18px; text-decoration: none; display: block; margin: 0 0 3px 36px; font-weight: 400; line-height: 1.3;" target="_blank">
                                    How to Build Authentication Middleware in FastAPI
                                </a>
</div>
</div>
<div data-slug="fastapi-saas-architecture-s-plus-plus-plus"></div></div><a class="article-date">Last updated March 24, 2026</a>
<script>
function detectRTL(text) {
  const rtlChars = /[֑-߿‏‫‮יִ-﷽ﹰ-ﻼ]/g;
  const matches = text.match(rtlChars) || [];
  return matches.length > 100;
}
const isRTL = detectRTL(document.documentElement.innerHTML);
if (isRTL) {
  document.body.classList.add('rtl-support');
  document.body.setAttribute('dir', 'rtl');
}
document.addEventListener("DOMContentLoaded", (event) => {window.print()});
</script>
</body>
</html>
```

