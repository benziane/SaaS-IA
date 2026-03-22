/**
 * API Keys hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { createAPIKey, listAPIKeys, revokeAPIKey } from '../api';
import type { APIKey, APIKeyCreated, APIKeyCreateRequest } from '../types';

export function useAPIKeys() {
  return useQuery<APIKey[]>({
    queryKey: ['api-keys'],
    queryFn: listAPIKeys,
  });
}

export function useCreateAPIKey() {
  const qc = useQueryClient();
  return useMutation<APIKeyCreated, Error, APIKeyCreateRequest>({
    mutationFn: createAPIKey,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['api-keys'] }),
  });
}

export function useRevokeAPIKey() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: revokeAPIKey,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['api-keys'] }),
  });
}
