# SaaS-IA Load Testing

Comprehensive load testing infrastructure for the SaaS-IA platform using **Locust** (Python) and **k6** (JavaScript).

## Prerequisites

### Locust (Python)

```bash
pip install locust
```

### k6

```bash
# macOS
brew install k6

# Windows (Chocolatey)
choco install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D68
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
  | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update && sudo apt-get install k6

# Docker
docker pull grafana/k6
```

### SaaS-IA Backend

The backend must be running on `http://localhost:8004` (or set `SAASIA_BASE_URL`). You also need a demo user account seeded in the database.

```bash
cd mvp && docker compose up -d
cd mvp/backend && python scripts/seed_data.py  # Creates demo@saas-ia.com
```

## Quick Start

```bash
cd mvp/tests/load

# Locust with web UI (http://localhost:8089)
locust -f locustfile.py

# Locust headless (50 users, 2 min)
locust -f locustfile.py --headless -u 50 -r 10 -t 2m

# k6 (staged ramp-up)
k6 run k6_test.js

# Makefile shortcuts (from mvp/)
make load-test      # Locust web UI
make load-smoke     # Smoke test (5 users, 30s)
make load-stress    # Stress test (ramp to 500)
make load-k6        # k6 test
```

## Test Scenarios

| Scenario | File | Users | Duration | Purpose |
|----------|------|-------|----------|---------|
| **Full** | `locustfile.py` | configurable | configurable | Comprehensive coverage of all endpoints |
| **Smoke** | `scenarios/smoke.py` | 5 | 30s | Quick sanity check before heavier tests |
| **Stress** | `scenarios/stress.py` | ramp to 500 | 7m | Find breaking point and max throughput |
| **Soak** | `scenarios/soak.py` | 50 | 30m | Detect memory leaks and degradation |
| **Spike** | `scenarios/spike.py` | 0-200-0 | 1m | Test spike resilience and recovery |

### Running Specific Scenarios

```bash
# Smoke test
locust -f scenarios/smoke.py --headless -u 5 -r 5 -t 30s

# Stress test
locust -f scenarios/stress.py --headless -u 500 -r 50 -t 7m

# Soak test
locust -f scenarios/soak.py --headless -u 50 -r 5 -t 30m

# Spike test
locust -f scenarios/spike.py --headless -u 200 -r 200 -t 1m
```

## Distributed Testing with Docker

For higher load generation, use the Docker Compose setup with multiple workers:

```bash
cd mvp/tests/load

# Start with 4 workers (default)
docker compose -f docker-compose.load.yml up -d

# Scale to 8 workers
docker compose -f docker-compose.load.yml up -d --scale locust-worker=8

# Open web UI
open http://localhost:8089

# Stop
docker compose -f docker-compose.load.yml down
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SAASIA_BASE_URL` | `http://localhost:8004` | Backend URL |
| `SAASIA_USER` | `demo@saas-ia.com` | Test user email |
| `SAASIA_PASSWORD` | `demo123` | Test user password |
| `SAASIA_API_KEY` | `test_api_key_placeholder` | API key for /v1 endpoints |
| `LOCUST_WORKERS` | `4` | Number of Docker workers |

### Running Against Different Environments

```bash
# Local
SAASIA_BASE_URL=http://localhost:8004 locust -f locustfile.py

# Staging
SAASIA_BASE_URL=https://staging-api.saas-ia.com \
SAASIA_USER=test@staging.com \
SAASIA_PASSWORD=staging_password \
locust -f locustfile.py

# k6 against staging
k6 run --env BASE_URL=https://staging-api.saas-ia.com k6_test.js
```

## Performance Targets

| Metric | Target | Description |
|--------|--------|-------------|
| **P95 latency** | < 2,000ms | 95th percentile response time |
| **P99 latency** | < 5,000ms | 99th percentile response time |
| **Error rate** | < 5% | Percentage of failed requests |
| **Throughput** | > 100 RPS | Requests per second at normal load |
| **Health check latency** | < 500ms | P95 for /health/* endpoints |
| **Auth latency** | < 3,000ms | P95 for login/token operations |
| **Read latency** | < 1,500ms | P95 for list/get operations |
| **Write latency** | < 3,000ms | P95 for create/update operations |

## Interpreting Results

### Locust Web UI

The Locust web UI at `http://localhost:8089` shows:

- **Statistics tab**: Per-endpoint request count, failure count, avg/median/p95/p99 response times, RPS
- **Charts tab**: Real-time graphs of RPS, response times, and number of users
- **Failures tab**: Detailed error messages for failed requests
- **Download Data tab**: Export CSV reports for archiving

### k6 Output

k6 prints a summary after each run:

- `http_req_duration`: Response time percentiles (p50, p90, p95, p99)
- `http_req_failed`: Percentage of requests that returned non-2xx status
- `errors`: Custom error rate metric
- Custom metrics: `auth_duration`, `read_duration`, `write_duration`, `heavy_duration`

Threshold violations are flagged with a red cross in the output.

### Custom Reports

Each scenario prints a custom summary on exit:

- **Smoke**: Pass/fail verdict with error rate check (threshold: 1%)
- **Stress**: Per-interval breakdown with breaking point detection
- **Soak**: Trend analysis comparing first/last third of the test for degradation
- **Spike**: Phase-by-phase analysis with recovery ratio calculation

## Endpoint Coverage

The load tests cover the following endpoint categories (see `mvp/docs/API_REFERENCE.md` for full details):

| Category | Read | Write | Total |
|----------|------|-------|-------|
| Health | 4 | 0 | 4 |
| Auth | 2 | 1 | 3 |
| Transcription | 2 | 0 | 2 |
| Conversation | 1 | 1 | 2 |
| Knowledge | 3 | 0 | 3 |
| Pipelines | 1 | 1 | 2 |
| Content Studio | 2 | 1 | 3 |
| Workflows | 2 | 1 | 3 |
| Agents | 1 | 1 | 2 |
| Sentiment | 0 | 1 | 1 |
| Marketplace | 3 | 0 | 3 |
| Chatbots | 1 | 0 | 1 |
| Search | 2 | 0 | 2 |
| Notifications | 2 | 0 | 2 |
| Costs | 2 | 0 | 2 |
| Billing | 2 | 0 | 2 |
| Monitoring | 2 | 0 | 2 |
| Security | 1 | 1 | 2 |
| Memory | 1 | 1 | 2 |
| Images | 1 | 0 | 1 |
| Videos | 1 | 0 | 1 |
| Presentations | 1 | 0 | 1 |
| Forms | 1 | 1 | 2 |
| Voice | 1 | 0 | 1 |
| Social | 1 | 0 | 1 |
| Integrations | 1 | 0 | 1 |
| Crews | 1 | 0 | 1 |
| Sandbox | 1 | 1 | 2 |
| Data | 1 | 0 | 1 |
| Realtime | 1 | 0 | 1 |
| API Keys | 1 | 0 | 1 |
| AI Assistant | 1 | 1 | 2 |
| Compare | 0 | 1 | 1 |
| Public API v1 | 0 | 2 | 2 |
| WebSocket | 1 | 0 | 1 |
| Feature Flags | 1 | 0 | 1 |
| Modules | 1 | 0 | 1 |
| Root | 1 | 0 | 1 |

## File Structure

```
mvp/tests/load/
  locustfile.py              # Main Locust load test (3 user classes)
  k6_test.js                 # k6 load test (staged, with thresholds)
  docker-compose.load.yml    # Distributed Locust (master + workers)
  README.md                  # This file
  scenarios/
    smoke.py                 # Smoke test (5 users, 30s)
    stress.py                # Stress test (ramp to 500)
    soak.py                  # Soak test (50 users, 30m)
    spike.py                 # Spike test (0-200-0, 1m)
```
