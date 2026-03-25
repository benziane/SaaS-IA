# Security Audit Report - SaaS-IA v4.0.0

**Date:** 2026-03-25
**Auditor:** Automated security review (Claude Code)
**Scope:** Backend application (`mvp/backend/app/`) - 10 critical files against OWASP Top 10
**Status:** READ-ONLY analysis; no changes were made to the codebase

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 3     |
| High     | 5     |
| Medium   | 6     |
| Low      | 4     |

---

## Critical (immediate action required)

### CRIT-01: Real API Keys Committed in `.env` (Appears Untracked but Present on Disk)

**OWASP:** A02 - Cryptographic Failures
**File:** `mvp/backend/.env`
**Finding:** The `.env` file contains real, functional API keys for production services:
- `ASSEMBLYAI_API_KEY=30efa8c7...` (real key)
- `GEMINI_API_KEY=AIzaSyAB3...` (real Google Cloud key)
- `CLAUDE_API_KEY=sk-ant-api03-...` (real Anthropic key)
- `GROQ_API_KEY=gsk_linPN2...` (real Groq key)
- `SECRET_KEY=change-me-in-production-use-strong-random-key-min-32-chars` (weak/default)

The `.env` file is correctly gitignored and NOT tracked by git. However, the `.env.example` also instructs users to use `change-me-in-production-use-strong-random-key` as SECRET_KEY, which is a predictable default. If any developer copies `.env.example` to `.env` without changing it, all JWTs are signed with a known key.

**Risk:** If the repository is ever cloned or backed up to an insecure location, all API keys are exposed. The weak default SECRET_KEY means anyone who knows the default can forge valid JWT tokens.

**Remediation:**
1. Rotate ALL API keys immediately (Gemini, Claude, Groq, AssemblyAI) as they have been visible on disk.
2. Use a secrets manager (HashiCorp Vault, AWS Secrets Manager, or `doppler`) for production.
3. The lifecycle.py check (line 114) logs a critical warning for weak SECRET_KEY but does NOT prevent startup. Consider refusing to start in `production` environment with the default key.

---

### CRIT-02: Code Sandbox Executes Arbitrary Code Without Container Isolation

**OWASP:** A03 - Injection, A04 - Insecure Design
**File:** `app/modules/code_sandbox/service.py`
**Finding:** The `_execute_code_subprocess()` function runs user-supplied Python code via `asyncio.create_subprocess_exec(sys.executable, "-c", restricted_code)`. The security relies on:
1. Regex-based import blocking (bypassable)
2. A custom `_RestrictedImporter` in `sys.meta_path` (bypassable)
3. Removing builtins like `exec`, `eval`, `open` (bypassable)

Known bypass vectors:
- **Attribute access chains:** `().__class__.__bases__[0].__subclasses__()` can access `os._wrap_close` or similar to execute shell commands without importing `os`.
- **`type()` to reconstruct builtins:** `type('', (), {'__init__': lambda self: None})` plus metaclass tricks.
- **`vars(__builtins__)` before restriction:** The restricted code prepends safety code, but a carefully crafted multiline string or encoding trick could execute before the restrictions apply.
- **`__class__.__subclasses__` traversal** to find `subprocess.Popen`, `os.system`, etc.
- The regex `IMPORT_PATTERN` only checks lines starting with `import` or `from`; inline `__import__` in expressions or `importlib` through subclass chains is not caught.

The subprocess runs as the **same OS user** as the backend with full filesystem and network access. There is no Linux namespace isolation, no `seccomp` profile, no cgroup limits, no Docker container.

**Risk:** Remote Code Execution (RCE) on the backend host. Any authenticated user can escape the sandbox and execute arbitrary OS commands.

**Remediation:**
1. **Immediate:** Run sandboxed code inside a disposable Docker container with `--network=none`, `--read-only`, memory/CPU limits, and a non-root user.
2. **Short-term:** Use a proper sandboxing library like `RestrictedPython` or `pyodide` (WebAssembly-based Python).
3. **Long-term:** Consider a dedicated code execution service (e.g., Firecracker microVMs).

---

### CRIT-03: No JWT Token Revocation Mechanism

**OWASP:** A07 - Authentication Failures, A01 - Broken Access Control
**File:** `app/auth.py`
**Finding:** The application issues JWT access tokens (30-minute TTL) and refresh tokens (7-day TTL) but has NO token revocation mechanism. There is:
- No token blacklist/blocklist in Redis or database
- No server-side session store
- No way to invalidate tokens after password change
- No way to force-logout a compromised user

When a user changes their password (line 384), the old tokens remain valid until they expire naturally. A refresh token remains valid for 7 days after a password compromise.

**Risk:** If credentials are compromised, there is no way to immediately revoke access. An attacker with a stolen refresh token has 7 days of persistent access even after the user changes their password.

**Remediation:**
1. Implement a Redis-backed token blacklist. On password change or logout, add the user's current tokens (or a `jti` claim) to the blacklist.
2. Add a `password_changed_at` timestamp to the User model and check it during token validation -- reject tokens issued before the last password change.
3. Consider shorter refresh token TTL (24-48 hours instead of 7 days).

---

## High (fix soon)

### HIGH-01: Metrics Endpoint Uses SECRET_KEY as Authentication Token

**OWASP:** A02 - Cryptographic Failures, A05 - Security Misconfiguration
**File:** `app/main.py` (lines 181-182)
**Finding:** The `/metrics` endpoint accepts `X-Metrics-Token` header and compares it to `settings.SECRET_KEY`:
```python
token_valid = request.headers.get("X-Metrics-Token") == settings.SECRET_KEY
```
This exposes the JWT signing key as a bearer token in HTTP headers. If the metrics scraper's request is logged anywhere (reverse proxy logs, load balancer, network capture), the SECRET_KEY is compromised -- allowing an attacker to forge any JWT token.

**Risk:** SECRET_KEY exposure through logs, network interception, or misconfigured monitoring.

**Remediation:** Use a separate `METRICS_TOKEN` environment variable that is distinct from `SECRET_KEY`.

---

### HIGH-02: API Key Daily Rate Limit Not Enforced

**OWASP:** A04 - Insecure Design
**File:** `app/modules/api_keys/service.py`, `app/modules/api_keys/public_routes.py`
**Finding:** The `APIKey` model has a `rate_limit_per_day` field (default: 1000), but the `verify_key()` method never checks the daily usage count. It only checks:
- Key hash match
- Active status
- Expiration date

There is no counter increment, no daily usage tracking, and no enforcement of the per-key rate limit. The `public_routes.py` relies only on the per-endpoint slowapi limit (10/minute).

**Risk:** A single API key can make unlimited requests per day, bypassing the intended rate limiting. This could lead to excessive API costs and abuse.

**Remediation:** Track API key usage in Redis (increment a daily counter keyed by `apikey:{key_hash}:daily:{date}`) and check it in `verify_key()`.

---

### HIGH-03: X-Forwarded-For Header Trusted Without Validation

**OWASP:** A05 - Security Misconfiguration
**File:** `app/middleware/rate_limiter.py` (lines 204-206)
**Finding:** The rate limiter trusts the `X-Forwarded-For` header directly:
```python
xff = request.headers.get("x-forwarded-for")
if xff:
    return xff.split(",")[0].strip()
```
Any client can set `X-Forwarded-For: 1.2.3.4` to spoof their IP address and get a fresh rate limit window. This applies to both the sliding window middleware and the slowapi-based rate limiter.

**Risk:** Complete bypass of IP-based rate limiting. An attacker can send unlimited requests by rotating the `X-Forwarded-For` value.

**Remediation:**
1. Configure Uvicorn/Gunicorn with `--forwarded-allow-ips` to only trust the reverse proxy's IP.
2. Use Starlette's `TrustedHostMiddleware` or configure `ProxyHeadersMiddleware` with trusted proxy IPs.
3. Only use `X-Forwarded-For` when running behind a known reverse proxy.

---

### HIGH-04: OpenAPI/Swagger Documentation Exposed Unconditionally

**OWASP:** A05 - Security Misconfiguration
**File:** `app/main.py` (lines 40-41)
**Finding:** The `/docs` (Swagger UI) and `/redoc` endpoints are always enabled regardless of environment:
```python
docs_url="/docs",
redoc_url="/redoc",
```
In production, this exposes the full API schema, including all internal endpoints, request/response models, and authentication mechanisms.

**Risk:** Information disclosure. Attackers can use the API documentation to map all endpoints and craft targeted attacks.

**Remediation:** Disable docs in production:
```python
docs_url="/docs" if settings.DEBUG else None,
redoc_url="/redoc" if settings.DEBUG else None,
```

---

### HIGH-05: `/api/modules` Endpoint Exposes Internal Architecture Without Authentication

**OWASP:** A01 - Broken Access Control
**File:** `app/main.py` (lines 156-168)
**Finding:** The `/api/modules` endpoint lists all registered modules, their versions, prefixes, tags, and dependencies with no authentication requirement. This reveals the full internal architecture to any unauthenticated user.

**Risk:** Information disclosure that helps attackers identify attack surface, module versions, and potential vulnerabilities.

**Remediation:** Require admin authentication or remove this endpoint in production.

---

## Medium (plan fix)

### MED-01: DEBUG=True by Default in Config

**OWASP:** A05 - Security Misconfiguration
**File:** `app/config.py` (line 15)
**Finding:** `DEBUG: bool = True` is the default. This causes:
- SQLAlchemy query logging (`echo=settings.DEBUG` in `database.py` line 26) which logs all SQL queries including potentially sensitive data.
- Uvicorn auto-reload in `main.py` line 216.
- Development metrics endpoint access without authentication.

If the `.env` file is missing or the `DEBUG` variable is unset, the application runs in debug mode by default.

**Risk:** SQL query logging in production could expose sensitive data. Auto-reload in production is a stability risk.

**Remediation:** Default `DEBUG` to `False` and `ENVIRONMENT` to `"production"`. Require explicit opt-in for debug mode.

---

### MED-02: No Account Lockout After Failed Login Attempts

**OWASP:** A07 - Authentication Failures
**File:** `app/auth.py`
**Finding:** The login endpoint has a rate limit of 5 requests/minute, but there is no account lockout mechanism. An attacker can try 5 passwords per minute indefinitely (7,200 attempts per day) without the account being locked.

**Risk:** Slow brute-force attacks against accounts with weak passwords are feasible over time.

**Remediation:** Implement progressive lockout: after N failed attempts for a given email (tracked in Redis), temporarily lock the account and require CAPTCHA or email verification.

---

### MED-03: Refresh Token Not Invalidated on Rotation

**OWASP:** A08 - Data Integrity
**File:** `app/auth.py` (lines 262-316)
**Finding:** The `/auth/refresh` endpoint issues new token pairs (rotation) but does not invalidate the old refresh token. Both the old and new refresh tokens remain valid until they expire. This defeats the purpose of token rotation.

If an attacker captures a refresh token, using it will generate a new pair, but the legitimate user's original tokens still work -- the attacker and user both have valid tokens with no detection.

**Risk:** Refresh token replay attacks. Token rotation without invalidation provides false security.

**Remediation:** Store refresh token identifiers (jti) in Redis. On rotation, invalidate the previous token. If a previously-used token is presented, invalidate ALL tokens for that user (token family detection).

---

### MED-04: Stripe Webhook Missing Rate Limiting

**OWASP:** A04 - Insecure Design
**File:** `app/modules/billing/routes.py` (line 147)
**Finding:** The `/webhook` endpoint has no rate limiting decorator. While webhook signature verification prevents unauthorized events, an attacker who replays valid webhook payloads (before Stripe's replay protection window) or sends crafted payloads to trigger signature verification failures can cause excessive CPU usage from repeated `stripe.Webhook.construct_event()` calls.

**Risk:** Resource exhaustion through webhook endpoint abuse.

**Remediation:** Add basic rate limiting to the webhook endpoint (e.g., `100/minute`) and consider adding idempotency checks (store processed event IDs).

---

### MED-05: SQL Echo Logs Full Queries in Debug Mode

**OWASP:** A09 - Security Logging and Monitoring Failures
**File:** `app/database.py` (line 26)
**Finding:** `echo=settings.DEBUG` logs all SQL queries when DEBUG is True. This includes:
- User credentials lookups
- API key hashes
- PII from scanned content
- Any data passing through the ORM

**Risk:** Sensitive data exposure in logs.

**Remediation:** Never use `echo=True` in production. Add a separate `SQL_ECHO` configuration variable, defaulting to `False`.

---

### MED-06: Seed Script Contains Hardcoded Credentials

**OWASP:** A07 - Authentication Failures
**File:** `scripts/seed_data.py` (lines 61, 67, 77, 83)
**Finding:** Hardcoded admin credentials: `admin@saas-ia.com / Admin123!` and `demo@saas-ia.com / Demo123!`. These are printed to stdout and will exist in any seeded database. If the seed script is run in production (accidentally or intentionally), these become known-credential backdoors.

**Risk:** Default admin credentials in production environments.

**Remediation:**
1. Check `ENVIRONMENT` before running seed -- refuse to seed in production, or generate random passwords.
2. Force password change on first login for seeded accounts.
3. Remove the password-printing output.

---

## Low (improvement)

### LOW-01: `datetime.utcnow()` is Deprecated

**OWASP:** N/A (code quality)
**Files:** `app/auth.py`, `app/modules/billing/stripe_service.py`, `app/modules/code_sandbox/service.py`, and others
**Finding:** Multiple files use `datetime.utcnow()` which was deprecated in Python 3.12. It returns a naive datetime without timezone information, which can cause subtle bugs with token expiration if the server timezone changes.

**Remediation:** Use `datetime.now(datetime.UTC)` (Python 3.11+) throughout.

---

### LOW-02: Bcrypt Rounds Not Explicitly Configured

**OWASP:** A02 - Cryptographic Failures
**File:** `app/auth.py` (line 25)
**Finding:** `CryptContext(schemes=["bcrypt"], deprecated="auto")` uses the passlib default rounds (12). While acceptable today, this should be explicitly set and periodically increased.

**Remediation:** Explicitly set `rounds=12` (or higher) and document the policy. Consider using Argon2id as the primary hash with bcrypt as fallback.

---

### LOW-03: CORS `allow_methods=["*"]` and `allow_headers=["*"]`

**OWASP:** A05 - Security Misconfiguration
**File:** `app/main.py` (lines 94-95)
**Finding:** CORS is configured with wildcard methods and headers. While `allow_origins` is properly restricted to specific origins, the wildcard methods/headers are more permissive than necessary.

**Remediation:** Restrict to the HTTP methods and headers actually used by the frontend:
```python
allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
```

---

### LOW-04: Health Check Endpoint Reveals Environment Name

**OWASP:** A05 - Security Misconfiguration
**File:** `app/main.py` (lines 147-152)
**Finding:** The `/health` endpoint returns `settings.ENVIRONMENT` in its response, confirming whether a server is running `development`, `staging`, or `production`. This is minor information leakage.

**Remediation:** Return only `status: healthy` and version. Move detailed info to an authenticated admin endpoint.

---

## Positive Findings

These are security measures already in place that demonstrate good security practices:

1. **Password hashing with bcrypt** (`app/auth.py`): Proper use of passlib with bcrypt. Passwords are never stored in plaintext.

2. **Password strength validation** (`app/schemas/user.py`): Enforces minimum 8 characters, at least one letter, at least one digit, maximum 100 characters.

3. **Input sanitization** (`app/utils/sanitize.py`): HTML tag stripping, control character removal, Unicode normalization (NFC), and path traversal validation are properly implemented.

4. **JWT token type separation** (`app/auth.py`): Refresh tokens carry `type: "refresh"` and are explicitly rejected when used as access tokens (line 110). This prevents token confusion attacks.

5. **API key hashing with SHA-256** (`app/modules/api_keys/service.py`): API keys are hashed before storage. Only the prefix (first 8 chars) and hash are stored; the full key is shown only once at creation.

6. **Comprehensive security headers** (`app/middleware/security_headers.py`): HSTS with preload, strict CSP, X-Frame-Options DENY, X-Content-Type-Options nosniff, Referrer-Policy, Permissions-Policy, COOP, CORP, and Server header removal.

7. **Dual rate limiting** (`app/rate_limit.py`, `app/middleware/rate_limiter.py`): Per-endpoint slowapi limits plus global sliding-window Redis-backed rate limiting with burst protection. Fail-open design ensures availability.

8. **Stripe webhook signature verification** (`app/modules/billing/stripe_service.py`): Webhooks are properly verified using `stripe.Webhook.construct_event()` with the webhook secret.

9. **Graceful error tracking** (`app/core/error_tracking.py`): Sentry integration with `send_default_pii=False`, event filtering for noise reduction, and health-check transaction filtering. Optional dependency with graceful fallback.

10. **Security Guardian module** (`app/modules/security_guardian/service.py`): Enterprise-grade PII detection (Presidio + regex fallback), prompt injection detection (NeMo + regex), content safety checks, and comprehensive audit logging.

11. **Database connection hardening** (`app/database.py`): Connection pooling with `pool_pre_ping`, statement timeout (30s), pool recycling, and connection readiness checks with exponential backoff.

12. **Weak SECRET_KEY detection** (`app/core/lifecycle.py`): Startup check detects the default weak SECRET_KEY and logs a critical warning.

13. **`.env` file properly gitignored**: Both root `.gitignore` and `mvp/backend/.gitignore` exclude `.env` files. The `.env` file is NOT tracked by git.

14. **User ownership checks**: All module services (sandbox, API keys, billing) verify `user_id` ownership before allowing access to resources.

---

## Prioritized Remediation Roadmap

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| Week 1 | CRIT-01: Rotate all API keys, add secrets manager | Low | Critical |
| Week 1 | CRIT-02: Move code sandbox to Docker containers | High | Critical |
| Week 1 | HIGH-01: Separate metrics token from SECRET_KEY | Low | High |
| Week 2 | CRIT-03: Implement token blacklist in Redis | Medium | Critical |
| Week 2 | HIGH-03: Configure trusted proxy IPs for X-Forwarded-For | Low | High |
| Week 2 | HIGH-04: Disable OpenAPI docs in production | Low | High |
| Week 2 | HIGH-05: Add auth to `/api/modules` endpoint | Low | High |
| Week 3 | MED-01: Default DEBUG=False, ENVIRONMENT=production | Low | Medium |
| Week 3 | MED-02: Implement account lockout | Medium | Medium |
| Week 3 | MED-03: Implement refresh token invalidation on rotation | Medium | Medium |
| Week 3 | HIGH-02: Enforce API key daily rate limits | Medium | High |
| Week 4 | MED-04: Rate-limit webhook endpoint | Low | Medium |
| Week 4 | MED-06: Environment-aware seed script | Low | Medium |
| Backlog | LOW-01 through LOW-04 | Low | Low |

---

*End of report. This audit covers the files listed in scope. A comprehensive security review should also include penetration testing, dependency vulnerability scanning (e.g., `pip-audit`, `safety`), and infrastructure-level security assessment.*
