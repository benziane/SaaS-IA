/**
 * Tenants API
 * API calls for multi-tenant management
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type {
  BrandingUpdateRequest,
  Tenant,
  TenantCreateRequest,
  TenantListResponse,
  TenantPublicConfig,
  TenantUpdateRequest,
} from './types';

const TENANTS_ENDPOINTS = {
  BASE: '/api/tenants',
  CURRENT: '/api/tenants/current',
} as const;

export async function createTenant(data: TenantCreateRequest): Promise<Tenant> {
  const response: AxiosResponse<Tenant> = await apiClient.post(
    TENANTS_ENDPOINTS.BASE,
    data
  );
  return response.data;
}

export async function listTenants(): Promise<TenantListResponse> {
  const response: AxiosResponse<TenantListResponse> = await apiClient.get(
    TENANTS_ENDPOINTS.BASE
  );
  return response.data;
}

export async function getTenant(tenantId: string): Promise<Tenant> {
  const response: AxiosResponse<Tenant> = await apiClient.get(
    `${TENANTS_ENDPOINTS.BASE}/${tenantId}`
  );
  return response.data;
}

export async function updateTenant(
  tenantId: string,
  data: TenantUpdateRequest
): Promise<Tenant> {
  const response: AxiosResponse<Tenant> = await apiClient.put(
    `${TENANTS_ENDPOINTS.BASE}/${tenantId}`,
    data
  );
  return response.data;
}

export async function updateBranding(
  tenantId: string,
  data: BrandingUpdateRequest
): Promise<Tenant> {
  const response: AxiosResponse<Tenant> = await apiClient.put(
    `${TENANTS_ENDPOINTS.BASE}/${tenantId}/branding`,
    data
  );
  return response.data;
}

export async function getCurrentTenant(): Promise<Tenant> {
  const response: AxiosResponse<Tenant> = await apiClient.get(
    TENANTS_ENDPOINTS.CURRENT
  );
  return response.data;
}

export async function getTenantPublicConfig(
  slug: string
): Promise<TenantPublicConfig> {
  const response: AxiosResponse<TenantPublicConfig> = await apiClient.get(
    `${TENANTS_ENDPOINTS.BASE}/by-slug/${slug}/config`
  );
  return response.data;
}

export const tenantsApi = {
  createTenant,
  listTenants,
  getTenant,
  updateTenant,
  updateBranding,
  getCurrentTenant,
  getTenantPublicConfig,
} as const;

export default tenantsApi;
