"""
SaaS-IA Load Tests -- Locust

Comprehensive load testing for the SaaS-IA platform (~280 endpoints).
Three user classes simulate realistic traffic patterns:

- SaaSIAUser:  typical authenticated user (reads >> writes)
- APIKeyUser:  external API consumer using API key auth
- HeavyUser:   power user performing AI-intensive operations

Usage:
    locust -f locustfile.py                    # web UI at http://localhost:8089
    locust -f locustfile.py --headless -u 50   # headless, 50 users

Environment variables:
    SAASIA_BASE_URL   (default: http://localhost:8004)
    SAASIA_USER       (default: demo@saas-ia.com)
    SAASIA_PASSWORD   (default: demo123)
    SAASIA_API_KEY    (default: test_api_key_placeholder)
"""

import json
import logging
import os
import random
import time
from typing import Optional

from locust import HttpUser, between, events, tag, task
from locust.runners import MasterRunner, WorkerRunner

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("SAASIA_BASE_URL", "http://localhost:8004")
DEFAULT_USER = os.getenv("SAASIA_USER", "demo@saas-ia.com")
DEFAULT_PASSWORD = os.getenv("SAASIA_PASSWORD", "demo123")
API_KEY = os.getenv("SAASIA_API_KEY", "test_api_key_placeholder")

# Sample texts for write operations
SAMPLE_TEXTS = [
    "This is a great product! I love using it every day.",
    "The customer service was terrible. I waited two hours for a response.",
    "Artificial intelligence is transforming how businesses operate globally.",
    "Our quarterly revenue exceeded expectations by 15% year over year.",
    "The new feature rollout has been smooth with positive user feedback.",
    "Cloud-native architectures enable rapid scaling and deployment.",
    "Natural language processing continues to advance at an impressive pace.",
    "Data-driven decision making is essential for modern enterprises.",
]

SAMPLE_PROMPTS = [
    "Explain quantum computing in simple terms",
    "What are the benefits of microservices architecture?",
    "Summarize the key trends in AI for 2025",
    "How does transfer learning work in deep learning?",
    "What is retrieval-augmented generation (RAG)?",
]

logger = logging.getLogger("saasia-load")


# ---------------------------------------------------------------------------
# Custom metrics & event hooks
# ---------------------------------------------------------------------------

_request_stats: dict = {
    "total": 0,
    "failures": 0,
    "by_endpoint": {},
}


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track per-endpoint statistics for custom reporting."""
    _request_stats["total"] += 1
    if exception:
        _request_stats["failures"] += 1

    key = f"{request_type} {name}"
    if key not in _request_stats["by_endpoint"]:
        _request_stats["by_endpoint"][key] = {
            "count": 0,
            "failures": 0,
            "total_time": 0,
            "min_time": float("inf"),
            "max_time": 0,
            "times": [],
        }

    stats = _request_stats["by_endpoint"][key]
    stats["count"] += 1
    stats["total_time"] += response_time
    stats["min_time"] = min(stats["min_time"], response_time)
    stats["max_time"] = max(stats["max_time"], response_time)

    # Keep last 1000 response times for percentile calculation
    if len(stats["times"]) < 1000:
        stats["times"].append(response_time)
    else:
        stats["times"][random.randint(0, 999)] = response_time

    if exception:
        stats["failures"] += 1


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Print custom summary report on exit."""
    if isinstance(environment.runner, WorkerRunner):
        return  # Only print on master/standalone

    print("\n" + "=" * 80)
    print("SaaS-IA LOAD TEST -- CUSTOM SUMMARY")
    print("=" * 80)

    total = _request_stats["total"]
    failures = _request_stats["failures"]
    error_rate = (failures / total * 100) if total > 0 else 0

    print(f"\nTotal requests:   {total}")
    print(f"Total failures:   {failures}")
    print(f"Error rate:       {error_rate:.2f}%")

    if _request_stats["by_endpoint"]:
        print(f"\n{'Endpoint':<55} {'Count':>7} {'Avg(ms)':>9} {'P95(ms)':>9} {'P99(ms)':>9} {'Err%':>7}")
        print("-" * 100)

        for endpoint, stats in sorted(
            _request_stats["by_endpoint"].items(),
            key=lambda x: x[1]["count"],
            reverse=True,
        ):
            count = stats["count"]
            avg = stats["total_time"] / count if count else 0
            err_pct = (stats["failures"] / count * 100) if count else 0

            times = sorted(stats["times"])
            p95 = times[int(len(times) * 0.95)] if times else 0
            p99 = times[int(len(times) * 0.99)] if times else 0

            name = endpoint[:54]
            print(f"{name:<55} {count:>7} {avg:>9.1f} {p95:>9.1f} {p99:>9.1f} {err_pct:>6.1f}%")

    print("\n" + "=" * 80)

    # Performance gate check
    if error_rate > 5:
        print("FAIL: Error rate exceeds 5% threshold")
    else:
        print("PASS: Error rate within 5% threshold")
    print("=" * 80 + "\n")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test configuration at start."""
    if isinstance(environment.runner, WorkerRunner):
        return
    print("\n" + "=" * 80)
    print("SaaS-IA LOAD TEST STARTING")
    print(f"  Target: {BASE_URL}")
    print(f"  User:   {DEFAULT_USER}")
    print("=" * 80 + "\n")


# ---------------------------------------------------------------------------
# Helper mixin
# ---------------------------------------------------------------------------

class AuthMixin:
    """Shared authentication logic for user classes."""

    token: Optional[str] = None
    headers: dict = {}

    def _login(self):
        """Authenticate via OAuth2 form and store JWT token."""
        response = self.client.post(
            "/api/auth/login",
            data={"username": DEFAULT_USER, "password": DEFAULT_PASSWORD},
            name="/api/auth/login",
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
            logger.debug("Login successful for %s", DEFAULT_USER)
        else:
            logger.warning(
                "Login failed (status=%d): %s",
                response.status_code,
                response.text[:200],
            )
            self.token = None
            self.headers = {}


# ---------------------------------------------------------------------------
# User class 1: Typical SaaS-IA User (weight=5)
# ---------------------------------------------------------------------------

class SaaSIAUser(AuthMixin, HttpUser):
    """
    Simulates a typical SaaS-IA user session.

    Traffic distribution mirrors real usage:
    - 60% health checks & read operations
    - 30% listing/browsing operations
    - 10% write operations
    """

    wait_time = between(1, 3)
    host = BASE_URL
    weight = 5

    def on_start(self):
        self._login()

    # --- Health checks (lightweight, high frequency) ---

    @tag("health")
    @task(10)
    def health_live(self):
        self.client.get("/health/live", name="/health/live")

    @tag("health")
    @task(5)
    def health_ready(self):
        self.client.get("/health/ready", name="/health/ready")

    @tag("health")
    @task(3)
    def health_check(self):
        self.client.get("/health", name="/health")

    @tag("health")
    @task(1)
    def health_startup(self):
        self.client.get("/health/startup", name="/health/startup")

    # --- Auth operations ---

    @tag("auth")
    @task(3)
    def get_me(self):
        self.client.get("/api/auth/me", headers=self.headers, name="/api/auth/me")

    # --- Core module reads (most common) ---

    @tag("read", "transcription")
    @task(8)
    def list_transcriptions(self):
        self.client.get(
            "/api/transcription/",
            headers=self.headers,
            name="/api/transcription/ [list]",
        )

    @tag("read", "transcription")
    @task(3)
    def transcription_stats(self):
        self.client.get(
            "/api/transcription/stats",
            headers=self.headers,
            name="/api/transcription/stats",
        )

    @tag("read", "conversation")
    @task(6)
    def list_conversations(self):
        self.client.get(
            "/api/conversations/",
            headers=self.headers,
            name="/api/conversations/ [list]",
        )

    @tag("read", "knowledge")
    @task(5)
    def list_knowledge(self):
        self.client.get(
            "/api/knowledge/documents",
            headers=self.headers,
            name="/api/knowledge/documents",
        )

    @tag("read", "knowledge")
    @task(4)
    def search_knowledge(self):
        query = random.choice(["test", "AI", "data", "analysis", "report"])
        self.client.post(
            "/api/knowledge/search",
            headers=self.headers,
            json={"query": query, "limit": 5},
            name="/api/knowledge/search",
        )

    @tag("read", "knowledge")
    @task(1)
    def knowledge_search_status(self):
        self.client.get(
            "/api/knowledge/search/status",
            name="/api/knowledge/search/status",
        )

    @tag("read", "pipelines")
    @task(3)
    def list_pipelines(self):
        self.client.get(
            "/api/pipelines/",
            headers=self.headers,
            name="/api/pipelines/ [list]",
        )

    @tag("read", "content")
    @task(3)
    def list_content_projects(self):
        self.client.get(
            "/api/content-studio/projects",
            headers=self.headers,
            name="/api/content-studio/projects [list]",
        )

    @tag("read", "content")
    @task(1)
    def list_content_formats(self):
        self.client.get(
            "/api/content-studio/formats",
            name="/api/content-studio/formats",
        )

    @tag("read", "agents")
    @task(2)
    def list_agent_runs(self):
        self.client.get(
            "/api/agents/runs",
            headers=self.headers,
            name="/api/agents/runs",
        )

    @tag("read", "workflows")
    @task(2)
    def list_workflows(self):
        self.client.get(
            "/api/workflows/",
            headers=self.headers,
            name="/api/workflows/ [list]",
        )

    @tag("read", "workflows")
    @task(1)
    def list_workflow_templates(self):
        self.client.get(
            "/api/workflows/templates",
            name="/api/workflows/templates",
        )

    @tag("read", "marketplace")
    @task(2)
    def browse_marketplace(self):
        self.client.get(
            "/api/marketplace/listings",
            name="/api/marketplace/listings",
        )

    @tag("read", "marketplace")
    @task(1)
    def marketplace_categories(self):
        self.client.get(
            "/api/marketplace/categories",
            name="/api/marketplace/categories",
        )

    @tag("read", "marketplace")
    @task(1)
    def marketplace_featured(self):
        self.client.get(
            "/api/marketplace/featured",
            name="/api/marketplace/featured",
        )

    @tag("read", "chatbots")
    @task(2)
    def list_chatbots(self):
        self.client.get(
            "/api/chatbots",
            headers=self.headers,
            name="/api/chatbots [list]",
        )

    @tag("read", "search")
    @task(2)
    def unified_search(self):
        query = random.choice(["test", "AI", "machine learning", "data"])
        self.client.get(
            f"/api/search/?q={query}&limit=5",
            headers=self.headers,
            name="/api/search/ [query]",
        )

    @tag("read", "search")
    @task(1)
    def search_status(self):
        self.client.get(
            "/api/search/status",
            headers=self.headers,
            name="/api/search/status",
        )

    @tag("read", "notifications")
    @task(2)
    def get_notifications(self):
        self.client.get(
            "/api/notifications?limit=10",
            headers=self.headers,
            name="/api/notifications",
        )

    @tag("read", "notifications")
    @task(1)
    def unread_count(self):
        self.client.get(
            "/api/notifications/unread-count",
            headers=self.headers,
            name="/api/notifications/unread-count",
        )

    @tag("read", "costs")
    @task(1)
    def get_cost_dashboard(self):
        self.client.get(
            "/api/costs/dashboard",
            headers=self.headers,
            name="/api/costs/dashboard",
        )

    @tag("read", "costs")
    @task(1)
    def get_cost_alerts(self):
        self.client.get(
            "/api/costs/alerts",
            headers=self.headers,
            name="/api/costs/alerts",
        )

    @tag("read", "billing")
    @task(1)
    def list_billing_plans(self):
        self.client.get(
            "/api/billing/plans",
            name="/api/billing/plans",
        )

    @tag("read", "billing")
    @task(1)
    def get_billing_quota(self):
        self.client.get(
            "/api/billing/quota",
            headers=self.headers,
            name="/api/billing/quota",
        )

    @tag("read", "monitoring")
    @task(1)
    def monitoring_dashboard(self):
        self.client.get(
            "/api/monitoring/dashboard",
            headers=self.headers,
            name="/api/monitoring/dashboard",
        )

    @tag("read", "monitoring")
    @task(1)
    def monitoring_providers(self):
        self.client.get(
            "/api/monitoring/providers",
            headers=self.headers,
            name="/api/monitoring/providers",
        )

    @tag("read", "security")
    @task(1)
    def security_dashboard(self):
        self.client.get(
            "/api/security/dashboard",
            headers=self.headers,
            name="/api/security/dashboard",
        )

    @tag("read", "memory")
    @task(1)
    def list_memories(self):
        self.client.get(
            "/api/memory/",
            headers=self.headers,
            name="/api/memory/ [list]",
        )

    @tag("read", "presentations")
    @task(1)
    def list_presentations(self):
        self.client.get(
            "/api/presentations",
            headers=self.headers,
            name="/api/presentations [list]",
        )

    @tag("read", "images")
    @task(1)
    def list_images(self):
        self.client.get(
            "/api/images/",
            headers=self.headers,
            name="/api/images/ [list]",
        )

    @tag("read", "videos")
    @task(1)
    def list_videos(self):
        self.client.get(
            "/api/videos/",
            headers=self.headers,
            name="/api/videos/ [list]",
        )

    @tag("read", "forms")
    @task(1)
    def list_forms(self):
        self.client.get(
            "/api/forms",
            headers=self.headers,
            name="/api/forms [list]",
        )

    @tag("read", "voice")
    @task(1)
    def list_voice_profiles(self):
        self.client.get(
            "/api/voice/profiles",
            headers=self.headers,
            name="/api/voice/profiles",
        )

    @tag("read", "social")
    @task(1)
    def list_social_accounts(self):
        self.client.get(
            "/api/social-publisher/accounts",
            headers=self.headers,
            name="/api/social-publisher/accounts",
        )

    @tag("read", "integrations")
    @task(1)
    def list_integration_providers(self):
        self.client.get(
            "/api/integrations/providers",
            name="/api/integrations/providers",
        )

    @tag("read", "crews")
    @task(1)
    def list_crews(self):
        self.client.get(
            "/api/crews/",
            headers=self.headers,
            name="/api/crews/ [list]",
        )

    @tag("read", "sandbox")
    @task(1)
    def list_sandboxes(self):
        self.client.get(
            "/api/sandbox/sandboxes",
            headers=self.headers,
            name="/api/sandbox/sandboxes [list]",
        )

    @tag("read", "data")
    @task(1)
    def list_datasets(self):
        self.client.get(
            "/api/data/datasets",
            headers=self.headers,
            name="/api/data/datasets [list]",
        )

    @tag("read", "realtime")
    @task(1)
    def list_realtime_sessions(self):
        self.client.get(
            "/api/realtime/sessions",
            headers=self.headers,
            name="/api/realtime/sessions [list]",
        )

    @tag("read", "keys")
    @task(1)
    def list_api_keys(self):
        self.client.get(
            "/api/keys/",
            headers=self.headers,
            name="/api/keys/ [list]",
        )

    # --- Admin / system reads ---

    @tag("admin")
    @task(1)
    def get_modules(self):
        self.client.get(
            "/api/modules",
            headers=self.headers,
            name="/api/modules",
        )

    @tag("admin")
    @task(1)
    def get_feature_flags(self):
        self.client.get(
            "/api/feature-flags/",
            headers=self.headers,
            name="/api/feature-flags/",
        )

    @tag("admin")
    @task(1)
    def get_root(self):
        self.client.get("/", name="/ [root]")

    # --- Write operations (lower frequency) ---

    @tag("write", "conversation")
    @task(2)
    def create_conversation(self):
        self.client.post(
            "/api/conversations/",
            headers=self.headers,
            json={"title": f"Load test conversation {random.randint(1, 100000)}"},
            name="/api/conversations/ [create]",
        )

    @tag("write", "sentiment")
    @task(1)
    def analyze_sentiment(self):
        self.client.post(
            "/api/sentiment/analyze",
            headers=self.headers,
            json={"text": random.choice(SAMPLE_TEXTS)},
            name="/api/sentiment/analyze",
        )

    @tag("write", "security")
    @task(1)
    def security_scan(self):
        self.client.post(
            "/api/security/scan",
            headers=self.headers,
            json={"text": random.choice(SAMPLE_TEXTS)},
            name="/api/security/scan",
        )

    @tag("write", "memory")
    @task(1)
    def add_memory(self):
        self.client.post(
            "/api/memory/",
            headers=self.headers,
            json={
                "content": f"Load test memory entry {random.randint(1, 100000)}",
                "memory_type": "fact",
            },
            name="/api/memory/ [create]",
        )


# ---------------------------------------------------------------------------
# User class 2: API Key User (weight=2)
# ---------------------------------------------------------------------------

class APIKeyUser(HttpUser):
    """
    Simulates external API access via API key.

    Covers /v1/* public API endpoints and health checks.
    Lower weight -- represents automated integrations.
    """

    wait_time = between(0.5, 2)
    host = BASE_URL
    weight = 2

    def on_start(self):
        self.headers = {"X-API-Key": API_KEY}

    @tag("api", "health")
    @task(5)
    def api_health(self):
        self.client.get("/health/live", name="/health/live [api-key]")

    @tag("api")
    @task(3)
    def api_process_text(self):
        self.client.post(
            "/v1/process",
            headers=self.headers,
            json={
                "text": random.choice(SAMPLE_TEXTS),
                "operation": "summarize",
            },
            name="/v1/process",
        )

    @tag("api")
    @task(2)
    def api_transcribe(self):
        self.client.post(
            "/v1/transcribe",
            headers=self.headers,
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            name="/v1/transcribe",
        )

    @tag("api", "marketplace")
    @task(2)
    def api_browse_marketplace(self):
        self.client.get(
            "/api/marketplace/listings",
            name="/api/marketplace/listings [api-key]",
        )


# ---------------------------------------------------------------------------
# User class 3: Heavy / Power User (weight=1)
# ---------------------------------------------------------------------------

class HeavyUser(AuthMixin, HttpUser):
    """
    Simulates power users performing AI-intensive operations.

    These requests are slower and more resource-intensive.
    Lowest weight -- represents a small fraction of total traffic.
    """

    wait_time = between(2, 5)
    host = BASE_URL
    weight = 1

    def on_start(self):
        self._login()

    @tag("heavy", "compare")
    @task(3)
    def compare_models(self):
        self.client.post(
            "/api/compare/run",
            headers=self.headers,
            json={
                "prompt": random.choice(SAMPLE_PROMPTS),
                "providers": ["gemini"],
            },
            name="/api/compare/run",
        )

    @tag("heavy", "pipelines")
    @task(2)
    def create_pipeline(self):
        self.client.post(
            "/api/pipelines/",
            headers=self.headers,
            json={
                "name": f"Load test pipeline {random.randint(1, 100000)}",
                "steps": [
                    {"type": "summarize", "config": {"max_length": 100}},
                ],
            },
            name="/api/pipelines/ [create]",
        )

    @tag("heavy", "content")
    @task(2)
    def create_content_project(self):
        self.client.post(
            "/api/content-studio/projects",
            headers=self.headers,
            json={
                "title": f"Load test project {random.randint(1, 100000)}",
                "source_text": random.choice(SAMPLE_TEXTS),
            },
            name="/api/content-studio/projects [create]",
        )

    @tag("heavy", "knowledge")
    @task(2)
    def knowledge_ask(self):
        self.client.post(
            "/api/knowledge/ask",
            headers=self.headers,
            json={
                "question": random.choice(SAMPLE_PROMPTS),
                "limit": 3,
            },
            name="/api/knowledge/ask [RAG]",
        )

    @tag("heavy", "ai-assistant")
    @task(2)
    def process_text_ai(self):
        self.client.post(
            "/api/ai-assistant/process-text",
            headers=self.headers,
            json={
                "text": random.choice(SAMPLE_TEXTS),
                "instruction": "Summarize this text",
            },
            name="/api/ai-assistant/process-text",
        )

    @tag("heavy", "agents")
    @task(1)
    def run_agent(self):
        self.client.post(
            "/api/agents/run",
            headers=self.headers,
            json={
                "instruction": random.choice(SAMPLE_PROMPTS),
                "max_steps": 3,
            },
            name="/api/agents/run",
        )

    @tag("heavy", "workflows")
    @task(1)
    def create_workflow(self):
        self.client.post(
            "/api/workflows/",
            headers=self.headers,
            json={
                "name": f"Load test workflow {random.randint(1, 100000)}",
                "nodes": [
                    {
                        "id": "start",
                        "type": "summarize",
                        "config": {"max_length": 200},
                    },
                ],
                "edges": [],
            },
            name="/api/workflows/ [create]",
        )

    @tag("heavy", "crawler")
    @task(1)
    def scrape_url(self):
        self.client.post(
            "/api/crawler/scrape",
            headers=self.headers,
            json={"url": "https://httpbin.org/html"},
            name="/api/crawler/scrape",
        )

    @tag("heavy", "sandbox")
    @task(1)
    def generate_code(self):
        self.client.post(
            "/api/sandbox/generate",
            headers=self.headers,
            json={
                "prompt": "Write a Python function to calculate fibonacci numbers",
                "language": "python",
            },
            name="/api/sandbox/generate",
        )

    @tag("heavy", "forms")
    @task(1)
    def generate_form(self):
        self.client.post(
            "/api/forms/generate",
            headers=self.headers,
            json={
                "prompt": "Create a customer satisfaction survey with 5 questions",
            },
            name="/api/forms/generate",
        )
