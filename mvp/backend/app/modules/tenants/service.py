"""
Tenant service - Business logic for multi-tenant management.
"""

import json
from datetime import UTC, datetime
from typing import Any, Optional
from uuid import UUID

import structlog
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.tenant import Tenant

logger = structlog.get_logger()


class TenantService:
    """Tenant management: create, configure, white-label."""

    @staticmethod
    async def create_tenant(
        name: str,
        slug: str,
        plan: str,
        config: dict[str, Any],
        session: AsyncSession,
        max_users: int = 5,
        max_storage_mb: int = 1000,
    ) -> Tenant:
        """Create a new tenant organization.

        Raises ValueError if slug already exists.
        """
        # Check slug uniqueness
        existing = await TenantService.get_tenant_by_slug(slug, session)
        if existing is not None:
            raise ValueError(f"Tenant with slug '{slug}' already exists")

        tenant = Tenant(
            name=name,
            slug=slug,
            plan=plan,
            config_json=json.dumps(config),
            max_users=max_users,
            max_storage_mb=max_storage_mb,
        )

        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)

        logger.info(
            "tenant_created",
            tenant_id=str(tenant.id),
            slug=slug,
            plan=plan,
        )

        return tenant

    @staticmethod
    async def get_tenant(tenant_id: UUID, session: AsyncSession) -> Optional[Tenant]:
        """Get a tenant by ID."""
        return await session.get(Tenant, tenant_id)

    @staticmethod
    async def update_tenant(
        tenant_id: UUID,
        data: dict[str, Any],
        session: AsyncSession,
    ) -> Optional[Tenant]:
        """Update tenant fields.

        Accepts a dict of field names to new values. Only updates provided fields.
        Returns the updated tenant or None if not found.
        """
        tenant = await session.get(Tenant, tenant_id)
        if tenant is None:
            return None

        updatable_fields = {"name", "plan", "is_active", "max_users", "max_storage_mb"}

        for field_name, value in data.items():
            if field_name == "config" and isinstance(value, dict):
                # Merge config: load existing, update with new keys
                existing_config = json.loads(tenant.config_json or "{}")
                existing_config.update(value)
                tenant.config_json = json.dumps(existing_config)
            elif field_name in updatable_fields and value is not None:
                setattr(tenant, field_name, value)

        tenant.updated_at = datetime.now(UTC)
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)

        logger.info(
            "tenant_updated",
            tenant_id=str(tenant_id),
            updated_fields=list(data.keys()),
        )

        return tenant

    @staticmethod
    async def list_tenants(session: AsyncSession) -> list[Tenant]:
        """List all tenants (admin only)."""
        result = await session.execute(
            select(Tenant).order_by(Tenant.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_tenant_by_slug(slug: str, session: AsyncSession) -> Optional[Tenant]:
        """Get a tenant by its unique slug."""
        result = await session.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_branding(
        tenant_id: UUID,
        logo_url: Optional[str],
        primary_color: Optional[str],
        favicon: Optional[str],
        custom_domain: Optional[str],
        session: AsyncSession,
    ) -> Optional[Tenant]:
        """Update tenant white-label branding.

        Merges provided values into existing branding_json.
        Returns the updated tenant or None if not found.
        """
        tenant = await session.get(Tenant, tenant_id)
        if tenant is None:
            return None

        # Load existing branding and merge
        branding = json.loads(tenant.branding_json or "{}")

        if logo_url is not None:
            branding["logo_url"] = logo_url
        if primary_color is not None:
            branding["primary_color"] = primary_color
        if favicon is not None:
            branding["favicon"] = favicon
        if custom_domain is not None:
            branding["custom_domain"] = custom_domain

        tenant.branding_json = json.dumps(branding)
        tenant.updated_at = datetime.now(UTC)

        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)

        logger.info(
            "tenant_branding_updated",
            tenant_id=str(tenant_id),
            has_custom_domain=custom_domain is not None,
        )

        return tenant

    @staticmethod
    def tenant_to_read_dict(tenant: Tenant) -> dict[str, Any]:
        """Convert a Tenant model to a dict suitable for TenantRead schema.

        Parses config_json and branding_json into proper dicts.
        """
        config = {}
        branding = {}

        try:
            config = json.loads(tenant.config_json or "{}")
        except (json.JSONDecodeError, TypeError):
            pass

        try:
            branding = json.loads(tenant.branding_json or "{}")
        except (json.JSONDecodeError, TypeError):
            pass

        return {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "plan": tenant.plan,
            "is_active": tenant.is_active,
            "config": config,
            "branding": branding,
            "max_users": tenant.max_users,
            "max_storage_mb": tenant.max_storage_mb,
            "created_at": tenant.created_at,
            "updated_at": tenant.updated_at,
        }
