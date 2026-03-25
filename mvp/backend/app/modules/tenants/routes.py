"""
Tenant API routes - Multi-tenant management with white-label support.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import get_current_user, require_role
from app.core.multi_tenant import TenantContext
from app.database import get_session
from app.models.user import Role, User
from app.modules.tenants.schemas import (
    BrandingUpdate,
    TenantCreate,
    TenantListResponse,
    TenantPublicConfig,
    TenantRead,
    TenantUpdate,
)
from app.modules.tenants.service import TenantService
from app.rate_limit import limiter

router = APIRouter()


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_tenant(
    request: Request,
    body: TenantCreate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new tenant organization.

    Admin only. Creates a new isolated tenant with its own slug,
    plan, and configuration.

    Rate limit: 10 requests/minute
    """
    try:
        tenant = await TenantService.create_tenant(
            name=body.name,
            slug=body.slug,
            plan=body.plan,
            config=body.config,
            session=session,
            max_users=body.max_users,
            max_storage_mb=body.max_storage_mb,
        )
        return TenantRead(**TenantService.tenant_to_read_dict(tenant))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("", response_model=TenantListResponse)
@limiter.limit("30/minute")
async def list_tenants(
    request: Request,
    current_user: User = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """
    List all tenants.

    Admin only. Returns all tenant organizations.

    Rate limit: 30 requests/minute
    """
    tenants = await TenantService.list_tenants(session)
    tenant_reads = [
        TenantRead(**TenantService.tenant_to_read_dict(t)) for t in tenants
    ]
    return TenantListResponse(count=len(tenant_reads), tenants=tenant_reads)


@router.get("/current", response_model=TenantRead)
@limiter.limit("30/minute")
async def get_current_tenant(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get the current tenant from JWT context.

    Returns the tenant associated with the authenticated user's JWT token.

    Rate limit: 30 requests/minute
    """
    tenant_id_str = TenantContext.get()
    if tenant_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tenant context. User may not be assigned to a tenant.",
        )

    try:
        tenant_uuid = UUID(tenant_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant_id format in context.",
        )

    tenant = await TenantService.get_tenant(tenant_uuid, session)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    return TenantRead(**TenantService.tenant_to_read_dict(tenant))


@router.get("/by-slug/{slug}/config", response_model=TenantPublicConfig)
@limiter.limit("60/minute")
async def get_tenant_public_config(
    request: Request,
    slug: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Get public tenant configuration for white-label.

    No authentication required. Returns only public branding info
    for rendering custom-branded login pages and UIs.

    Rate limit: 60 requests/minute
    """
    tenant = await TenantService.get_tenant_by_slug(slug, session)
    if tenant is None or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    read_dict = TenantService.tenant_to_read_dict(tenant)
    return TenantPublicConfig(
        name=read_dict["name"],
        slug=read_dict["slug"],
        plan=read_dict["plan"],
        branding=read_dict["branding"],
    )


@router.get("/{tenant_id}", response_model=TenantRead)
@limiter.limit("30/minute")
async def get_tenant(
    request: Request,
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a specific tenant by ID.

    Authenticated users can view their own tenant. Admins can view any tenant.

    Rate limit: 30 requests/minute
    """
    tenant = await TenantService.get_tenant(tenant_id, session)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    # Non-admin users can only view their own tenant
    if current_user.role != Role.ADMIN:
        current_tid = TenantContext.get()
        if current_tid is None or str(tenant_id) != current_tid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own tenant.",
            )

    return TenantRead(**TenantService.tenant_to_read_dict(tenant))


@router.put("/{tenant_id}", response_model=TenantRead)
@limiter.limit("10/minute")
async def update_tenant(
    request: Request,
    tenant_id: UUID,
    body: TenantUpdate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """
    Update a tenant.

    Admin only. Updates tenant name, plan, limits, and configuration.

    Rate limit: 10 requests/minute
    """
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update.",
        )

    tenant = await TenantService.update_tenant(tenant_id, update_data, session)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    return TenantRead(**TenantService.tenant_to_read_dict(tenant))


@router.put("/{tenant_id}/branding", response_model=TenantRead)
@limiter.limit("10/minute")
async def update_tenant_branding(
    request: Request,
    tenant_id: UUID,
    body: BrandingUpdate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """
    Update tenant white-label branding.

    Admin only. Updates logo, colors, favicon, and custom domain.

    Rate limit: 10 requests/minute
    """
    tenant = await TenantService.update_branding(
        tenant_id=tenant_id,
        logo_url=body.logo_url,
        primary_color=body.primary_color,
        favicon=body.favicon,
        custom_domain=body.custom_domain,
        session=session,
    )
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    return TenantRead(**TenantService.tenant_to_read_dict(tenant))
