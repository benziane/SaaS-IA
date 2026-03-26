"""
Feature Flags management routes (admin-only).
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import get_current_user
from app.models.user import User
from app.modules.feature_flags.schemas import (
    FeatureFlagList,
    FeatureFlagRead,
    FeatureFlagUpdate,
    FeatureFlagUserResolved,
    KillSwitchResponse,
)
from app.modules.feature_flags.service import FeatureFlagModuleService
from app.rate_limit import limiter

router = APIRouter()


@router.get("/", response_model=FeatureFlagList)
@limiter.limit("30/minute")
async def list_flags(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    List all feature flags with current values, defaults, and overrides.

    Rate limit: 30 requests/minute
    """
    result = await FeatureFlagModuleService.list_all()
    return result


@router.get("/user/{user_id}", response_model=FeatureFlagUserResolved)
@limiter.limit("20/minute")
async def get_user_flags(
    request: Request,
    user_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get all resolved flag values for a specific user.

    Useful for debugging percentage rollouts and user whitelists.

    Rate limit: 20 requests/minute
    """
    flags = await FeatureFlagModuleService.get_user_flags(user_id)
    return FeatureFlagUserResolved(user_id=user_id, flags=flags)


@router.post("/kill/{module_name}", response_model=KillSwitchResponse)
@limiter.limit("10/minute")
async def kill_module(
    request: Request,
    module_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    Quick kill switch: immediately disable a module.

    Sets {module_name}_enabled = false. Takes effect within seconds.

    Rate limit: 10 requests/minute
    """
    result = await FeatureFlagModuleService.kill_module(module_name)
    return KillSwitchResponse(**result)


@router.post("/restore/{module_name}", response_model=KillSwitchResponse)
@limiter.limit("10/minute")
async def restore_module(
    request: Request,
    module_name: str,
    current_user: User = Depends(get_current_user),
):
    """
    Restore a killed module by removing the override (reverts to default).

    Rate limit: 10 requests/minute
    """
    result = await FeatureFlagModuleService.restore_module(module_name)
    return KillSwitchResponse(**result)


@router.get("/{name}", response_model=FeatureFlagRead)
@limiter.limit("30/minute")
async def get_flag(
    request: Request,
    name: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get a single feature flag's details.

    Rate limit: 30 requests/minute
    """
    flag = await FeatureFlagModuleService.get_flag(name)
    if flag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{name}' not found",
        )
    return FeatureFlagRead(**flag)


@router.put("/{name}", response_model=FeatureFlagRead)
@limiter.limit("10/minute")
async def set_flag(
    request: Request,
    name: str,
    body: FeatureFlagUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Set a feature flag value.

    Supported values:
    - "true" / "false": boolean toggle
    - "30%": percentage rollout (30% of users)
    - "users:uuid1,uuid2": user whitelist

    Rate limit: 10 requests/minute
    """
    await FeatureFlagModuleService.set_flag(name, body.value)
    flag = await FeatureFlagModuleService.get_flag(name)
    if flag is None:
        return FeatureFlagRead(name=name, default=None, override=body.value, effective=body.value)
    return FeatureFlagRead(**flag)


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_flag(
    request: Request,
    name: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a feature flag override (reverts to default value).

    Rate limit: 10 requests/minute
    """
    await FeatureFlagModuleService.delete_flag(name)
    return None
