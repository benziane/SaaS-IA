/**
 * Tenant Types
 * Type definitions for multi-tenant management
 */

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan: 'free' | 'pro' | 'enterprise';
  is_active: boolean;
  config: Record<string, unknown>;
  branding: TenantBranding;
  max_users: number;
  max_storage_mb: number;
  created_at: string;
  updated_at: string;
}

export interface TenantBranding {
  logo_url?: string;
  primary_color?: string;
  favicon?: string;
  custom_domain?: string;
}

export interface TenantPublicConfig {
  name: string;
  slug: string;
  plan: string;
  branding: TenantBranding;
}

export interface TenantListResponse {
  count: number;
  tenants: Tenant[];
}

export interface TenantCreateRequest {
  name: string;
  slug: string;
  plan: 'free' | 'pro' | 'enterprise';
  config?: Record<string, unknown>;
  max_users?: number;
  max_storage_mb?: number;
}

export interface TenantUpdateRequest {
  name?: string;
  plan?: 'free' | 'pro' | 'enterprise';
  is_active?: boolean;
  config?: Record<string, unknown>;
  max_users?: number;
  max_storage_mb?: number;
}

export interface BrandingUpdateRequest {
  logo_url?: string;
  primary_color?: string;
  favicon?: string;
  custom_domain?: string;
}
