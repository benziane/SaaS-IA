/**
 * SaaS-IA Load Tests -- k6
 *
 * Advanced load testing with staged ramp-up, custom metrics,
 * threshold gates, and comprehensive endpoint coverage.
 *
 * Usage:
 *   k6 run k6_test.js                              # default stages
 *   k6 run --vus 50 --duration 2m k6_test.js       # override
 *   k6 run --env BASE_URL=https://staging k6_test.js
 *
 * Environment variables:
 *   BASE_URL   (default: http://localhost:8004)
 *   USERNAME   (default: demo@saas-ia.com)
 *   PASSWORD   (default: demo123)
 *   API_KEY    (default: test_api_key_placeholder)
 */

import http from "k6/http";
import ws from "k6/ws";
import { check, group, sleep, fail } from "k6";
import { Rate, Trend, Counter, Gauge } from "k6/metrics";

// ---------------------------------------------------------------------------
// Custom metrics
// ---------------------------------------------------------------------------

const errorRate = new Rate("errors");
const authDuration = new Trend("auth_duration", true);
const readDuration = new Trend("read_duration", true);
const writeDuration = new Trend("write_duration", true);
const heavyDuration = new Trend("heavy_duration", true);
const healthDuration = new Trend("health_duration", true);
const rateLimitHits = new Counter("rate_limit_hits");
const successfulLogins = new Counter("successful_logins");
const activeTokens = new Gauge("active_tokens");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const BASE_URL = __ENV.BASE_URL || "http://localhost:8004";
const USERNAME = __ENV.USERNAME || "demo@saas-ia.com";
const PASSWORD = __ENV.PASSWORD || "demo123";
const API_KEY = __ENV.API_KEY || "test_api_key_placeholder";

// Test stages: ramp-up -> normal -> peak -> sustain -> ramp-down
export const options = {
  stages: [
    { duration: "30s", target: 10 }, // Ramp up to 10 users
    { duration: "1m", target: 50 }, // Normal load (50 users)
    { duration: "30s", target: 100 }, // Ramp to peak (100 users)
    { duration: "1m", target: 100 }, // Sustain peak load
    { duration: "30s", target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: [
      "p(95)<2000", // 95th percentile < 2 seconds
      "p(99)<5000", // 99th percentile < 5 seconds
    ],
    errors: ["rate<0.05"], // Error rate < 5%
    http_req_failed: ["rate<0.05"], // HTTP failure rate < 5%
    auth_duration: ["p(95)<3000"], // Auth < 3s at p95
    read_duration: ["p(95)<1500"], // Reads < 1.5s at p95
    write_duration: ["p(95)<3000"], // Writes < 3s at p95
    health_duration: ["p(95)<500"], // Health < 500ms at p95
  },
  // Tags for filtering in Grafana/k6 Cloud
  tags: {
    project: "saas-ia",
    testType: "load",
  },
};

// ---------------------------------------------------------------------------
// Sample data
// ---------------------------------------------------------------------------

const SAMPLE_TEXTS = [
  "This is a great product! I love using it every day.",
  "The customer service was terrible. I waited two hours for a response.",
  "Artificial intelligence is transforming how businesses operate globally.",
  "Our quarterly revenue exceeded expectations by 15% year over year.",
  "Natural language processing continues to advance at an impressive pace.",
];

const SAMPLE_PROMPTS = [
  "Explain quantum computing in simple terms",
  "What are the benefits of microservices architecture?",
  "Summarize the key trends in AI for 2025",
  "How does transfer learning work in deep learning?",
];

function randomChoice(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

// ---------------------------------------------------------------------------
// Auth helper
// ---------------------------------------------------------------------------

function login() {
  const payload = `username=${encodeURIComponent(USERNAME)}&password=${encodeURIComponent(PASSWORD)}`;

  const res = http.post(`${BASE_URL}/api/auth/login`, payload, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    tags: { name: "POST /api/auth/login" },
  });

  authDuration.add(res.timings.duration);

  const loginOk = check(res, {
    "login status 200": (r) => r.status === 200,
    "login has access_token": (r) => {
      try {
        return r.json().access_token !== undefined;
      } catch {
        return false;
      }
    },
  });

  if (!loginOk) {
    errorRate.add(1);
    console.warn(`Login failed: status=${res.status} body=${res.body.substring(0, 200)}`);
    return null;
  }

  errorRate.add(0);
  successfulLogins.add(1);

  const token = res.json().access_token;
  activeTokens.add(1);
  return token;
}

function authHeaders(token) {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

// ---------------------------------------------------------------------------
// Main test function
// ---------------------------------------------------------------------------

export default function () {
  // Login at the start of each VU iteration
  const token = login();
  if (!token) {
    sleep(2);
    return;
  }

  const headers = authHeaders(token);

  // -----------------------------------------------------------------------
  // Group 1: Health Checks
  // -----------------------------------------------------------------------
  group("Health Checks", function () {
    let res;

    res = http.get(`${BASE_URL}/health/live`, {
      tags: { name: "GET /health/live" },
    });
    healthDuration.add(res.timings.duration);
    check(res, { "liveness 200": (r) => r.status === 200 });
    errorRate.add(res.status !== 200);

    res = http.get(`${BASE_URL}/health/ready`, {
      tags: { name: "GET /health/ready" },
    });
    healthDuration.add(res.timings.duration);
    check(res, {
      "readiness 200 or 503": (r) => r.status === 200 || r.status === 503,
    });
    errorRate.add(res.status !== 200 && res.status !== 503);

    res = http.get(`${BASE_URL}/health/startup`, {
      tags: { name: "GET /health/startup" },
    });
    healthDuration.add(res.timings.duration);
    check(res, {
      "startup 200 or 503": (r) => r.status === 200 || r.status === 503,
    });

    res = http.get(`${BASE_URL}/health`, {
      tags: { name: "GET /health" },
    });
    healthDuration.add(res.timings.duration);
    check(res, {
      "health check 200": (r) => r.status === 200 || r.status === 503,
    });

    sleep(0.5);
  });

  // -----------------------------------------------------------------------
  // Group 2: Read Operations (Core Modules)
  // -----------------------------------------------------------------------
  group("Core Module Reads", function () {
    let res;

    // Transcription
    res = http.get(`${BASE_URL}/api/transcription/`, {
      headers: headers,
      tags: { name: "GET /api/transcription/" },
    });
    readDuration.add(res.timings.duration);
    check(res, { "list transcriptions": (r) => r.status === 200 });
    errorRate.add(res.status !== 200);

    res = http.get(`${BASE_URL}/api/transcription/stats`, {
      headers: headers,
      tags: { name: "GET /api/transcription/stats" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Conversations
    res = http.get(`${BASE_URL}/api/conversations/`, {
      headers: headers,
      tags: { name: "GET /api/conversations/" },
    });
    readDuration.add(res.timings.duration);
    check(res, { "list conversations": (r) => r.status === 200 });
    errorRate.add(res.status !== 200);

    // Knowledge Base
    res = http.get(`${BASE_URL}/api/knowledge/documents`, {
      headers: headers,
      tags: { name: "GET /api/knowledge/documents" },
    });
    readDuration.add(res.timings.duration);
    check(res, { "list knowledge docs": (r) => r.status === 200 });
    errorRate.add(res.status !== 200);

    // Knowledge search
    res = http.post(
      `${BASE_URL}/api/knowledge/search`,
      JSON.stringify({ query: "test", limit: 5 }),
      {
        headers: headers,
        tags: { name: "POST /api/knowledge/search" },
      }
    );
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Pipelines
    res = http.get(`${BASE_URL}/api/pipelines/`, {
      headers: headers,
      tags: { name: "GET /api/pipelines/" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Content Studio
    res = http.get(`${BASE_URL}/api/content-studio/projects`, {
      headers: headers,
      tags: { name: "GET /api/content-studio/projects" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    sleep(1);
  });

  // -----------------------------------------------------------------------
  // Group 3: Read Operations (Platform Modules)
  // -----------------------------------------------------------------------
  group("Platform Module Reads", function () {
    let res;

    // Agent runs
    res = http.get(`${BASE_URL}/api/agents/runs`, {
      headers: headers,
      tags: { name: "GET /api/agents/runs" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Workflows
    res = http.get(`${BASE_URL}/api/workflows/`, {
      headers: headers,
      tags: { name: "GET /api/workflows/" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Marketplace (public)
    res = http.get(`${BASE_URL}/api/marketplace/listings`, {
      tags: { name: "GET /api/marketplace/listings" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Chatbots
    res = http.get(`${BASE_URL}/api/chatbots`, {
      headers: headers,
      tags: { name: "GET /api/chatbots" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Unified search
    res = http.get(`${BASE_URL}/api/search/?q=test&limit=5`, {
      headers: headers,
      tags: { name: "GET /api/search/" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Notifications
    res = http.get(`${BASE_URL}/api/notifications?limit=10`, {
      headers: headers,
      tags: { name: "GET /api/notifications" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Cost dashboard
    res = http.get(`${BASE_URL}/api/costs/dashboard`, {
      headers: headers,
      tags: { name: "GET /api/costs/dashboard" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Billing plans (public)
    res = http.get(`${BASE_URL}/api/billing/plans`, {
      tags: { name: "GET /api/billing/plans" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Monitoring
    res = http.get(`${BASE_URL}/api/monitoring/dashboard`, {
      headers: headers,
      tags: { name: "GET /api/monitoring/dashboard" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Security dashboard
    res = http.get(`${BASE_URL}/api/security/dashboard`, {
      headers: headers,
      tags: { name: "GET /api/security/dashboard" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Memory
    res = http.get(`${BASE_URL}/api/memory/`, {
      headers: headers,
      tags: { name: "GET /api/memory/" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // AI providers
    res = http.get(`${BASE_URL}/api/ai-assistant/providers`, {
      headers: headers,
      tags: { name: "GET /api/ai-assistant/providers" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Modules
    res = http.get(`${BASE_URL}/api/modules`, {
      headers: headers,
      tags: { name: "GET /api/modules" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    sleep(1);
  });

  // -----------------------------------------------------------------------
  // Group 4: Additional Module Reads
  // -----------------------------------------------------------------------
  group("Extended Module Reads", function () {
    let res;

    // Images
    res = http.get(`${BASE_URL}/api/images/`, {
      headers: headers,
      tags: { name: "GET /api/images/" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Videos
    res = http.get(`${BASE_URL}/api/videos/`, {
      headers: headers,
      tags: { name: "GET /api/videos/" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Presentations
    res = http.get(`${BASE_URL}/api/presentations`, {
      headers: headers,
      tags: { name: "GET /api/presentations" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Sandboxes
    res = http.get(`${BASE_URL}/api/sandbox/sandboxes`, {
      headers: headers,
      tags: { name: "GET /api/sandbox/sandboxes" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Forms
    res = http.get(`${BASE_URL}/api/forms`, {
      headers: headers,
      tags: { name: "GET /api/forms" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Voice profiles
    res = http.get(`${BASE_URL}/api/voice/profiles`, {
      headers: headers,
      tags: { name: "GET /api/voice/profiles" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Social accounts
    res = http.get(`${BASE_URL}/api/social-publisher/accounts`, {
      headers: headers,
      tags: { name: "GET /api/social-publisher/accounts" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Crews
    res = http.get(`${BASE_URL}/api/crews/`, {
      headers: headers,
      tags: { name: "GET /api/crews/" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Data datasets
    res = http.get(`${BASE_URL}/api/data/datasets`, {
      headers: headers,
      tags: { name: "GET /api/data/datasets" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Realtime sessions
    res = http.get(`${BASE_URL}/api/realtime/sessions`, {
      headers: headers,
      tags: { name: "GET /api/realtime/sessions" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Feature flags
    res = http.get(`${BASE_URL}/api/feature-flags/`, {
      headers: headers,
      tags: { name: "GET /api/feature-flags/" },
    });
    readDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    sleep(1);
  });

  // -----------------------------------------------------------------------
  // Group 5: Write Operations
  // -----------------------------------------------------------------------
  group("Write Operations", function () {
    let res;

    // Create conversation
    res = http.post(
      `${BASE_URL}/api/conversations/`,
      JSON.stringify({
        title: `k6 load test ${randomInt(1, 100000)}`,
      }),
      {
        headers: headers,
        tags: { name: "POST /api/conversations/" },
      }
    );
    writeDuration.add(res.timings.duration);
    check(res, { "create conversation": (r) => r.status === 200 || r.status === 201 });
    errorRate.add(res.status !== 200 && res.status !== 201);

    // Sentiment analysis
    res = http.post(
      `${BASE_URL}/api/sentiment/analyze`,
      JSON.stringify({ text: randomChoice(SAMPLE_TEXTS) }),
      {
        headers: headers,
        tags: { name: "POST /api/sentiment/analyze" },
      }
    );
    writeDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    // Security scan
    res = http.post(
      `${BASE_URL}/api/security/scan`,
      JSON.stringify({ text: randomChoice(SAMPLE_TEXTS) }),
      {
        headers: headers,
        tags: { name: "POST /api/security/scan" },
      }
    );
    writeDuration.add(res.timings.duration);
    errorRate.add(res.status !== 200);

    sleep(1);
  });

  // -----------------------------------------------------------------------
  // Group 6: AI-Heavy Operations (subset of VUs)
  // -----------------------------------------------------------------------
  if (__VU % 5 === 0) {
    group("AI Heavy Operations", function () {
      let res;

      // Compare providers
      res = http.post(
        `${BASE_URL}/api/compare/run`,
        JSON.stringify({
          prompt: randomChoice(SAMPLE_PROMPTS),
          providers: ["gemini"],
        }),
        {
          headers: headers,
          tags: { name: "POST /api/compare/run" },
          timeout: "30s",
        }
      );
      heavyDuration.add(res.timings.duration);
      errorRate.add(res.status !== 200);

      // Process text with AI
      res = http.post(
        `${BASE_URL}/api/ai-assistant/process-text`,
        JSON.stringify({
          text: randomChoice(SAMPLE_TEXTS),
          instruction: "Summarize this text in one sentence",
        }),
        {
          headers: headers,
          tags: { name: "POST /api/ai-assistant/process-text" },
          timeout: "30s",
        }
      );
      heavyDuration.add(res.timings.duration);
      errorRate.add(res.status !== 200);

      // Knowledge RAG
      res = http.post(
        `${BASE_URL}/api/knowledge/ask`,
        JSON.stringify({
          question: randomChoice(SAMPLE_PROMPTS),
          limit: 3,
        }),
        {
          headers: headers,
          tags: { name: "POST /api/knowledge/ask" },
          timeout: "30s",
        }
      );
      heavyDuration.add(res.timings.duration);
      errorRate.add(res.status !== 200);

      sleep(2);
    });
  }

  // -----------------------------------------------------------------------
  // Group 7: Rate Limit Validation (1 in 10 VUs)
  // -----------------------------------------------------------------------
  if (__VU % 10 === 0) {
    group("Rate Limit Validation", function () {
      // Rapid-fire requests to trigger rate limiting
      let hitRateLimit = false;
      for (let i = 0; i < 20; i++) {
        const res = http.get(`${BASE_URL}/api/auth/me`, {
          headers: headers,
          tags: { name: "GET /api/auth/me [rate-limit-test]" },
        });

        if (res.status === 429) {
          hitRateLimit = true;
          rateLimitHits.add(1);
          check(res, {
            "rate limit returns 429": (r) => r.status === 429,
            "rate limit has Retry-After": (r) =>
              r.headers["Retry-After"] !== undefined ||
              r.headers["retry-after"] !== undefined,
          });
          break;
        }
      }

      // Verify rate limiting is working (it should have kicked in)
      // Note: this may not trigger depending on server configuration
      if (!hitRateLimit) {
        console.log("Rate limit not triggered after 20 rapid requests on /api/auth/me");
      }

      sleep(2);
    });
  }

  // -----------------------------------------------------------------------
  // Group 8: WebSocket Connection Test (1 in 20 VUs)
  // -----------------------------------------------------------------------
  if (__VU % 20 === 0) {
    group("WebSocket Connection", function () {
      const wsUrl = BASE_URL.replace("http", "ws") + `/ws/${token}`;

      const res = ws.connect(wsUrl, {}, function (socket) {
        socket.on("open", function () {
          // Send a ping
          socket.send(JSON.stringify({ type: "ping", data: {} }));
        });

        socket.on("message", function (msg) {
          try {
            const data = JSON.parse(msg);
            check(data, {
              "ws message has type": (d) => d.type !== undefined,
            });
          } catch (e) {
            // Binary message or parse error, that is fine
          }
        });

        socket.on("error", function (e) {
          console.warn(`WebSocket error: ${e}`);
          errorRate.add(1);
        });

        // Keep connection open briefly then close
        sleep(2);
        socket.close();
      });

      check(res, {
        "ws connected": (r) => r && r.status === 101,
      });

      sleep(1);
    });
  }

  // -----------------------------------------------------------------------
  // Group 9: Public API v1 (API Key auth)
  // -----------------------------------------------------------------------
  if (__VU % 3 === 0) {
    group("Public API v1", function () {
      let res;
      const apiHeaders = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json",
      };

      // Process text
      res = http.post(
        `${BASE_URL}/v1/process`,
        JSON.stringify({
          text: randomChoice(SAMPLE_TEXTS),
          operation: "summarize",
        }),
        {
          headers: apiHeaders,
          tags: { name: "POST /v1/process" },
        }
      );
      readDuration.add(res.timings.duration);
      errorRate.add(res.status !== 200 && res.status !== 201);

      // Transcribe
      res = http.post(
        `${BASE_URL}/v1/transcribe`,
        JSON.stringify({
          url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        }),
        {
          headers: apiHeaders,
          tags: { name: "POST /v1/transcribe" },
        }
      );
      readDuration.add(res.timings.duration);
      // Transcribe may return 200, 201, or 202 (accepted)
      errorRate.add(res.status < 200 || res.status >= 300);

      sleep(1);
    });
  }

  // Final sleep between iterations
  sleep(randomInt(1, 3));
}

// ---------------------------------------------------------------------------
// Setup & Teardown
// ---------------------------------------------------------------------------

export function setup() {
  console.log(`\n${"=".repeat(60)}`);
  console.log("SaaS-IA k6 Load Test");
  console.log(`  Target:    ${BASE_URL}`);
  console.log(`  User:      ${USERNAME}`);
  console.log(`${"=".repeat(60)}\n`);

  // Verify the server is reachable
  const res = http.get(`${BASE_URL}/health/live`);
  if (res.status !== 200) {
    fail(`Server is not reachable at ${BASE_URL}/health/live (status=${res.status})`);
  }

  // Login once to verify credentials
  const payload = `username=${encodeURIComponent(USERNAME)}&password=${encodeURIComponent(PASSWORD)}`;
  const loginRes = http.post(`${BASE_URL}/api/auth/login`, payload, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  if (loginRes.status !== 200) {
    fail(`Cannot authenticate: status=${loginRes.status}`);
  }

  return { verified: true };
}

export function teardown(data) {
  console.log(`\n${"=".repeat(60)}`);
  console.log("SaaS-IA k6 Load Test COMPLETE");
  console.log(`${"=".repeat(60)}\n`);
}
