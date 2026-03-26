/**
 * Secrets API
 * API calls for secret rotation tracking
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type {
  SecretAlert,
  SecretHealth,
  SecretRegisterRequest,
  SecretRegistration,
  SecretRotateRequest,
} from './types';

const ENDPOINTS = {
  LIST: '/api/secrets',
  ALERTS: '/api/secrets/alerts',
  HEALTH: '/api/secrets/health',
  REGISTER: '/api/secrets/register',
} as const;

export async function getSecrets(): Promise<SecretRegistration[]> {
  const response: AxiosResponse<SecretRegistration[]> = await apiClient.get(
    ENDPOINTS.LIST
  );
  return response.data;
}

export async function getAlerts(): Promise<SecretAlert[]> {
  const response: AxiosResponse<SecretAlert[]> = await apiClient.get(
    ENDPOINTS.ALERTS
  );
  return response.data;
}

export async function getHealth(): Promise<SecretHealth> {
  const response: AxiosResponse<SecretHealth> = await apiClient.get(
    ENDPOINTS.HEALTH
  );
  return response.data;
}

export async function registerSecret(
  data: SecretRegisterRequest
): Promise<{ message: string }> {
  const response: AxiosResponse<{ message: string }> = await apiClient.post(
    ENDPOINTS.REGISTER,
    data
  );
  return response.data;
}

export async function startRotation(
  name: string,
  data?: SecretRotateRequest
): Promise<{ message: string }> {
  const response: AxiosResponse<{ message: string }> = await apiClient.post(
    `${ENDPOINTS.LIST}/${encodeURIComponent(name)}/rotate`,
    data ?? {}
  );
  return response.data;
}

export async function completeRotation(
  name: string
): Promise<{ message: string }> {
  const response: AxiosResponse<{ message: string }> = await apiClient.post(
    `${ENDPOINTS.LIST}/${encodeURIComponent(name)}/complete`
  );
  return response.data;
}

export async function markCompromised(
  name: string
): Promise<{ message: string }> {
  const response: AxiosResponse<{ message: string }> = await apiClient.post(
    `${ENDPOINTS.LIST}/${encodeURIComponent(name)}/compromised`
  );
  return response.data;
}

export const secretsApi = {
  getSecrets,
  getAlerts,
  getHealth,
  registerSecret,
  startRotation,
  completeRotation,
  markCompromised,
} as const;

export default secretsApi;
