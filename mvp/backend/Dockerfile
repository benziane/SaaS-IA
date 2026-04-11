# ──────────────────────────────────────────────────────────────
#  SaaS-IA Backend – Multi-stage production Dockerfile
# ──────────────────────────────────────────────────────────────

# ── Stage 1: builder ─────────────────────────────────────────
FROM python:3.14-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
        curl \
        git \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv — fast Python package manager (replaces pip for dependency resolution)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    UV_SYSTEM_PYTHON=0 \
    UV_PROJECT_ENVIRONMENT=/opt/venv

COPY requirements.txt /tmp/requirements.txt
# lxml 6.x override — crawl4ai and streamlink try to pull lxml<6 which has no Py3.14 wheel
# We force lxml>=6.0.0 via uv override, bypassing transitive pins
RUN echo "lxml>=6.0.0" > /tmp/lxml_override.txt
RUN uv pip install --no-cache \
        --override /tmp/lxml_override.txt \
        -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt /tmp/lxml_override.txt

# Install Playwright browser so web_crawler module works
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN playwright install chromium --with-deps \
    && chmod -R 755 /ms-playwright


# ── Stage 2: runtime ────────────────────────────────────────
FROM python:3.14-slim AS runtime

LABEL org.opencontainers.image.title="saas-ia-backend" \
      org.opencontainers.image.description="SaaS-IA AI Platform – FastAPI backend" \
      org.opencontainers.image.vendor="SaaS-IA" \
      org.opencontainers.image.source="https://github.com/saas-ia/saas-ia"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Runtime-only system dependencies (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        tini \
        ffmpeg \
        # Playwright/Chromium runtime dependencies
        libnss3 \
        libatk-bridge2.0-0 \
        libdrm2 \
        libxkbcommon0 \
        libgbm1 \
        libasound2 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libxfixes3 \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy Playwright browsers from builder
COPY --from=builder /ms-playwright /ms-playwright

WORKDIR /app

# Create non-root user
RUN useradd --no-log-init -r -m -u 1001 appuser \
    && chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser scripts ./scripts
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini ./alembic.ini
COPY --chown=appuser:appuser pyproject.toml ./pyproject.toml

USER appuser

EXPOSE 8000

STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
