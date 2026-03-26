/**
 * Feature Flags API
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type {
  FeatureFlag,
  FeatureFlagList,
  FeatureFlagUpdate,
  FeatureFlagUserResolved,
  KillSwitchResponse,
} from './types';

const ENDPOINTS = {
  LIST: '/api/feature-flags',
  FLAG: (name: string) => `/api/feature-flags/${name}`,
  USER: (userId: string) => `/api/feature-flags/user/${userId}`,
  KILL: (module: string) => `/api/feature-flags/kill/${module}`,
  RESTORE: (module: string) => `/api/feature-flags/restore/${module}`,
} as const;

export async function listFeatureFlags(): Promise<FeatureFlagList> {
  const response: AxiosResponse<FeatureFlagList> = await apiClient.get(ENDPOINTS.LIST);
  return response.data;
}

export async function getFeatureFlag(name: string): Promise<FeatureFlag> {
  const response: AxiosResponse<FeatureFlag> = await apiClient.get(ENDPOINTS.FLAG(name));
  return response.data;
}

export async function setFeatureFlag(name: string, data: FeatureFlagUpdate): Promise<FeatureFlag> {
  const response: AxiosResponse<FeatureFlag> = await apiClient.put(ENDPOINTS.FLAG(name), data);
  return response.data;
}

export async function deleteFeatureFlag(name: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.FLAG(name));
}

export async function getUserFlags(userId: string): Promise<FeatureFlagUserResolved> {
  const response: AxiosResponse<FeatureFlagUserResolved> = await apiClient.get(ENDPOINTS.USER(userId));
  return response.data;
}

export async function killModule(module: string): Promise<KillSwitchResponse> {
  const response: AxiosResponse<KillSwitchResponse> = await apiClient.post(ENDPOINTS.KILL(module));
  return response.data;
}

export async function restoreModule(module: string): Promise<KillSwitchResponse> {
  const response: AxiosResponse<KillSwitchResponse> = await apiClient.post(ENDPOINTS.RESTORE(module));
  return response.data;
}

export const featureFlagsApi = {
  listFeatureFlags,
  getFeatureFlag,
  setFeatureFlag,
  deleteFeatureFlag,
  getUserFlags,
  killModule,
  restoreModule,
} as const;
export default featureFlagsApi;
