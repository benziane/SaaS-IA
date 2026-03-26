"""
SaaS-IA Soak Test Scenario

Sustained moderate load (50 users) over 30 minutes to detect:
- Memory leaks (gradual increase in response times)
- Connection pool exhaustion
- Database connection leaks
- Redis connection leaks
- File descriptor exhaustion
- Celery task queue build-up

Metrics are collected in 60-second intervals and analyzed for
upward trends in response times and error rates.

Usage:
    locust -f scenarios/soak.py --headless -u 50 -r 5 -t 30m
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
    "Natural language processing advances at an impressive pace.",
]

# ---------------------------------------------------------------------------
# Soak-specific metrics: per-minute interval tracking
# ---------------------------------------------------------------------------

_soak_metrics = {
    "intervals": [],
    "current_interval": {
        "start": time.time(),
        "requests": 0,
        "failures": 0,
        "total_time": 0,
        "times": [],
    },
}

INTERVAL_SECONDS = 60  # 1-minute buckets


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    interval = _soak_metrics["current_interval"]
    now = time.time()

    # Rotate interval
    if now - interval["start"] >= INTERVAL_SECONDS:
        if interval["requests"] > 0:
            times = sorted(interval["times"])
            p50 = times[int(len(times) * 0.50)] if times else 0
            p95 = times[int(len(times) * 0.95)] if times else 0
            p99 = times[int(len(times) * 0.99)] if times else 0

            _soak_metrics["intervals"].append({
                "timestamp": interval["start"],
                "requests": interval["requests"],
                "failures": interval["failures"],
                "avg_ms": interval["total_time"] / interval["requests"],
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
                "rps": interval["requests"] / INTERVAL_SECONDS,
                "error_rate": interval["failures"] / interval["requests"] * 100,
            })
        _soak_metrics["current_interval"] = {
            "start": now,
            "requests": 0,
            "failures": 0,
            "total_time": 0,
            "times": [],
        }
        interval = _soak_metrics["current_interval"]

    interval["requests"] += 1
    interval["total_time"] += response_time

    # Sample response times (keep max 500 per interval for percentiles)
    if len(interval["times"]) < 500:
        interval["times"].append(response_time)
    else:
        interval["times"][random.randint(0, 499)] = response_time

    if exception:
        interval["failures"] += 1


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    if isinstance(environment.runner, WorkerRunner):
        return

    intervals = _soak_metrics["intervals"]
    if not intervals:
        print("\nNo soak test data collected.")
        return

    print("\n" + "=" * 90)
    print("SOAK TEST RESULTS -- STABILITY ANALYSIS")
    print("=" * 90)

    print(
        f"\n{'Minute':<8} {'Requests':>10} {'RPS':>8} "
        f"{'Avg(ms)':>10} {'P50(ms)':>10} {'P95(ms)':>10} {'P99(ms)':>10} {'Err%':>8}"
    )
    print("-" * 90)

    start = intervals[0]["timestamp"]
    p95_values = []

    for iv in intervals:
        minute = int((iv["timestamp"] - start) / 60)
        p95_values.append(iv["p95_ms"])
        print(
            f"{minute:<8} {iv['requests']:>10} {iv['rps']:>8.1f} "
            f"{iv['avg_ms']:>10.1f} {iv['p50_ms']:>10.1f} "
            f"{iv['p95_ms']:>10.1f} {iv['p99_ms']:>10.1f} {iv['error_rate']:>7.1f}%"
        )

    # --- Trend analysis ---
    print("\n" + "-" * 90)
    print("STABILITY ANALYSIS:")

    total_requests = sum(iv["requests"] for iv in intervals)
    total_failures = sum(iv["failures"] for iv in intervals)
    overall_error = (total_failures / total_requests * 100) if total_requests else 0
    avg_rps = sum(iv["rps"] for iv in intervals) / len(intervals)

    print(f"  Total requests:     {total_requests}")
    print(f"  Total failures:     {total_failures}")
    print(f"  Overall error rate: {overall_error:.2f}%")
    print(f"  Average RPS:        {avg_rps:.1f}")

    # Check for upward trend in p95 (potential memory leak)
    if len(p95_values) >= 6:
        first_third = sum(p95_values[:len(p95_values)//3]) / (len(p95_values)//3)
        last_third = sum(p95_values[-len(p95_values)//3:]) / (len(p95_values)//3)

        degradation = ((last_third - first_third) / first_third * 100) if first_third > 0 else 0

        print(f"\n  P95 trend analysis:")
        print(f"    First third avg:  {first_third:.1f}ms")
        print(f"    Last third avg:   {last_third:.1f}ms")
        print(f"    Degradation:      {degradation:+.1f}%")

        if degradation > 50:
            print("    WARNING: Significant performance degradation detected!")
            print("    Possible causes: memory leak, connection pool exhaustion, GC pressure")
        elif degradation > 20:
            print("    CAUTION: Moderate performance degradation observed.")
        else:
            print("    OK: Response times are stable over the test duration.")

    # Error rate trend
    if len(intervals) >= 6:
        first_errors = sum(iv["error_rate"] for iv in intervals[:len(intervals)//3]) / (len(intervals)//3)
        last_errors = sum(iv["error_rate"] for iv in intervals[-len(intervals)//3:]) / (len(intervals)//3)

        print(f"\n  Error rate trend:")
        print(f"    First third:      {first_errors:.2f}%")
        print(f"    Last third:       {last_errors:.2f}%")

        if last_errors > first_errors + 5:
            print("    WARNING: Error rate increasing over time!")
        else:
            print("    OK: Error rate is stable.")

    # Verdict
    print("\n" + "-" * 90)
    issues = []
    if overall_error > 5:
        issues.append(f"overall error rate {overall_error:.1f}% > 5%")
    if len(p95_values) >= 6:
        first_third = sum(p95_values[:len(p95_values)//3]) / (len(p95_values)//3)
        last_third = sum(p95_values[-len(p95_values)//3:]) / (len(p95_values)//3)
        degradation = ((last_third - first_third) / first_third * 100) if first_third > 0 else 0
        if degradation > 50:
            issues.append(f"p95 degradation {degradation:.0f}% > 50%")

    if issues:
        print(f"  VERDICT: FAIL -- {'; '.join(issues)}")
        environment.process_exit_code = 1
    else:
        print("  VERDICT: PASS -- System is stable under sustained load")
        environment.process_exit_code = 0

    print("=" * 90 + "\n")


# ---------------------------------------------------------------------------
# Soak Test User
# ---------------------------------------------------------------------------

class SoakTestUser(HttpUser):
    """
    Moderate-load user for sustained soak testing.

    Mimics realistic usage patterns with balanced read/write distribution.
    Wait times are longer than stress tests to maintain a steady,
    sustainable load level.
    """

    wait_time = between(1, 3)
    host = BASE_URL

    def on_start(self):
        response = self.client.post(
            "/api/auth/login",
            data={"username": DEFAULT_USER, "password": DEFAULT_PASSWORD},
            name="[soak] POST /api/auth/login",
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
            self.token = None

    # --- Health ---

    @tag("soak", "health")
    @task(5)
    def health_live(self):
        self.client.get("/health/live", name="[soak] GET /health/live")

    @tag("soak", "health")
    @task(2)
    def health_ready(self):
        self.client.get("/health/ready", name="[soak] GET /health/ready")

    # --- Reads ---

    @tag("soak", "read")
    @task(8)
    def list_transcriptions(self):
        self.client.get(
            "/api/transcription/",
            headers=self.headers,
            name="[soak] GET /api/transcription/",
        )

    @tag("soak", "read")
    @task(6)
    def list_conversations(self):
        self.client.get(
            "/api/conversations/",
            headers=self.headers,
            name="[soak] GET /api/conversations/",
        )

    @tag("soak", "read")
    @task(5)
    def list_knowledge(self):
        self.client.get(
            "/api/knowledge/documents",
            headers=self.headers,
            name="[soak] GET /api/knowledge/documents",
        )

    @tag("soak", "read")
    @task(4)
    def search_knowledge(self):
        self.client.post(
            "/api/knowledge/search",
            headers=self.headers,
            json={"query": random.choice(["test", "AI", "data", "analysis"]), "limit": 5},
            name="[soak] POST /api/knowledge/search",
        )

    @tag("soak", "read")
    @task(3)
    def list_pipelines(self):
        self.client.get(
            "/api/pipelines/",
            headers=self.headers,
            name="[soak] GET /api/pipelines/",
        )

    @tag("soak", "read")
    @task(3)
    def list_workflows(self):
        self.client.get(
            "/api/workflows/",
            headers=self.headers,
            name="[soak] GET /api/workflows/",
        )

    @tag("soak", "read")
    @task(2)
    def list_content(self):
        self.client.get(
            "/api/content-studio/projects",
            headers=self.headers,
            name="[soak] GET /api/content-studio/projects",
        )

    @tag("soak", "read")
    @task(2)
    def unified_search(self):
        self.client.get(
            "/api/search/?q=test&limit=5",
            headers=self.headers,
            name="[soak] GET /api/search/",
        )

    @tag("soak", "read")
    @task(2)
    def notifications(self):
        self.client.get(
            "/api/notifications?limit=10",
            headers=self.headers,
            name="[soak] GET /api/notifications",
        )

    @tag("soak", "read")
    @task(2)
    def marketplace(self):
        self.client.get(
            "/api/marketplace/listings",
            name="[soak] GET /api/marketplace/listings",
        )

    @tag("soak", "read")
    @task(2)
    def get_me(self):
        self.client.get(
            "/api/auth/me",
            headers=self.headers,
            name="[soak] GET /api/auth/me",
        )

    @tag("soak", "read")
    @task(1)
    def cost_dashboard(self):
        self.client.get(
            "/api/costs/dashboard",
            headers=self.headers,
            name="[soak] GET /api/costs/dashboard",
        )

    @tag("soak", "read")
    @task(1)
    def monitoring_dashboard(self):
        self.client.get(
            "/api/monitoring/dashboard",
            headers=self.headers,
            name="[soak] GET /api/monitoring/dashboard",
        )

    @tag("soak", "read")
    @task(1)
    def list_chatbots(self):
        self.client.get(
            "/api/chatbots",
            headers=self.headers,
            name="[soak] GET /api/chatbots",
        )

    @tag("soak", "read")
    @task(1)
    def get_modules(self):
        self.client.get(
            "/api/modules",
            headers=self.headers,
            name="[soak] GET /api/modules",
        )

    # --- Writes (lower frequency) ---

    @tag("soak", "write")
    @task(2)
    def create_conversation(self):
        self.client.post(
            "/api/conversations/",
            headers=self.headers,
            json={"title": f"Soak test {random.randint(1, 100000)}"},
            name="[soak] POST /api/conversations/",
        )

    @tag("soak", "write")
    @task(1)
    def analyze_sentiment(self):
        self.client.post(
            "/api/sentiment/analyze",
            headers=self.headers,
            json={"text": random.choice(SAMPLE_TEXTS)},
            name="[soak] POST /api/sentiment/analyze",
        )

    @tag("soak", "write")
    @task(1)
    def add_memory(self):
        self.client.post(
            "/api/memory/",
            headers=self.headers,
            json={
                "content": f"Soak test memory {random.randint(1, 100000)}",
                "memory_type": "fact",
            },
            name="[soak] POST /api/memory/",
        )
