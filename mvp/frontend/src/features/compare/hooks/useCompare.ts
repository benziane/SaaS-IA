/**
 * Compare hooks
 * React Query hooks for comparison features
 */

'use client';

import { useMutation, useQuery } from '@tanstack/react-query';

import { getCompareStats, runComparison, voteComparison } from '../api';
import type { CompareRequest, CompareResponse, ProviderStats } from '../types';

export function useRunComparison() {
  return useMutation<CompareResponse, Error, CompareRequest>({
    mutationFn: runComparison,
  });
}

export function useVoteComparison() {
  return useMutation<void, Error, { comparisonId: string; providerName: string; qualityScore: number }>({
    mutationFn: ({ comparisonId, providerName, qualityScore }) =>
      voteComparison(comparisonId, providerName, qualityScore),
  });
}

export function useCompareStats() {
  return useQuery<ProviderStats[]>({
    queryKey: ['compare', 'stats'],
    queryFn: getCompareStats,
    staleTime: 60 * 1000,
  });
}
