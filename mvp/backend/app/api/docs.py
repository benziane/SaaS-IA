"""OpenAPI schema enrichment for SaaS-IA API documentation."""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

TAGS_METADATA = [
    {"name": "Authentication", "description": "JWT-based auth (login, register, refresh, me)"},
    {"name": "AI Assistant", "description": "Multi-provider AI text processing (Gemini, Claude, Groq)"},
    {"name": "Transcription", "description": "YouTube/audio/video transcription with speaker diarization"},
    {"name": "Conversation", "description": "Contextual AI chat with history"},
    {"name": "Knowledge", "description": "Document upload, chunking, hybrid search (pgvector + TF-IDF)"},
    {"name": "Compare", "description": "Multi-model comparison with voting"},
    {"name": "Pipelines", "description": "Sequential AI operation chaining (23 step types)"},
    {"name": "Agents", "description": "Autonomous AI agents with planning and 65 actions"},
    {"name": "Sentiment", "description": "Text sentiment analysis (RoBERTa + LLM)"},
    {"name": "Web Crawler", "description": "Web scraping with Crawl4AI + Jina Reader fallback"},
    {"name": "Workspaces", "description": "Collaborative spaces with members and comments"},
    {"name": "Billing", "description": "Stripe integration (Free/Pro/Enterprise plans)"},
    {"name": "API Keys", "description": "Public API key management (SHA-256)"},
    {"name": "Cost Tracker", "description": "AI usage cost tracking per provider/module/user"},
    {"name": "Content Studio", "description": "Multi-format content generation (10 formats)"},
    {"name": "AI Workflows", "description": "No-code DAG automation engine (26 action types)"},
    {"name": "Multi-Agent Crew", "description": "Collaborative agent teams (9 roles)"},
    {"name": "Voice Clone", "description": "TTS + voice cloning (OpenAI/Coqui)"},
    {"name": "Realtime AI", "description": "Real-time voice/vision sessions (LiveKit)"},
    {"name": "Security Guardian", "description": "PII detection (Presidio) + prompt injection (NeMo)"},
    {"name": "Image Gen", "description": "AI image generation (10 styles) + Real-ESRGAN upscaling"},
    {"name": "Data Analyst", "description": "CSV/JSON analysis with DuckDB + NL queries"},
    {"name": "Video Gen", "description": "Text-to-video generation (6 types) + ffmpeg"},
    {"name": "Fine-Tuning", "description": "LoRA training (Unsloth) + evaluation (lm-eval)"},
    {"name": "AI Monitoring", "description": "LLM observability (Langfuse + OpenTelemetry)"},
    {"name": "Unified Search", "description": "Cross-module search (Meilisearch + PostgreSQL)"},
    {"name": "AI Memory", "description": "Persistent memory (Mem0 + DB)"},
    {"name": "Social Publisher", "description": "Multi-platform social media publishing"},
    {"name": "Integration Hub", "description": "External connectors with webhooks"},
    {"name": "AI Chatbot Builder", "description": "RAG chatbots with embed deployment"},
    {"name": "Marketplace", "description": "Module/template/prompt marketplace"},
    {"name": "Presentation Gen", "description": "AI slide generation (5 templates)"},
    {"name": "Code Sandbox", "description": "Secure code execution + AI debug"},
    {"name": "AI Forms", "description": "Conversational forms with AI generation"},
    {"name": "Health", "description": "Kubernetes health probes (live/ready/startup)"},
    {"name": "Public API v1", "description": "External API with API key authentication"},
]

API_DESCRIPTION = """\
# SaaS-IA API

Modular AI platform with **33 modules**, **~270 endpoints**, and enterprise-grade
infrastructure.

## Authentication

Most endpoints require a **JWT Bearer token** obtained via `POST /api/auth/login`.

```
Authorization: Bearer <access_token>
```

The **Public API v1** (`/v1/*`) uses an **API key** passed in the `X-API-Key` header.

## Rate Limiting

Every endpoint is rate-limited (sliding window). Limits are noted in each
endpoint description. A global middleware also enforces per-IP limits.

When a limit is exceeded the API returns **429 Too Many Requests**.

## AI Providers

Requests that involve AI processing are routed through the **AI Router** which
auto-selects the best provider based on content classification:

| Provider | Model | Use Case |
|----------|-------|----------|
| Gemini | 2.0 Flash | General, multilingual, vision |
| Claude | Sonnet | Complex reasoning, sensitive content |
| Groq | Llama 3.3 70B | Fast inference, cost-optimized |

## Modules Overview

| Group | Modules |
|-------|---------|
| **Core** | Auth, AI Assistant, Transcription, Conversation, Knowledge, Compare, Pipelines, Agents, Sentiment, Web Crawler, Workspaces, Billing, API Keys, Cost Tracker |
| **Content & Automation** | Content Studio, AI Workflows |
| **Intelligence & Safety** | Multi-Agent Crew, Voice Clone, Realtime AI, Security Guardian |
| **Media** | Image Gen, Data Analyst, Video Gen |
| **Custom Models** | Fine-Tuning |
| **Platform** | AI Monitoring, Unified Search, AI Memory |
| **Growth** | Social Publisher, Integration Hub, AI Chatbot Builder, Marketplace, Presentation Gen, Code Sandbox, AI Forms |

## WebSocket Endpoints

- `WS /api/transcription/debug/{job_id}` -- real-time transcription debug stream

## Error Responses

All errors follow the standard format:

```json
{
  "detail": "Human-readable error message"
}
```

Common status codes: `400` (validation), `401` (unauthenticated), `403` (forbidden),
`404` (not found), `413` (too large), `429` (rate limited), `500` (server error).
"""

SERVERS = [
    {
        "url": "http://localhost:8004",
        "description": "Development server",
    },
    {
        "url": "https://staging-api.saas-ia.com",
        "description": "Staging server",
    },
    {
        "url": "https://api.saas-ia.com",
        "description": "Production server",
    },
]

CONTACT = {
    "name": "SaaS-IA Team",
    "url": "https://saas-ia.com",
    "email": "support@saas-ia.com",
}

LICENSE_INFO = {
    "name": "Proprietary",
}

EXTERNAL_DOCS = {
    "description": "Full documentation and guides",
    "url": "https://docs.saas-ia.com",
}


def custom_openapi(app: FastAPI) -> dict:
    """Generate an enriched OpenAPI schema for the SaaS-IA platform.

    Calling this function replaces the default schema with one that includes
    detailed descriptions, server URLs, security schemes, and tag metadata.
    The result is cached on ``app.openapi_schema`` so subsequent calls are free.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="SaaS-IA API",
        version="3.9.0",
        description=API_DESCRIPTION,
        routes=app.routes,
        tags=TAGS_METADATA,
        contact=CONTACT,
        license_info=LICENSE_INFO,
    )

    # Servers
    openapi_schema["servers"] = SERVERS

    # External docs
    openapi_schema["externalDocs"] = EXTERNAL_DOCS

    # Security schemes
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": (
                "JWT access token obtained via POST /api/auth/login. "
                "Include in the Authorization header: `Bearer <token>`."
            ),
        },
        "APIKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": (
                "API key for the Public API v1 (/v1/*). "
                "Create keys via POST /api/keys. "
                "Keys are SHA-256 hashed at rest."
            ),
        },
    }

    # Default security (JWT) -- individual endpoints can override
    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema
