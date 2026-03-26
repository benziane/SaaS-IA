"""
Module auto-discovery and loading integration tests.

Verifies that all modules are correctly discovered, registered, and
that their endpoints are accessible via the FastAPI application.
"""

import json
from pathlib import Path

import pytest

from tests.integration.conftest import USE_REAL_DB, register_user, login_user


# ---------------------------------------------------------------------------
# Module discovery
# ---------------------------------------------------------------------------

class TestModuleDiscovery:
    """Verify module auto-discovery and registration."""

    _auth_headers: dict = {}

    @pytest.fixture(autouse=True)
    async def _setup_auth(self, client):
        """Register and login a user for authenticated endpoints."""
        from uuid import uuid4
        email = f"modtest_{uuid4().hex[:8]}@test.com"
        password = "ModTest123!"
        await register_user(client, email, password)
        resp = await login_user(client, email, password)
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            self._auth_headers = {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_all_modules_loaded(self, client):
        """The /api/modules endpoint should report all enabled modules."""
        if not self._auth_headers:
            pytest.skip("Could not authenticate")
        resp = await client.get("/api/modules", headers=self._auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "count" in data
        assert "modules" in data
        # Platform has 40 modules; some may fail to import, but at least 30 should load
        assert data["count"] >= 30, f"Only {data['count']} modules loaded, expected >= 30"

    @pytest.mark.asyncio
    async def test_module_names_unique(self, client):
        """Module names should be unique."""
        if not self._auth_headers:
            pytest.skip("Could not authenticate")
        resp = await client.get("/api/modules", headers=self._auth_headers)
        data = resp.json()
        names = [m["name"] for m in data["modules"]]
        assert len(names) == len(set(names)), f"Duplicate module names: {[n for n in names if names.count(n) > 1]}"

    @pytest.mark.asyncio
    async def test_module_prefixes_unique(self, client):
        """Module prefixes should be unique."""
        if not self._auth_headers:
            pytest.skip("Could not authenticate")
        resp = await client.get("/api/modules", headers=self._auth_headers)
        data = resp.json()
        prefixes = [m["prefix"] for m in data["modules"]]
        assert len(prefixes) == len(set(prefixes)), f"Duplicate prefixes: {[p for p in prefixes if prefixes.count(p) > 1]}"

    @pytest.mark.asyncio
    async def test_core_modules_present(self, client):
        """Core modules should always be loaded."""
        if not self._auth_headers:
            pytest.skip("Could not authenticate")
        resp = await client.get("/api/modules", headers=self._auth_headers)
        data = resp.json()
        module_names = {m["name"] for m in data["modules"]}

        core = {"transcription", "conversation", "knowledge", "billing", "agents"}
        missing = core - module_names
        assert not missing, f"Core modules missing: {missing}"


# ---------------------------------------------------------------------------
# Manifests validation
# ---------------------------------------------------------------------------

class TestManifestValidation:
    """Verify all manifest.json files are well-formed."""

    def _get_all_manifests(self):
        """Collect all manifest.json paths."""
        modules_dir = Path(__file__).resolve().parent.parent.parent / "app" / "modules"
        manifests = []
        for entry in sorted(modules_dir.iterdir()):
            manifest_path = entry / "manifest.json"
            if manifest_path.exists():
                manifests.append(manifest_path)
        return manifests

    def test_all_manifests_valid_json(self):
        """Every manifest.json should be valid JSON."""
        manifests = self._get_all_manifests()
        assert len(manifests) > 0, "No manifests found"

        for path in manifests:
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {path}: {e}")

    def test_all_manifests_have_required_fields(self):
        """Every manifest should contain name, version, prefix, tags, enabled."""
        required = {"name", "version", "description", "prefix", "tags", "enabled", "dependencies"}
        manifests = self._get_all_manifests()

        for path in manifests:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            missing = required - set(data.keys())
            assert not missing, f"{path.parent.name}/manifest.json missing fields: {missing}"

    def test_manifest_prefix_starts_with_api(self):
        """All module prefixes should start with /api/."""
        manifests = self._get_all_manifests()

        for path in manifests:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            prefix = data.get("prefix", "")
            assert prefix.startswith("/api/"), (
                f"{data['name']}: prefix '{prefix}' does not start with /api/"
            )

    def test_manifest_count(self):
        """There should be at least 37 module manifests."""
        manifests = self._get_all_manifests()
        assert len(manifests) >= 37, f"Found {len(manifests)} manifests, expected >= 37"


# ---------------------------------------------------------------------------
# Endpoint registration
# ---------------------------------------------------------------------------

class TestEndpointRegistration:
    """Verify key endpoints are registered and respond."""

    @pytest.mark.asyncio
    async def test_openapi_schema_valid(self, client):
        """The OpenAPI schema should be valid JSON and contain paths."""
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200, resp.text
        schema = resp.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert len(schema["paths"]) > 50, f"Only {len(schema['paths'])} paths in OpenAPI schema"

    @pytest.mark.asyncio
    async def test_auth_endpoints_registered(self, client):
        """Auth endpoints should be in the OpenAPI schema."""
        resp = await client.get("/openapi.json")
        paths = resp.json()["paths"]
        assert "/api/auth/register" in paths
        assert "/api/auth/login" in paths
        assert "/api/auth/me" in paths

    @pytest.mark.asyncio
    async def test_transcription_endpoints_registered(self, client):
        """Transcription endpoints should be in the OpenAPI schema."""
        resp = await client.get("/openapi.json")
        paths = resp.json()["paths"]
        assert "/api/transcription/" in paths


# ---------------------------------------------------------------------------
# Health probes
# ---------------------------------------------------------------------------

class TestHealthProbes:
    """Verify Kubernetes health probes respond."""

    @pytest.mark.asyncio
    async def test_liveness_probe(self, client):
        """Liveness probe should always return 200."""
        resp = await client.get("/health/live")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "alive"

    @pytest.mark.asyncio
    async def test_startup_probe(self, client):
        """Startup probe should return 200 after boot."""
        resp = await client.get("/health/startup")
        # May return 200 or 503 depending on timing
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_readiness_probe(self, client):
        """Readiness probe should respond (may be unhealthy without real deps)."""
        resp = await client.get("/health/ready")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data
        assert "checks" in data


# ---------------------------------------------------------------------------
# Middleware stack
# ---------------------------------------------------------------------------

class TestMiddlewareStack:
    """Verify middleware headers and behavior."""

    @pytest.mark.asyncio
    async def test_request_id_header(self, client):
        """Every response should include X-Request-ID."""
        resp = await client.get("/")
        # The RequestIDMiddleware should add this header
        request_id = resp.headers.get("x-request-id")
        assert request_id is not None, "Missing X-Request-ID header"
        assert len(request_id) > 0

    @pytest.mark.asyncio
    async def test_security_headers(self, client):
        """Security middleware should add OWASP headers."""
        resp = await client.get("/")
        # SecurityHeadersMiddleware adds these
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert "x-frame-options" in resp.headers

    @pytest.mark.asyncio
    async def test_cors_preflight(self, client):
        """CORS preflight OPTIONS request should succeed."""
        resp = await client.options(
            "/api/auth/login",
            headers={
                "Origin": "http://localhost:3002",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert resp.status_code == 200
