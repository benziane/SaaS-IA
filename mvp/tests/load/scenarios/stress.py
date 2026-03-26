"""
SaaS-IA Stress Test Scenario

Ramp to 500 concurrent users to find the breaking point.
Identifies the maximum throughput and the load at which error rates
begin to exceed acceptable thresholds.

Stages:
  0:00 - 1:00   ramp to 50 users     (warm-up)
  1:00 - 2:00   ramp to 100 users    (baseline)
  2:00 - 3:00   ramp to 200 users    (moderate load)
  3:00 - 4:00   ramp to 300 users    (high load)
  4:00 - 5:00   ramp to 500 users    (stress)
  5:00 - 6:00   sustain 500 users    (breaking point)
  6:00 - 7:00   ramp down to 0       (recovery)

Usage:
    locust -f scenarios/stress.py --headless -t 7m
    make load-stress
"""

import os
import random
import time
from collections import defaultdict

from locust import HttpUser, between, events, tag, task
from locust.runners import WorkerRunner

BASE_URL = os.getenv("SAASIA_BASE_URL", "http://localhost:8004")
DEFAULT_USER = os.getenv("SAASIA_USER", "demo@saas-ia.com")
DEFAULT_PASSWORD = os.getenv("SAASIA_PASSWORD", "demo123")

SAMPLE_TEXTS = [
    "This is a great product! I love using it every day.",
    "The customer service was terrible. I waited two hours.",
    "AI is transforming how businesses operate globally.",
    "Our quarterly revenue exceeded expectations by 15%.",
    "The new feature rollout has been smooth with positive feedback.",
]

# ---------------------------------------------------------------------------
# Stress-specific metrics tracking
# ---------------------------------------------------------------------------

_stress_metrics = {
    "intervals": [],  # Per-10s interval stats
    "current_interval": {
        "start": time.time(),
        "requests": 0,
        "failures": 0,
        "total_time": 0,
        "status_codes": defaultdict(int),
    },
}

INTERVAL_SECONDS = 10


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    interval = _stress_metrics["current_interval"]
    now = time.time()

    # Rotate interval every INTERVAL_SECONDS
    if now - interval["start"] >= INTERVAL_SECONDS:
        if interval["requests"] > 0:
            _stress_metrics["intervals"].append({
                "timestamp": interval["start"],
                "requests": interval["requests"],
                "failures": interval["failures"],
                "avg_ms": interval["total_time"] / interval["requests"],
                "rps": interval["requests"] / INTERVAL_SECONDS,
                "error_rate": interval["failures"] / interval["requests"] * 100,
                "status_codes": dict(interval["status_codes"]),
            })
        _stress_metrics["current_interval"] = {
            "start": now,
            "requests": 0,
            "failures": 0,
            "total_time": 0,
            "status_codes": defaultdict(int),
        }
        interval = _stress_metrics["current_interval"]

    interval["requests"] += 1
    interval["total_time"] += response_time

    response = kwargs.get("response", None)
    if response is not None:
        interval["status_codes"][response.status_code] += 1

    if exception:
        interval["failures"] += 1


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    if isinstance(environment.runner, WorkerRunner):
        return

    intervals = _stress_metrics["intervals"]
    if not intervals:
        print("\nNo stress test data collected.")
        return

    print("\n" + "=" * 80)
    print("STRESS TEST RESULTS")
    print("=" * 80)

    print(f"\n{'Time(s)':<10} {'Requests':>10} {'RPS':>8} {'Avg(ms)':>10} {'Err%':>8} {'5xx':>6} {'429':>6}")
    print("-" * 70)

    start = intervals[0]["timestamp"]
    peak_rps = 0
    breaking_point = None

    for iv in intervals:
        elapsed = int(iv["timestamp"] - start)
        rps = iv["rps"]
        err_rate = iv["error_rate"]
        count_5xx = sum(v for k, v in iv["status_codes"].items() if 500 <= k < 600)
        count_429 = iv["status_codes"].get(429, 0)

        peak_rps = max(peak_rps, rps)

        # Detect breaking point: first interval with > 10% error rate
        if err_rate > 10 and breaking_point is None:
            breaking_point = elapsed

        print(
            f"{elapsed:<10} {iv['requests']:>10} {rps:>8.1f} "
            f"{iv['avg_ms']:>10.1f} {err_rate:>7.1f}% {count_5xx:>6} {count_429:>6}"
        )

    total_requests = sum(iv["requests"] for iv in intervals)
    total_failures = sum(iv["failures"] for iv in intervals)
    overall_error = (total_failures / total_requests * 100) if total_requests else 0

    print("\n" + "-" * 70)
    print(f"  Total requests:   {total_requests}")
    print(f"  Total failures:   {total_failures}")
    print(f"  Overall error:    {overall_error:.2f}%")
    print(f"  Peak RPS:         {peak_rps:.1f}")

    if breaking_point is not None:
        print(f"  Breaking point:   ~{breaking_point}s (error rate exceeded 10%)")
    else:
        print("  Breaking point:   NOT REACHED (system held under load)")

    print("=" * 80 + "\n")


# ---------------------------------------------------------------------------
# Stress Test User
# ---------------------------------------------------------------------------

class StressTestUser(HttpUser):
    """
    High-throughput user for stress testing.

    Shorter wait times and heavier task distribution compared to
    the standard SaaSIAUser. Exercises the most performance-critical
    endpoints to identify bottlenecks.
    """

    wait_time = between(0.2, 1)
    host = BASE_URL

    def on_start(self):
        response = self.client.post(
            "/api/auth/login",
            data={"username": DEFAULT_USER, "password": DEFAULT_PASSWORD},
            name="[stress] POST /api/auth/login",
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
            self.token = None

    # --- Health (lightweight baseline) ---

    @tag("stress", "health")
    @task(8)
    def health_live(self):
        self.client.get("/health/live", name="[stress] GET /health/live")

    @tag("stress", "health")
    @task(3)
    def health_ready(self):
        self.client.get("/health/ready", name="[stress] GET /health/ready")

    # --- Auth pressure ---

    @tag("stress", "auth")
    @task(5)
    def get_me(self):
        self.client.get("/api/auth/me", headers=self.headers, name="[stress] GET /api/auth/me")

    # --- High-frequency reads ---

    @tag("stress", "read")
    @task(10)
    def list_transcriptions(self):
        self.client.get(
            "/api/transcription/",
            headers=self.headers,
            name="[stress] GET /api/transcription/",
        )

    @tag("stress", "read")
    @task(8)
    def list_conversations(self):
        self.client.get(
            "/api/conversations/",
            headers=self.headers,
            name="[stress] GET /api/conversations/",
        )

    @tag("stress", "read")
    @task(7)
    def list_knowledge(self):
        self.client.get(
            "/api/knowledge/documents",
            headers=self.headers,
            name="[stress] GET /api/knowledge/documents",
        )

    @tag("stress", "read")
    @task(5)
    def search_knowledge(self):
        self.client.post(
            "/api/knowledge/search",
            headers=self.headers,
            json={"query": random.choice(["test", "AI", "data"]), "limit": 5},
            name="[stress] POST /api/knowledge/search",
        )

    @tag("stress", "read")
    @task(5)
    def list_pipelines(self):
        self.client.get(
            "/api/pipelines/",
            headers=self.headers,
            name="[stress] GET /api/pipelines/",
        )

    @tag("stress", "read")
    @task(4)
    def list_content(self):
        self.client.get(
            "/api/content-studio/projects",
            headers=self.headers,
            name="[stress] GET /api/content-studio/projects",
        )

    @tag("stress", "read")
    @task(4)
    def list_workflows(self):
        self.client.get(
            "/api/workflows/",
            headers=self.headers,
            name="[stress] GET /api/workflows/",
        )

    @tag("stress", "read")
    @task(3)
    def unified_search(self):
        self.client.get(
            "/api/search/?q=test&limit=5",
            headers=self.headers,
            name="[stress] GET /api/search/",
        )

    @tag("stress", "read")
    @task(3)
    def list_agents(self):
        self.client.get(
            "/api/agents/runs",
            headers=self.headers,
            name="[stress] GET /api/agents/runs",
        )

    @tag("stress", "read")
    @task(3)
    def marketplace_listings(self):
        self.client.get(
            "/api/marketplace/listings",
            name="[stress] GET /api/marketplace/listings",
        )

    @tag("stress", "read")
    @task(2)
    def notifications(self):
        self.client.get(
            "/api/notifications?limit=10",
            headers=self.headers,
            name="[stress] GET /api/notifications",
        )

    @tag("stress", "read")
    @task(2)
    def cost_dashboard(self):
        self.client.get(
            "/api/costs/dashboard",
            headers=self.headers,
            name="[stress] GET /api/costs/dashboard",
        )

    @tag("stress", "read")
    @task(2)
    def monitoring_dashboard(self):
        self.client.get(
            "/api/monitoring/dashboard",
            headers=self.headers,
            name="[stress] GET /api/monitoring/dashboard",
        )

    @tag("stress", "read")
    @task(1)
    def list_chatbots(self):
        self.client.get(
            "/api/chatbots",
            headers=self.headers,
            name="[stress] GET /api/chatbots",
        )

    @tag("stress", "read")
    @task(1)
    def list_images(self):
        self.client.get(
            "/api/images/",
            headers=self.headers,
            name="[stress] GET /api/images/",
        )

    @tag("stress", "read")
    @task(1)
    def list_forms(self):
        self.client.get(
            "/api/forms",
            headers=self.headers,
            name="[stress] GET /api/forms",
        )

    # --- Write operations under stress ---

    @tag("stress", "write")
    @task(3)
    def create_conversation(self):
        self.client.post(
            "/api/conversations/",
            headers=self.headers,
            json={"title": f"Stress test {random.randint(1, 100000)}"},
            name="[stress] POST /api/conversations/",
        )

    @tag("stress", "write")
    @task(2)
    def analyze_sentiment(self):
        self.client.post(
            "/api/sentiment/analyze",
            headers=self.headers,
            json={"text": random.choice(SAMPLE_TEXTS)},
            name="[stress] POST /api/sentiment/analyze",
        )

    @tag("stress", "write")
    @task(1)
    def security_scan(self):
        self.client.post(
            "/api/security/scan",
            headers=self.headers,
            json={"text": random.choice(SAMPLE_TEXTS)},
            name="[stress] POST /api/security/scan",
        )
