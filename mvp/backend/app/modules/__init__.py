"""
Module Registry - Auto-discovers and registers API modules from manifest files.

Each module is a subdirectory under app/modules/ containing:
  - manifest.json  -- declares name, version, prefix, tags, enabled flag, etc.
  - routes.py      -- exposes a FastAPI ``router`` (APIRouter instance).

Modules can be disabled at runtime via the DISABLED_MODULES environment variable
(comma-separated list of module names).
"""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from typing import Any

import structlog
from fastapi import FastAPI

logger = structlog.get_logger()

# Manifest JSON schema -- required keys and their expected types.
_MANIFEST_SCHEMA: dict[str, type] = {
    "name": str,
    "version": str,
    "description": str,
    "prefix": str,
    "tags": list,
    "enabled": bool,
    "dependencies": list,
}


def _validate_manifest(manifest: dict[str, Any], manifest_path: str) -> list[str]:
    """Validate a manifest dict against the expected schema.

    Returns a list of human-readable error strings.  An empty list means the
    manifest is valid.
    """
    errors: list[str] = []
    for key, expected_type in _MANIFEST_SCHEMA.items():
        if key not in manifest:
            errors.append(f"Missing required field '{key}' in {manifest_path}")
        elif not isinstance(manifest[key], expected_type):
            errors.append(
                f"Field '{key}' in {manifest_path} must be {expected_type.__name__}, "
                f"got {type(manifest[key]).__name__}"
            )
    return errors


class ModuleRegistry:
    """Auto-discovers and registers API modules from manifest files."""

    _registered: list[dict[str, Any]] = []

    @classmethod
    def discover_modules(cls, app: FastAPI) -> list[dict[str, Any]]:
        """Scan the modules/ directory for manifest.json files, load enabled
        modules, and include their routers in the FastAPI application.

        Returns a list of dicts describing every successfully registered module.
        """
        cls._registered = []

        modules_dir = Path(__file__).resolve().parent
        disabled_raw = os.environ.get("DISABLED_MODULES", "")
        disabled_modules: set[str] = {
            name.strip().lower()
            for name in disabled_raw.split(",")
            if name.strip()
        }

        for entry in sorted(modules_dir.iterdir()):
            if not entry.is_dir():
                continue

            manifest_path = entry / "manifest.json"
            if not manifest_path.exists():
                continue

            module_dir_name = entry.name

            # ----------------------------------------------------------
            # 1. Load and validate manifest
            # ----------------------------------------------------------
            try:
                with open(manifest_path, "r", encoding="utf-8") as fh:
                    manifest: dict[str, Any] = json.load(fh)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(
                    "module_manifest_read_error",
                    module=module_dir_name,
                    error=str(exc),
                )
                continue

            validation_errors = _validate_manifest(manifest, str(manifest_path))
            if validation_errors:
                for err in validation_errors:
                    logger.warning("module_manifest_invalid", detail=err)
                continue

            module_name: str = manifest["name"]

            # ----------------------------------------------------------
            # 2. Check enabled / disabled status
            # ----------------------------------------------------------
            if not manifest.get("enabled", True):
                logger.info("module_disabled_by_manifest", module=module_name)
                continue

            if module_name.lower() in disabled_modules:
                logger.info(
                    "module_disabled_by_env",
                    module=module_name,
                    env_var="DISABLED_MODULES",
                )
                continue

            # ----------------------------------------------------------
            # 3. Dynamically import routes.py and retrieve the router
            # ----------------------------------------------------------
            routes_module_path = f"app.modules.{module_dir_name}.routes"
            try:
                routes_module = importlib.import_module(routes_module_path)
            except Exception as exc:
                logger.warning(
                    "module_import_error",
                    module=module_name,
                    import_path=routes_module_path,
                    error=str(exc),
                )
                continue

            router = getattr(routes_module, "router", None)
            if router is None:
                logger.warning(
                    "module_missing_router",
                    module=module_name,
                    detail=f"{routes_module_path} does not expose a 'router' attribute",
                )
                continue

            # ----------------------------------------------------------
            # 4. Include the router in the FastAPI app
            # ----------------------------------------------------------
            prefix: str = manifest["prefix"]
            tags: list[str] = manifest["tags"]

            try:
                app.include_router(router, prefix=prefix, tags=tags)
            except Exception as exc:
                logger.warning(
                    "module_router_include_error",
                    module=module_name,
                    error=str(exc),
                )
                continue

            info: dict[str, Any] = {
                "name": module_name,
                "version": manifest["version"],
                "description": manifest["description"],
                "prefix": prefix,
                "tags": tags,
                "dependencies": manifest.get("dependencies", []),
            }
            cls._registered.append(info)

            logger.info(
                "module_registered",
                module=module_name,
                version=manifest["version"],
                prefix=prefix,
            )

        return cls._registered

    @classmethod
    def get_registered_modules(cls) -> list[dict[str, Any]]:
        """Return info about all currently registered modules."""
        return list(cls._registered)
