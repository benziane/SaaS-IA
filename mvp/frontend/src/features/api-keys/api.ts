/**
 * API Keys API
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type { APIKey, APIKeyCreated, APIKeyCreateRequest } from './types';

const KEYS_ENDPOINTS = {
  LIST: '/api/keys',
  CREATE: '/api/keys',
  DELETE: (id: string) => `/api/keys/${id}`,
} as const;

export async function listAPIKeys(): Promise<APIKey[]> {
  const response: AxiosResponse<APIKey[]> = await apiClient.get(KEYS_ENDPOINTS.LIST);
  return response.data;
}

export async function createAPIKey(data: APIKeyCreateRequest): Promise<APIKeyCreated> {
  const response: AxiosResponse<APIKeyCreated> = await apiClient.post(KEYS_ENDPOINTS.CREATE, data);
  return response.data;
}

export async function revokeAPIKey(id: string): Promise<void> {
  await apiClient.delete(KEYS_ENDPOINTS.DELETE(id));
}

export const apiKeysApi = { listAPIKeys, createAPIKey, revokeAPIKey } as const;
export default apiKeysApi;
