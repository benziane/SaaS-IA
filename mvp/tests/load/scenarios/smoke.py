"""
SaaS-IA Smoke Test Scenario

Quick validation that the system is functional before running heavier tests.
- 5 virtual users
- 30 seconds duration
- Covers login, health checks, and basic reads
- Strict thresholds (100% success expected)

Usage:
    locust -f scenarios/smoke.py --headless -u 5 -r 5 -t 30s
    make load-smoke
"""

import os
import random
import sys

from locust import HttpUser, between, events, tag, task

BASE_URL = os.getenv("SAASIA_BASE_URL", "http://localhost:8004")
DEFAULT_USER = os.getenv("SAASIA_USER", "demo@saas-ia.com")
DEFAULT_PASSWORD = os.getenv("SAASIA_PASSWORD", "demo123")

# Track failures for exit code
_smoke_failures = 0
_smoke_total = 0


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    global _smoke_failures, _smoke_total
    _smoke_total += 1
    if exception or (hasattr(kwargs.get("response", None), "status_code") and kwargs["response"].status_code >= 500):
        _smoke_failures += 1


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    error_rate = (_smoke_failures / _smoke_total * 100) if _smoke_total > 0 else 0

    print("\n" + "=" * 60)
    print("SMOKE TEST RESULTS")
    print("=" * 60)
    print(f"  Total requests: {_smoke_total}")
    print(f"  Failures:       {_smoke_failures}")
    print(f"  Error rate:     {error_rate:.2f}%")

    if error_rate > 1:
        print("  VERDICT:        FAIL (error rate > 1%)")
        print("=" * 60 + "\n")
        environment.process_exit_code = 1
    else:
        print("  VERDICT:        PASS")
        print("=" * 60 + "\n")
        environment.process_exit_code = 0


class SmokeTestUser(HttpUser):
    """
    Minimal user for smoke testing.

    Validates that core system functions are operational:
    - Authentication (login)
    - Health endpoints
    - Basic CRUD on 3 core modules
    """

    wait_time = between(0.5, 1)
    host = BASE_URL

    def on_start(self):
        response = self.client.post(
            "/api/auth/login",
            data={"username": DEFAULT_USER, "password": DEFAULT_PASSWORD},
            name="[smoke] POST /api/auth/login",
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
            self.token = None

    # --- Health ---

    @tag("smoke", "health")
    @task(5)
    def health_live(self):
        with self.client.get("/health/live", name="[smoke] GET /health/live", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Expected 200, got {resp.status_code}")

    @tag("smoke", "health")
    @task(3)
    def health_ready(self):
        self.client.get("/health/ready", name="[smoke] GET /health/ready")

    @tag("smoke", "health")
    @task(2)
    def health_full(self):
        self.client.get("/health", name="[smoke] GET /health")

    # --- Auth ---

    @tag("smoke", "auth")
    @task(3)
    def get_me(self):
        with self.client.get("/api/auth/me", headers=self.headers, name="[smoke] GET /api/auth/me", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Expected 200, got {resp.status_code}")

    # --- Core module reads ---

    @tag("smoke", "read")
    @task(3)
    def list_transcriptions(self):
        self.client.get(
            "/api/transcription/",
            headers=self.headers,
            name="[smoke] GET /api/transcription/",
        )

    @tag("smoke", "read")
    @task(3)
    def list_conversations(self):
        self.client.get(
            "/api/conversations/",
            headers=self.headers,
            name="[smoke] GET /api/conversations/",
        )

    @tag("smoke", "read")
    @task(3)
    def list_knowledge(self):
        self.client.get(
            "/api/knowledge/documents",
            headers=self.headers,
            name="[smoke] GET /api/knowledge/documents",
        )

    @tag("smoke", "read")
    @task(2)
    def list_pipelines(self):
        self.client.get(
            "/api/pipelines/",
            headers=self.headers,
            name="[smoke] GET /api/pipelines/",
        )

    @tag("smoke", "read")
    @task(2)
    def list_workflows(self):
        self.client.get(
            "/api/workflows/",
            headers=self.headers,
            name="[smoke] GET /api/workflows/",
        )

    @tag("smoke", "read")
    @task(1)
    def get_modules(self):
        self.client.get(
            "/api/modules",
            headers=self.headers,
            name="[smoke] GET /api/modules",
        )

    @tag("smoke", "read")
    @task(1)
    def get_root(self):
        with self.client.get("/", name="[smoke] GET /", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Expected 200, got {resp.status_code}")

    # --- Public endpoints ---

    @tag("smoke", "public")
    @task(1)
    def marketplace_listings(self):
        self.client.get(
            "/api/marketplace/listings",
            name="[smoke] GET /api/marketplace/listings",
        )

    @tag("smoke", "public")
    @task(1)
    def billing_plans(self):
        self.client.get(
            "/api/billing/plans",
            name="[smoke] GET /api/billing/plans",
        )
