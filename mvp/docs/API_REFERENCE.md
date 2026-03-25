# API Reference - SaaS-IA Platform

> **Version**: 3.9.0 | **Base URL**: `http://localhost:8004` (dev) | **Interactive docs**: `/docs` (Swagger), `/redoc` (ReDoc)

## Authentication

| Method | Header | Used by |
|--------|--------|---------|
| JWT Bearer | `Authorization: Bearer <access_token>` | All `/api/*` endpoints |
| API Key | `X-API-Key: sk-...` | Public API `/v1/*` endpoints |

---

## Root & Health

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/` | API info and version | No | - |
| GET | `/health` | Basic health check | No | 100/min |
| GET | `/health/live` | Kubernetes liveness probe | No | - |
| GET | `/health/ready` | Kubernetes readiness probe (Postgres + Redis) | No | - |
| GET | `/health/startup` | Kubernetes startup probe | No | - |
| GET | `/api/modules` | List registered modules | No | - |
| GET | `/metrics` | Prometheus metrics (dev or X-Metrics-Token) | Token | - |

---

## Authentication (`/api/auth`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/auth/register` | Register a new user | No | 5/min |
| POST | `/api/auth/login` | Login (OAuth2 form), get JWT + refresh token | No | 5/min |
| POST | `/api/auth/refresh` | Refresh expired access token | No | 5/min |
| GET | `/api/auth/me` | Get current user profile | Yes | 20/min |
| PUT | `/api/auth/profile` | Update user profile (full_name) | Yes | 20/min |
| PUT | `/api/auth/password` | Change password | Yes | 3/min |

---

## AI Assistant (`/api/ai-assistant`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/ai-assistant/providers` | List available AI providers | Yes | - |
| POST | `/api/ai-assistant/process-text` | Process text with AI | Yes | - |
| POST | `/api/ai-assistant/stream` | Stream AI text processing (SSE) | Yes | - |
| GET | `/api/ai-assistant/health` | AI Assistant module health | No | - |
| POST | `/api/ai-assistant/classify-content` | Classify content (debug) | Yes | - |
| POST | `/api/ai-assistant/classify-batch` | Batch classify multiple texts | Yes | - |

---

## Transcription (`/api/transcription`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/transcription/` | Create transcription job (YouTube/URL) | Yes | 10/min |
| POST | `/api/transcription/upload` | Upload audio/video file for transcription | Yes | 5/min |
| GET | `/api/transcription/` | List transcriptions (paginated) | Yes | 20/min |
| GET | `/api/transcription/stats` | User transcription statistics | Yes | 20/min |
| GET | `/api/transcription/{job_id}` | Get transcription by ID | Yes | 30/min |
| GET | `/api/transcription/{job_id}/speakers` | Get transcription with speaker diarization | Yes | 20/min |
| DELETE | `/api/transcription/{job_id}` | Delete transcription | Yes | 10/min |
| POST | `/api/transcription/smart-transcribe` | Smart transcription with provider routing | Yes | 10/min |
| POST | `/api/transcription/metadata` | Extract YouTube video metadata | Yes | 20/min |
| POST | `/api/transcription/playlist` | Transcribe YouTube playlist | Yes | 3/min |
| POST | `/api/transcription/auto-chapter` | Auto-chaptering with summaries | Yes | 5/min |
| POST | `/api/transcription/stream/status` | Check live stream status | Yes | 20/min |
| POST | `/api/transcription/stream/capture` | Capture live stream segment | Yes | 2/min |
| POST | `/api/transcription/video/analyze` | Analyze video frames with Vision AI | Yes | 3/min |
| WS | `/api/transcription/debug/{job_id}` | WebSocket debug stream (dev only) | No | - |
| GET | `/api/transcription/debug/{job_id}/audio` | Download cached debug audio | Yes | - |
| POST | `/api/transcription/debug/transcribe/{job_id}` | Synchronous debug transcription | Yes | - |
| POST | `/api/transcription/debug/run-backend-test` | Run backend test script | Yes | - |

---

## Conversation (`/api/conversations`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/conversations/` | Create conversation (optionally linked to transcription) | Yes | 10/min |
| GET | `/api/conversations/` | List conversations (paginated) | Yes | 30/min |
| GET | `/api/conversations/{id}` | Get conversation with messages | Yes | 30/min |
| DELETE | `/api/conversations/{id}` | Delete conversation and messages | Yes | 10/min |
| POST | `/api/conversations/{id}/messages` | Send message, get AI reply (SSE) | Yes | 20/min |

---

## Knowledge Base (`/api/knowledge`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/knowledge/upload` | Upload document (TXT, MD, CSV; max 10 MB) | Yes | 5/min |
| GET | `/api/knowledge/documents` | List user documents | Yes | 20/min |
| GET | `/api/knowledge/documents/{id}/chunks` | List document chunks | Yes | 20/min |
| DELETE | `/api/knowledge/documents/{id}` | Delete document and chunks | Yes | 10/min |
| POST | `/api/knowledge/search` | Hybrid search (auto-detect best mode) | Yes | 20/min |
| POST | `/api/knowledge/search/vector` | Vector-only search (pgvector) | Yes | 20/min |
| POST | `/api/knowledge/ask` | RAG query (search + AI answer) | Yes | 10/min |
| POST | `/api/knowledge/reindex-embeddings` | Reindex chunks with embeddings | Yes | 1/min |
| GET | `/api/knowledge/search/status` | Search modes availability | No | - |

---

## Compare (`/api/compare`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/compare/run` | Run prompt across multiple providers | Yes | 5/min |
| POST | `/api/compare/{id}/vote` | Vote for best provider response | Yes | 10/min |
| GET | `/api/compare/stats` | Aggregated provider quality stats | Yes | 20/min |

---

## Pipelines (`/api/pipelines`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/pipelines/` | Create pipeline | Yes | 10/min |
| GET | `/api/pipelines/` | List pipelines | Yes | 20/min |
| GET | `/api/pipelines/{id}` | Get pipeline | Yes | 30/min |
| PUT | `/api/pipelines/{id}` | Update pipeline | Yes | 10/min |
| DELETE | `/api/pipelines/{id}` | Delete pipeline | Yes | 10/min |
| POST | `/api/pipelines/{id}/execute` | Execute pipeline | Yes | 3/min |
| GET | `/api/pipelines/{id}/executions` | List pipeline executions | Yes | 20/min |
| GET | `/api/pipelines/executions/{id}` | Get execution details | Yes | 30/min |

---

## Agents (`/api/agents`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/agents/run` | Execute autonomous AI agent | Yes | 5/min |
| POST | `/api/agents/react` | Run ReAct agent (reason + act loop) | Yes | 3/min |
| GET | `/api/agents/runs` | List agent runs | Yes | 20/min |
| GET | `/api/agents/runs/{id}` | Get agent run with steps | Yes | 30/min |
| POST | `/api/agents/runs/{id}/cancel` | Cancel running agent | Yes | 10/min |

---

## Sentiment (`/api/sentiment`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/sentiment/analyze` | Analyze text sentiment and emotions | Yes | 10/min |
| POST | `/api/sentiment/transcription` | Analyze transcription sentiment | Yes | 5/min |

---

## Web Crawler (`/api/crawler`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/crawler/scrape` | Scrape URL, extract markdown + images | Yes | 10/min |
| POST | `/api/crawler/scrape-vision` | Scrape + AI vision analysis of images | Yes | 3/min |
| POST | `/api/crawler/index` | Crawl URL and index into Knowledge Base | Yes | 3/min |

---

## Workspaces (`/api/workspaces`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/workspaces/` | Create workspace | Yes | 10/min |
| GET | `/api/workspaces/` | List workspaces | Yes | 20/min |
| GET | `/api/workspaces/{id}` | Get workspace | Yes | 30/min |
| PUT | `/api/workspaces/{id}` | Update workspace (owner) | Yes | 10/min |
| DELETE | `/api/workspaces/{id}` | Delete workspace (owner) | Yes | 5/min |
| POST | `/api/workspaces/{id}/invite` | Invite member by email | Yes | 10/min |
| GET | `/api/workspaces/{id}/members` | List members | Yes | 20/min |
| DELETE | `/api/workspaces/{id}/members/{user_id}` | Remove member (owner) | Yes | 10/min |
| POST | `/api/workspaces/{id}/share` | Share item to workspace | Yes | 10/min |
| GET | `/api/workspaces/{id}/items` | List shared items | Yes | 20/min |
| GET | `/api/workspaces/items/{id}/detail` | Get shared item content | Yes | 20/min |
| POST | `/api/workspaces/items/{id}/comments` | Add comment on shared item | Yes | 20/min |
| GET | `/api/workspaces/items/{id}/comments` | List comments | Yes | 30/min |

---

## Billing (`/api/billing`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/billing/plans` | List subscription plans | No | 30/min |
| GET | `/api/billing/quota` | Get current user quota and usage | Yes | 30/min |
| POST | `/api/billing/checkout` | Create Stripe checkout session | Yes | 5/min |
| POST | `/api/billing/portal` | Create Stripe billing portal session | Yes | 5/min |
| POST | `/api/billing/webhook` | Stripe webhook receiver | No | - |

---

## API Keys (`/api/keys`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/keys/` | Create API key (returned once in plaintext) | Yes | 5/min |
| GET | `/api/keys/` | List API keys (prefix only) | Yes | 20/min |
| DELETE | `/api/keys/{id}` | Revoke API key | Yes | 10/min |

---

## Cost Tracker (`/api/costs`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/costs/dashboard` | Cost dashboard with breakdowns | Yes | 20/min |
| GET | `/api/costs/alerts` | Budget alerts and spending warnings | Yes | 20/min |
| GET | `/api/costs/export` | Export usage logs as CSV | Yes | 5/min |

---

## Content Studio (`/api/content-studio`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/content-studio/projects` | Create content project | Yes | 10/min |
| GET | `/api/content-studio/projects` | List projects | Yes | 20/min |
| DELETE | `/api/content-studio/projects/{id}` | Delete project | Yes | 10/min |
| POST | `/api/content-studio/projects/{id}/generate` | Generate content in multiple formats | Yes | 5/min |
| GET | `/api/content-studio/projects/{id}/contents` | Get project contents | Yes | 20/min |
| PUT | `/api/content-studio/contents/{id}` | Update content piece | Yes | 10/min |
| POST | `/api/content-studio/contents/{id}/regenerate` | Regenerate content | Yes | 5/min |
| POST | `/api/content-studio/from-url` | Crawl URL and generate content | Yes | 3/min |
| GET | `/api/content-studio/formats` | List available content formats | No | - |

---

## AI Workflows (`/api/workflows`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/workflows/` | Create workflow (DAG validated) | Yes | 10/min |
| GET | `/api/workflows/` | List workflows | Yes | 20/min |
| GET | `/api/workflows/templates` | List workflow templates | No | - |
| POST | `/api/workflows/from-template/{id}` | Create from template | Yes | 10/min |
| POST | `/api/workflows/validate` | Validate DAG (cycle + connectivity check) | No | - |
| GET | `/api/workflows/{id}` | Get workflow | Yes | 30/min |
| PUT | `/api/workflows/{id}` | Update workflow | Yes | 10/min |
| DELETE | `/api/workflows/{id}` | Delete workflow | Yes | 10/min |
| POST | `/api/workflows/{id}/run` | Trigger workflow execution | Yes | 3/min |
| GET | `/api/workflows/{id}/runs` | List workflow runs | Yes | 20/min |
| GET | `/api/workflows/runs/{id}` | Get run details | Yes | 30/min |

---

## Multi-Agent Crew (`/api/crews`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/crews/` | Create agent crew | Yes | 10/min |
| GET | `/api/crews/` | List crews | Yes | 20/min |
| GET | `/api/crews/templates` | List crew templates | No | - |
| POST | `/api/crews/from-template/{id}` | Create from template | Yes | 10/min |
| GET | `/api/crews/{id}` | Get crew | Yes | 30/min |
| PUT | `/api/crews/{id}` | Update crew | Yes | 10/min |
| DELETE | `/api/crews/{id}` | Delete crew | Yes | 10/min |
| POST | `/api/crews/{id}/run` | Run crew with instruction | Yes | 3/min |
| GET | `/api/crews/{id}/runs` | List crew runs | Yes | 20/min |

---

## Voice Clone (`/api/voice`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/voice/profiles` | Create voice profile (optional audio sample) | Yes | 5/min |
| GET | `/api/voice/profiles` | List voice profiles | Yes | 20/min |
| DELETE | `/api/voice/profiles/{id}` | Delete voice profile | Yes | 10/min |
| POST | `/api/voice/synthesize` | Text-to-speech synthesis | Yes | 5/min |
| POST | `/api/voice/synthesize-source` | TTS from transcription/document | Yes | 3/min |
| POST | `/api/voice/dub` | Dub content to another language | Yes | 2/min |
| GET | `/api/voice/syntheses` | List synthesis history | Yes | 20/min |
| GET | `/api/voice/voices` | List built-in voices | No | - |

---

## Realtime AI (`/api/realtime`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/realtime/sessions` | Create realtime AI session | Yes | 10/min |
| GET | `/api/realtime/sessions` | List sessions | Yes | 20/min |
| GET | `/api/realtime/sessions/{id}` | Get session details | Yes | 30/min |
| POST | `/api/realtime/sessions/{id}/message` | Send message, get AI response | Yes | 30/min |
| POST | `/api/realtime/sessions/{id}/end` | End session and generate summary | Yes | 10/min |
| GET | `/api/realtime/sessions/{id}/transcript` | Get full session transcript | Yes | 20/min |
| GET | `/api/realtime/config` | Available realtime config options | No | - |

---

## Security Guardian (`/api/security`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/security/scan` | Scan for PII, injection, safety issues | Yes | 10/min |
| GET | `/api/security/dashboard` | Security overview dashboard | Yes | 20/min |
| GET | `/api/security/audit` | List audit log entries (filterable) | Yes | 20/min |
| POST | `/api/security/guardrails` | Create guardrail rule | Yes | 10/min |
| GET | `/api/security/guardrails` | List guardrail rules | Yes | 20/min |
| PUT | `/api/security/guardrails/{id}` | Update guardrail rule | Yes | 10/min |
| DELETE | `/api/security/guardrails/{id}` | Delete guardrail rule | Yes | 10/min |

---

## Image Gen (`/api/images`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/images/generate` | Generate image from prompt | Yes | 5/min |
| POST | `/api/images/thumbnail` | Generate YouTube thumbnail | Yes | 5/min |
| POST | `/api/images/bulk` | Bulk generate multiple images | Yes | 2/min |
| GET | `/api/images/` | List generated images | Yes | 20/min |
| DELETE | `/api/images/{id}` | Delete image | Yes | 10/min |
| POST | `/api/images/{id}/upscale` | Upscale with Real-ESRGAN | Yes | 3/min |
| POST | `/api/images/projects` | Create image project | Yes | 10/min |
| GET | `/api/images/projects` | List image projects | Yes | 20/min |
| GET | `/api/images/styles` | List available styles (10) | No | - |

---

## Data Analyst (`/api/data`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/data/datasets` | Upload dataset (CSV, JSON, Excel) | Yes | 5/min |
| GET | `/api/data/datasets` | List datasets | Yes | 20/min |
| GET | `/api/data/datasets/{id}` | Get dataset with preview | Yes | 30/min |
| DELETE | `/api/data/datasets/{id}` | Delete dataset and analyses | Yes | 10/min |
| POST | `/api/data/datasets/{id}/ask` | Natural language query | Yes | 5/min |
| POST | `/api/data/datasets/{id}/auto-analyze` | Automatic analysis | Yes | 3/min |
| POST | `/api/data/datasets/{id}/report` | Generate comprehensive report | Yes | 2/min |
| GET | `/api/data/datasets/{id}/analyses` | List analyses for dataset | Yes | 20/min |

---

## Video Gen (`/api/videos`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/videos/generate` | Generate video from text prompt | Yes | 3/min |
| POST | `/api/videos/clips` | Generate highlight clips from transcription | Yes | 2/min |
| POST | `/api/videos/avatar` | Generate talking avatar video | Yes | 3/min |
| POST | `/api/videos/from-source` | Generate from transcription/document | Yes | 3/min |
| GET | `/api/videos/` | List generated videos | Yes | 20/min |
| DELETE | `/api/videos/{id}` | Delete video | Yes | 10/min |
| POST | `/api/videos/projects` | Create video project | Yes | 10/min |
| GET | `/api/videos/projects` | List video projects | Yes | 20/min |
| GET | `/api/videos/types` | List available video types (6) | No | - |

---

## Fine-Tuning (`/api/fine-tuning`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/fine-tuning/datasets` | Create training dataset | Yes | 10/min |
| POST | `/api/fine-tuning/datasets/from-source` | Create from platform data | Yes | 3/min |
| GET | `/api/fine-tuning/datasets` | List datasets | Yes | 20/min |
| GET | `/api/fine-tuning/datasets/{id}` | Get dataset details | Yes | 30/min |
| POST | `/api/fine-tuning/datasets/{id}/samples` | Add samples to dataset | Yes | 10/min |
| POST | `/api/fine-tuning/datasets/{id}/assess-quality` | AI quality assessment | Yes | 3/min |
| DELETE | `/api/fine-tuning/datasets/{id}` | Delete dataset | Yes | 10/min |
| POST | `/api/fine-tuning/jobs` | Create and start fine-tuning job | Yes | 3/min |
| GET | `/api/fine-tuning/jobs` | List jobs | Yes | 20/min |
| GET | `/api/fine-tuning/jobs/{id}` | Get job details | Yes | 30/min |
| POST | `/api/fine-tuning/jobs/{id}/evaluate` | Evaluate fine-tuned model | Yes | 3/min |
| GET | `/api/fine-tuning/jobs/{id}/evaluations` | List evaluations | Yes | 20/min |
| GET | `/api/fine-tuning/models` | List available base models | No | - |

---

## AI Monitoring (`/api/monitoring`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/monitoring/dashboard` | LLM observability dashboard | Yes | 20/min |
| GET | `/api/monitoring/providers` | Compare providers (latency, cost, quality) | Yes | 20/min |
| GET | `/api/monitoring/traces` | Recent AI call traces | Yes | 20/min |
| POST | `/api/monitoring/langfuse/traces` | Create Langfuse trace | Yes | 30/min |
| POST | `/api/monitoring/langfuse/generations` | Create Langfuse generation | Yes | 30/min |
| POST | `/api/monitoring/langfuse/scores` | Score Langfuse generation | Yes | 30/min |
| GET | `/api/monitoring/langfuse/status` | Langfuse integration status | Yes | 20/min |
| POST | `/api/monitoring/langfuse/flush` | Flush Langfuse pending events | Yes | 5/min |

---

## Unified Search (`/api/search`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/search/` | Universal cross-module search | Yes | 30/min |
| GET | `/api/search/answer` | Cross-module RAG (search + synthesize) | Yes | 10/min |
| GET | `/api/search/status` | Search engine status | Yes | 30/min |
| POST | `/api/search/index` | Index document in Meilisearch | Yes | 60/min |
| POST | `/api/search/reindex/{module}` | Rebuild index for a module | Yes | 5/min |

---

## AI Memory (`/api/memory`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/memory/` | Add memory entry | Yes | 20/min |
| GET | `/api/memory/` | List memories (filterable by type) | Yes | 20/min |
| DELETE | `/api/memory/{id}` | Delete memory | Yes | 20/min |
| GET | `/api/memory/context` | Get memory context injection string | Yes | 30/min |
| POST | `/api/memory/extract` | Auto-extract memories from text | Yes | 5/min |
| GET | `/api/memory/recall` | Semantic memory recall (Mem0 + DB) | Yes | 30/min |
| POST | `/api/memory/sync-to-mem0` | Bulk-sync DB memories to Mem0 | Yes | 2/min |
| DELETE | `/api/memory/forget-all` | RGPD: forget all memories | Yes | 1/min |

---

## Social Publisher (`/api/social-publisher`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/social-publisher/accounts` | Connect social media account | Yes | 10/min |
| GET | `/api/social-publisher/accounts` | List connected accounts | Yes | 20/min |
| DELETE | `/api/social-publisher/accounts/{id}` | Disconnect account | Yes | 10/min |
| POST | `/api/social-publisher/posts` | Create post (draft/scheduled) | Yes | 10/min |
| GET | `/api/social-publisher/posts` | List posts (filterable by status) | Yes | 20/min |
| GET | `/api/social-publisher/posts/{id}` | Get post details | Yes | 20/min |
| POST | `/api/social-publisher/posts/{id}/publish` | Publish post immediately | Yes | 5/min |
| PUT | `/api/social-publisher/posts/{id}/schedule` | Schedule/reschedule post | Yes | 10/min |
| DELETE | `/api/social-publisher/posts/{id}` | Delete draft/failed post | Yes | 10/min |
| GET | `/api/social-publisher/posts/{id}/analytics` | Get post analytics | Yes | 20/min |
| POST | `/api/social-publisher/recycle` | Recycle Content Studio content | Yes | 5/min |
| GET | `/api/social-publisher/platforms` | List supported platforms | No | - |

---

## Integration Hub (`/api/integrations`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/integrations/providers` | List supported providers | No | - |
| POST | `/api/integrations/connectors` | Create connector (webhook/OAuth2/API key) | Yes | 10/min |
| GET | `/api/integrations/connectors` | List connectors | Yes | 20/min |
| GET | `/api/integrations/connectors/{id}` | Get connector | Yes | 30/min |
| DELETE | `/api/integrations/connectors/{id}` | Soft-delete connector | Yes | 10/min |
| POST | `/api/integrations/connectors/{id}/test` | Test connector connectivity | Yes | 5/min |
| POST | `/api/integrations/webhook/{connector_id}` | Receive webhook event (public) | No | - |
| GET | `/api/integrations/connectors/{id}/events` | List received events | Yes | 20/min |
| POST | `/api/integrations/triggers` | Create event trigger | Yes | 10/min |
| GET | `/api/integrations/triggers` | List triggers | Yes | 20/min |
| DELETE | `/api/integrations/triggers/{id}` | Delete trigger | Yes | 10/min |

---

## AI Chatbot Builder (`/api/chatbots`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/chatbots` | Create chatbot | Yes | 10/min |
| GET | `/api/chatbots` | List chatbots | Yes | 20/min |
| GET | `/api/chatbots/{id}` | Get chatbot details | Yes | 20/min |
| PUT | `/api/chatbots/{id}` | Update chatbot settings | Yes | 10/min |
| DELETE | `/api/chatbots/{id}` | Soft-delete chatbot | Yes | 10/min |
| POST | `/api/chatbots/{id}/publish` | Publish + generate embed token | Yes | 5/min |
| POST | `/api/chatbots/{id}/unpublish` | Unpublish + revoke embed token | Yes | 5/min |
| POST | `/api/chatbots/{id}/channels` | Add deployment channel | Yes | 10/min |
| DELETE | `/api/chatbots/{id}/channels/{type}` | Remove deployment channel | Yes | 10/min |
| GET | `/api/chatbots/{id}/analytics` | Chatbot analytics | Yes | 20/min |
| GET | `/api/chatbots/{id}/embed-code` | Get embed HTML/JS snippet | Yes | 20/min |
| POST | `/api/chatbots/widget/{token}/chat` | Public chat (embed widget) | No | 30/min |
| GET | `/api/chatbots/widget/{token}/history/{session}` | Public chat history | No | 20/min |
| GET | `/api/chatbots/widget/{token}/config` | Public widget config | No | 30/min |

---

## Marketplace (`/api/marketplace`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/marketplace/listings` | Browse listings (public) | No | 30/min |
| GET | `/api/marketplace/listings/{id}` | Get listing details (public) | No | 30/min |
| GET | `/api/marketplace/listings/{id}/reviews` | Get reviews (public) | No | 30/min |
| GET | `/api/marketplace/categories` | List categories (public) | No | 30/min |
| GET | `/api/marketplace/featured` | Featured listings (public) | No | 30/min |
| POST | `/api/marketplace/listings` | Create listing | Yes | 10/min |
| PUT | `/api/marketplace/listings/{id}` | Update listing (author) | Yes | 10/min |
| POST | `/api/marketplace/listings/{id}/publish` | Publish listing | Yes | 10/min |
| POST | `/api/marketplace/listings/{id}/unpublish` | Unpublish listing | Yes | 10/min |
| DELETE | `/api/marketplace/listings/{id}` | Soft-delete listing | Yes | 10/min |
| POST | `/api/marketplace/listings/{id}/install` | Install listing | Yes | 10/min |
| DELETE | `/api/marketplace/listings/{id}/install` | Uninstall listing | Yes | 10/min |
| POST | `/api/marketplace/listings/{id}/reviews` | Add review | Yes | 5/min |
| GET | `/api/marketplace/installed` | List installed items | Yes | 20/min |
| GET | `/api/marketplace/my-listings` | List own listings | Yes | 20/min |

---

## Presentation Gen (`/api/presentations`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/presentations` | Generate presentation from topic | Yes | 5/min |
| GET | `/api/presentations` | List presentations | Yes | 20/min |
| GET | `/api/presentations/templates` | List presentation templates | No | - |
| GET | `/api/presentations/{id}` | Get presentation with slides | Yes | 30/min |
| PUT | `/api/presentations/{id}/slides/{n}` | Update a slide | Yes | 15/min |
| POST | `/api/presentations/{id}/slides/{n}` | Insert slide after position | Yes | 10/min |
| DELETE | `/api/presentations/{id}/slides/{n}` | Remove slide | Yes | 10/min |
| POST | `/api/presentations/{id}/export` | Export (HTML, Markdown, PDF) | Yes | 5/min |
| POST | `/api/presentations/from-transcript` | Generate from transcription | Yes | 5/min |
| DELETE | `/api/presentations/{id}` | Delete presentation | Yes | 10/min |

---

## Code Sandbox (`/api/sandbox`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/sandbox/sandboxes` | Create sandbox | Yes | 10/min |
| GET | `/api/sandbox/sandboxes` | List sandboxes | Yes | 30/min |
| GET | `/api/sandbox/sandboxes/{id}` | Get sandbox with cells | Yes | 30/min |
| DELETE | `/api/sandbox/sandboxes/{id}` | Delete sandbox | Yes | 10/min |
| POST | `/api/sandbox/sandboxes/{id}/cells` | Add cell | Yes | 20/min |
| PUT | `/api/sandbox/sandboxes/{id}/cells/{cell}` | Update cell source | Yes | 30/min |
| DELETE | `/api/sandbox/sandboxes/{id}/cells/{cell}` | Remove cell | Yes | 20/min |
| POST | `/api/sandbox/sandboxes/{id}/cells/{cell}/execute` | Execute cell in sandbox | Yes | 10/min |
| POST | `/api/sandbox/generate` | Generate code from NL prompt | Yes | 5/min |
| POST | `/api/sandbox/explain` | Explain code with AI | Yes | 10/min |
| POST | `/api/sandbox/debug` | Debug code with AI | Yes | 5/min |

---

## AI Forms (`/api/forms`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/api/forms` | Create form | Yes | 10/min |
| GET | `/api/forms` | List forms | Yes | 20/min |
| GET | `/api/forms/{id}` | Get form details | Yes | 20/min |
| PUT | `/api/forms/{id}` | Update form | Yes | 10/min |
| DELETE | `/api/forms/{id}` | Soft-delete form | Yes | 10/min |
| POST | `/api/forms/{id}/publish` | Publish + generate share token | Yes | 5/min |
| POST | `/api/forms/{id}/close` | Close to new responses | Yes | 5/min |
| GET | `/api/forms/{id}/responses` | List responses | Yes | 20/min |
| GET | `/api/forms/{id}/responses/{rid}` | Get single response | Yes | 20/min |
| GET | `/api/forms/{id}/analytics` | AI analysis of responses | Yes | 10/min |
| POST | `/api/forms/{id}/responses/{rid}/score` | AI scoring of response | Yes | 10/min |
| POST | `/api/forms/generate` | Generate form from NL prompt | Yes | 5/min |
| GET | `/api/forms/public/{token}` | Get published form (public) | No | 30/min |
| POST | `/api/forms/public/{token}/submit` | Submit response (public) | No | 20/min |

---

## Public API v1 (`/v1`)

| Method | Path | Description | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| POST | `/v1/transcribe` | Submit transcription job | API Key | 10/min |
| POST | `/v1/process` | Process text with AI | API Key | 10/min |
| GET | `/v1/jobs/{job_id}` | Get job status | API Key | 30/min |

---

## Summary

| Category | Endpoints |
|----------|-----------|
| Root & Health | 7 |
| Authentication | 6 |
| AI Assistant | 6 |
| Transcription | 18 |
| Conversation | 5 |
| Knowledge Base | 9 |
| Compare | 3 |
| Pipelines | 8 |
| Agents | 5 |
| Sentiment | 2 |
| Web Crawler | 3 |
| Workspaces | 13 |
| Billing | 5 |
| API Keys | 3 |
| Cost Tracker | 3 |
| Content Studio | 9 |
| AI Workflows | 11 |
| Multi-Agent Crew | 9 |
| Voice Clone | 8 |
| Realtime AI | 7 |
| Security Guardian | 7 |
| Image Gen | 9 |
| Data Analyst | 8 |
| Video Gen | 9 |
| Fine-Tuning | 13 |
| AI Monitoring | 8 |
| Unified Search | 5 |
| AI Memory | 8 |
| Social Publisher | 12 |
| Integration Hub | 11 |
| AI Chatbot Builder | 14 |
| Marketplace | 15 |
| Presentation Gen | 10 |
| Code Sandbox | 11 |
| AI Forms | 14 |
| Public API v1 | 3 |
| **Total** | **~270** |
