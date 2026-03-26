"""
SaaS-IA Spike Test Scenario

Tests system resilience to sudden traffic spikes and recovery behavior.
Validates that the system recovers gracefully after a traffic burst.

Pattern:
  0:00 - 0:10   baseline (10 users)
  0:10 - 0:20   spike UP to 200 users
  0:20 - 0:40   hold at 200 users
  0:40 - 0:50   spike DOWN to 10 users
  0:50 - 1:00   verify recovery at 10 users

Usage:
    locust -f scenarios/spike.py --headless -t 1m
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
]

# ---------------------------------------------------------------------------
# Spike-specific metrics: track pre-spike, during-spike, post-spike
# ---------------------------------------------------------------------------

_spike_metrics = {
    "phases": defaultdict(lambda: {
        "requests": 0,
        "failures": 0,
        "total_time": 0,
        "times": [],
    }),
    "start_time": None,
}

# Phase boundaries (seconds from test start)
PHASE_BOUNDARIES = [
    (0, 10, "pre-spike"),
    (10, 20, "ramp-up"),
    (20, 40, "sustained-spike"),
    (40, 50, "ramp-down"),
    (50, 60, "recovery"),
]


def _get_phase(elapsed_seconds):
    for start, end, name in PHASE_BOUNDARIES:
        if start <= elapsed_seconds < end:
            return name
    return "overtime"


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    _spike_metrics["start_time"] = time.time()


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    if _spike_metrics["start_time"] is None:
        return

    elapsed = time.time() - _spike_metrics["start_time"]
    phase = _get_phase(elapsed)
    stats = _spike_metrics["phases"][phase]

    stats["requests"] += 1
    stats["total_time"] += response_time

    if len(stats["times"]) < 1000:
        stats["times"].append(response_time)
    else:
        stats["times"][random.randint(0, 999)] = response_time

    if exception:
        stats["failures"] += 1


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    if isinstance(environment.runner, WorkerRunner):
        return

    phases = _spike_metrics["phases"]
    if not phases:
        print("\nNo spike test data collected.")
        return

    print("\n" + "=" * 80)
    print("SPIKE TEST RESULTS -- RESILIENCE ANALYSIS")
    print("=" * 80)

    print(
        f"\n{'Phase':<20} {'Requests':>10} {'Failures':>10} {'Avg(ms)':>10} "
        f"{'P95(ms)':>10} {'P99(ms)':>10} {'Err%':>8}"
    )
    print("-" * 80)

    phase_order = ["pre-spike", "ramp-up", "sustained-spike", "ramp-down", "recovery", "overtime"]

    pre_spike_p95 = None
    recovery_p95 = None

    for phase_name in phase_order:
        if phase_name not in phases:
            continue

        stats = phases[phase_name]
        count = stats["requests"]
        if count == 0:
            continue

        avg = stats["total_time"] / count
        err_rate = (stats["failures"] / count * 100)

        times = sorted(stats["times"])
        p95 = times[int(len(times) * 0.95)] if times else 0
        p99 = times[int(len(times) * 0.99)] if times else 0

        if phase_name == "pre-spike":
            pre_spike_p95 = p95
        if phase_name == "recovery":
            recovery_p95 = p95

        print(
            f"{phase_name:<20} {count:>10} {stats['failures']:>10} "
            f"{avg:>10.1f} {p95:>10.1f} {p99:>10.1f} {err_rate:>7.1f}%"
        )

    # --- Recovery analysis ---
    print("\n" + "-" * 80)
    print("RECOVERY ANALYSIS:")

    total_requests = sum(p["requests"] for p in phases.values())
    total_failures = sum(p["failures"] for p in phases.values())
    overall_error = (total_failures / total_requests * 100) if total_requests else 0

    print(f"  Total requests:     {total_requests}")
    print(f"  Total failures:     {total_failures}")
    print(f"  Overall error rate: {overall_error:.2f}%")

    if pre_spike_p95 is not None and recovery_p95 is not None:
        recovery_ratio = recovery_p95 / pre_spike_p95 if pre_spike_p95 > 0 else float("inf")
        print(f"\n  Pre-spike P95:      {pre_spike_p95:.1f}ms")
        print(f"  Recovery P95:       {recovery_p95:.1f}ms")
        print(f"  Recovery ratio:     {recovery_ratio:.2f}x")

        if recovery_ratio <= 1.5:
            print("  Recovery status:    EXCELLENT (within 1.5x of baseline)")
        elif recovery_ratio <= 2.0:
            print("  Recovery status:    GOOD (within 2x of baseline)")
        elif recovery_ratio <= 3.0:
            print("  Recovery status:    ACCEPTABLE (within 3x of baseline)")
        else:
            print("  Recovery status:    POOR (exceeds 3x baseline)")
            print("  Possible causes:   connection pool exhaustion, thread starvation, GC pause")

    # Check spike-phase error rate
    spike_stats = phases.get("sustained-spike")
    if spike_stats and spike_stats["requests"] > 0:
        spike_error = spike_stats["failures"] / spike_stats["requests"] * 100
        print(f"\n  Spike error rate:   {spike_error:.1f}%")
        if spike_error > 20:
            print("  WARNING: High error rate during spike indicates capacity issues")
        elif spike_error > 10:
            print("  CAUTION: Elevated errors during spike, may need auto-scaling")
        else:
            print("  OK: System handled spike with acceptable error rate")

    # Verdict
    print("\n" + "-" * 80)
    issues = []
    if overall_error > 10:
        issues.append(f"overall error rate {overall_error:.1f}% > 10%")

    recovery_stats = phases.get("recovery")
    if recovery_stats and recovery_stats["requests"] > 0:
        recovery_error = recovery_stats["failures"] / recovery_stats["requests"] * 100
        if recovery_error > 5:
            issues.append(f"recovery error rate {recovery_error:.1f}% > 5%")

    if pre_spike_p95 and recovery_p95 and recovery_p95 / pre_spike_p95 > 3:
        issues.append("recovery response time > 3x baseline")

    if issues:
        print(f"  VERDICT: FAIL -- {'; '.join(issues)}")
        environment.process_exit_code = 1
    else:
        print("  VERDICT: PASS -- System recovers gracefully from traffic spikes")
        environment.process_exit_code = 0

    print("=" * 80 + "\n")


# ---------------------------------------------------------------------------
# Spike Test User
# ---------------------------------------------------------------------------

class SpikeTestUser(HttpUser):
    """
    User for spike testing.

    Fast wait times to generate maximum throughput during spike phases.
    Exercises a focused set of high-traffic endpoints.
    """

    wait_time = between(0.1, 0.5)
    host = BASE_URL

    def on_start(self):
        response = self.client.post(
            "/api/auth/login",
            data={"username": DEFAULT_USER, "password": DEFAULT_PASSWORD},
            name="[spike] POST /api/auth/login",
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
            self.token = None

    # --- Health (always) ---

    @tag("spike", "health")
    @task(10)
    def health_live(self):
        self.client.get("/health/live", name="[spike] GET /health/live")

    @tag("spike", "health")
    @task(3)
    def health_ready(self):
        self.client.get("/health/ready", name="[spike] GET /health/ready")

    # --- High-frequency reads ---

    @tag("spike", "read")
    @task(8)
    def list_transcriptions(self):
        self.client.get(
            "/api/transcription/",
            headers=self.headers,
            name="[spike] GET /api/transcription/",
        )

    @tag("spike", "read")
    @task(6)
    def list_conversations(self):
        self.client.get(
            "/api/conversations/",
            headers=self.headers,
            name="[spike] GET /api/conversations/",
        )

    @tag("spike", "read")
    @task(5)
    def list_knowledge(self):
        self.client.get(
            "/api/knowledge/documents",
            headers=self.headers,
            name="[spike] GET /api/knowledge/documents",
        )

    @tag("spike", "read")
    @task(4)
    def list_pipelines(self):
        self.client.get(
            "/api/pipelines/",
            headers=self.headers,
            name="[spike] GET /api/pipelines/",
        )

    @tag("spike", "read")
    @task(4)
    def get_me(self):
        self.client.get(
            "/api/auth/me",
            headers=self.headers,
            name="[spike] GET /api/auth/me",
        )

    @tag("spike", "read")
    @task(3)
    def list_workflows(self):
        self.client.get(
            "/api/workflows/",
            headers=self.headers,
            name="[spike] GET /api/workflows/",
        )

    @tag("spike", "read")
    @task(3)
    def list_content(self):
        self.client.get(
            "/api/content-studio/projects",
            headers=self.headers,
            name="[spike] GET /api/content-studio/projects",
        )

    @tag("spike", "read")
    @task(2)
    def unified_search(self):
        self.client.get(
            "/api/search/?q=test&limit=5",
            headers=self.headers,
            name="[spike] GET /api/search/",
        )

    @tag("spike", "read")
    @task(2)
    def marketplace_listings(self):
        self.client.get(
            "/api/marketplace/listings",
            name="[spike] GET /api/marketplace/listings",
        )

    @tag("spike", "read")
    @task(2)
    def notifications(self):
        self.client.get(
            "/api/notifications?limit=10",
            headers=self.headers,
            name="[spike] GET /api/notifications",
        )

    @tag("spike", "read")
    @task(1)
    def list_agents(self):
        self.client.get(
            "/api/agents/runs",
            headers=self.headers,
            name="[spike] GET /api/agents/runs",
        )

    @tag("spike", "read")
    @task(1)
    def list_chatbots(self):
        self.client.get(
            "/api/chatbots",
            headers=self.headers,
            name="[spike] GET /api/chatbots",
        )

    # --- Writes (sparse during spikes) ---

    @tag("spike", "write")
    @task(2)
    def create_conversation(self):
        self.client.post(
            "/api/conversations/",
            headers=self.headers,
            json={"title": f"Spike test {random.randint(1, 100000)}"},
            name="[spike] POST /api/conversations/",
        )

    @tag("spike", "write")
    @task(1)
    def analyze_sentiment(self):
        self.client.post(
            "/api/sentiment/analyze",
            headers=self.headers,
            json={"text": random.choice(SAMPLE_TEXTS)},
            name="[spike] POST /api/sentiment/analyze",
        )
