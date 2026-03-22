/**
 * Compare API
 * API calls for multi-model comparison
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type { CompareRequest, CompareResponse, ProviderStats } from './types';

const COMPARE_ENDPOINTS = {
  RUN: '/api/compare/run',
  VOTE: (id: string) => `/api/compare/${id}/vote`,
  STATS: '/api/compare/stats',
} as const;

export async function runComparison(data: CompareRequest): Promise<CompareResponse> {
  const response: AxiosResponse<CompareResponse> = await apiClient.post(
    COMPARE_ENDPOINTS.RUN,
    data
  );
  return response.data;
}

export async function voteComparison(
  comparisonId: string,
  providerName: string,
  qualityScore: number
): Promise<void> {
  await apiClient.post(COMPARE_ENDPOINTS.VOTE(comparisonId), {
    provider_name: providerName,
    quality_score: qualityScore,
  });
}

export async function getCompareStats(): Promise<ProviderStats[]> {
  const response: AxiosResponse<ProviderStats[]> = await apiClient.get(
    COMPARE_ENDPOINTS.STATS
  );
  return response.data;
}

export const compareApi = { runComparison, voteComparison, getCompareStats } as const;
export default compareApi;
