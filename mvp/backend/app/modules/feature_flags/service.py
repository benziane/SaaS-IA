"""
Feature Flags service - delegates to core FeatureFlagService.
"""

import structlog

from app.core.feature_flags import FeatureFlagService

logger = structlog.get_logger()


class FeatureFlagModuleService:
    """Thin wrapper around FeatureFlagService for the module routes."""

    @staticmethod
    async def list_all() -> dict:
        """Get all flags with defaults, overrides, and effective values."""
        flags = await FeatureFlagService.get_all_flags()
        return {"count": len(flags), "flags": flags}

    @staticmethod
    async def get_flag(name: str) -> dict | None:
        """Get a single flag's details."""
        all_flags = await FeatureFlagService.get_all_flags()
        return all_flags.get(name)

    @staticmethod
    async def set_flag(name: str, value: str) -> None:
        """Set a flag value."""
        # Normalize boolean strings
        lower = value.strip().lower()
        if lower in ("true", "false"):
            await FeatureFlagService.set_flag(name, lower == "true")
        else:
            await FeatureFlagService.set_flag(name, value.strip())

    @staticmethod
    async def delete_flag(name: str) -> None:
        """Delete a flag override (reverts to default)."""
        await FeatureFlagService.delete_flag(name)

    @staticmethod
    async def get_user_flags(user_id: str) -> dict[str, bool]:
        """Get resolved flags for a specific user."""
        return await FeatureFlagService.get_flags_for_user(user_id)

    @staticmethod
    async def kill_module(module_name: str) -> dict:
        """Quick kill switch: disable a module immediately."""
        flag_name = f"{module_name}_enabled"
        await FeatureFlagService.set_flag(flag_name, False)
        # Clear middleware cache to take effect immediately
        try:
            from app.middleware.feature_flag_middleware import FeatureFlagMiddleware
            FeatureFlagMiddleware.clear_cache()
        except ImportError:
            pass
        FeatureFlagService.clear_cache()
        logger.warning("module_killed", module=module_name, flag=flag_name)
        return {
            "module": module_name,
            "flag_name": flag_name,
            "action": "kill",
            "status": "disabled",
        }

    @staticmethod
    async def restore_module(module_name: str) -> dict:
        """Restore a killed module by deleting its override."""
        flag_name = f"{module_name}_enabled"
        await FeatureFlagService.delete_flag(flag_name)
        try:
            from app.middleware.feature_flag_middleware import FeatureFlagMiddleware
            FeatureFlagMiddleware.clear_cache()
        except ImportError:
            pass
        FeatureFlagService.clear_cache()
        logger.info("module_restored", module=module_name, flag=flag_name)
        return {
            "module": module_name,
            "flag_name": flag_name,
            "action": "restore",
            "status": "reverted_to_default",
        }
