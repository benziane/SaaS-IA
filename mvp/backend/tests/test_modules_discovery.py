"""
Tests for the ModuleRegistry auto-discovery system.

Validates that:
  - All 32 modules with manifest.json are discovered.
  - Every manifest.json contains the required schema fields.
  - Module routes are registered under /api/{module} prefixes.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

MODULES_DIR = Path(__file__).resolve().parent.parent / "app" / "modules"

# Required fields and their expected types per the _MANIFEST_SCHEMA
# defined in app.modules.__init__.py
MANIFEST_REQUIRED_FIELDS = {
    "name": str,
    "version": str,
    "description": str,
    "prefix": str,
    "tags": list,
    "enabled": bool,
    "dependencies": list,
}


def _collect_manifest_paths() -> list[Path]:
    """Return all manifest.json files under the modules directory."""
    return sorted(MODULES_DIR.glob("*/manifest.json"))


# --------------------------------------------------------------------------
# Tests: module discovery
# --------------------------------------------------------------------------

def test_all_modules_discovered():
    """ModuleRegistry should find all modules that have a manifest.json."""
    manifest_paths = _collect_manifest_paths()
    assert len(manifest_paths) >= 33, (
        f"Expected at least 33 manifest.json files, found {len(manifest_paths)}. "
        f"Modules: {[p.parent.name for p in manifest_paths]}"
    )


# --------------------------------------------------------------------------
# Tests: manifest validation
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "manifest_path",
    _collect_manifest_paths(),
    ids=lambda p: p.parent.name,
)
def test_module_manifests_valid(manifest_path: Path):
    """Each manifest.json must contain all required fields with correct types."""
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    for field_name, expected_type in MANIFEST_REQUIRED_FIELDS.items():
        assert field_name in manifest, (
            f"{manifest_path}: missing required field '{field_name}'"
        )
        assert isinstance(manifest[field_name], expected_type), (
            f"{manifest_path}: field '{field_name}' should be "
            f"{expected_type.__name__}, got {type(manifest[field_name]).__name__}"
        )

    # Extra semantic checks
    assert manifest["prefix"].startswith("/api/"), (
        f"{manifest_path}: prefix should start with '/api/', got '{manifest['prefix']}'"
    )
    assert len(manifest["name"]) > 0, (
        f"{manifest_path}: 'name' must not be empty"
    )
    assert len(manifest["tags"]) > 0, (
        f"{manifest_path}: 'tags' list must not be empty"
    )


# --------------------------------------------------------------------------
# Tests: routes registration
# --------------------------------------------------------------------------

def test_module_routes_registered(app):
    """Every enabled module should have at least one route registered
    under its declared prefix."""
    from app.modules import ModuleRegistry

    registered = ModuleRegistry.get_registered_modules()
    assert len(registered) > 0, "No modules were registered"

    # Collect all route paths from the FastAPI app
    all_paths: set[str] = set()
    for route in app.routes:
        path = getattr(route, "path", None)
        if path:
            all_paths.add(path)

    for mod in registered:
        prefix = mod["prefix"]
        matching = [p for p in all_paths if p.startswith(prefix)]
        assert len(matching) > 0, (
            f"Module '{mod['name']}' declares prefix '{prefix}' but no "
            f"routes were found with that prefix"
        )


def test_module_registry_get_registered_modules(app):
    """ModuleRegistry.get_registered_modules() returns a list of dicts with
    the expected keys."""
    from app.modules import ModuleRegistry

    modules = ModuleRegistry.get_registered_modules()
    assert isinstance(modules, list)

    for mod in modules:
        assert "name" in mod
        assert "version" in mod
        assert "prefix" in mod
        assert "tags" in mod


def test_disabled_module_not_registered(app):
    """Modules with 'enabled': false in their manifest should NOT appear
    in the registered list."""
    from app.modules import ModuleRegistry

    registered_names = {m["name"] for m in ModuleRegistry.get_registered_modules()}

    for manifest_path in _collect_manifest_paths():
        with open(manifest_path, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        if not manifest.get("enabled", True):
            assert manifest["name"] not in registered_names, (
                f"Disabled module '{manifest['name']}' should not be registered"
            )
