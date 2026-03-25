/**
 * Tenants hooks
 * React Query hooks for multi-tenant management
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createTenant,
  getCurrentTenant,
  getTenant,
  getTenantPublicConfig,
  listTenants,
  updateBranding,
  updateTenant,
} from '../api';
import type {
  BrandingUpdateRequest,
  Tenant,
  TenantCreateRequest,
  TenantListResponse,
  TenantPublicConfig,
  TenantUpdateRequest,
} from '../types';

export function useTenants() {
  return useQuery<TenantListResponse>({
    queryKey: ['tenants'],
    queryFn: listTenants,
    staleTime: 30 * 1000,
  });
}

export function useTenant(tenantId: string | undefined) {
  return useQuery<Tenant>({
    queryKey: ['tenants', tenantId],
    queryFn: () => getTenant(tenantId!),
    enabled: !!tenantId,
    staleTime: 30 * 1000,
  });
}

export function useCurrentTenant() {
  return useQuery<Tenant>({
    queryKey: ['tenants', 'current'],
    queryFn: getCurrentTenant,
    staleTime: 60 * 1000,
  });
}

export function useTenantPublicConfig(slug: string | undefined) {
  return useQuery<TenantPublicConfig>({
    queryKey: ['tenants', 'public-config', slug],
    queryFn: () => getTenantPublicConfig(slug!),
    enabled: !!slug,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCreateTenant() {
  const queryClient = useQueryClient();

  return useMutation<Tenant, Error, TenantCreateRequest>({
    mutationFn: createTenant,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
    },
  });
}

export function useUpdateTenant() {
  const queryClient = useQueryClient();

  return useMutation<
    Tenant,
    Error,
    { tenantId: string; data: TenantUpdateRequest }
  >({
    mutationFn: ({ tenantId, data }) => updateTenant(tenantId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      queryClient.invalidateQueries({
        queryKey: ['tenants', variables.tenantId],
      });
    },
  });
}

export function useUpdateBranding() {
  const queryClient = useQueryClient();

  return useMutation<
    Tenant,
    Error,
    { tenantId: string; data: BrandingUpdateRequest }
  >({
    mutationFn: ({ tenantId, data }) => updateBranding(tenantId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
      queryClient.invalidateQueries({
        queryKey: ['tenants', variables.tenantId],
      });
    },
  });
}
