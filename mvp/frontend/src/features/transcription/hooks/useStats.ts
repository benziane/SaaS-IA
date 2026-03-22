/**
 * useStats Hook - Grade S++
 * React Query hook for fetching transcription statistics
 */

import { useQuery, type UseQueryResult } from '@tanstack/react-query';

import { QUERY_STALE_TIME, queryKeys } from '@/lib/queryClient';

import { transcriptionApi } from '../api';
import type { TranscriptionStats } from '../types';

/* ========================================================================
   QUERY KEY
   ======================================================================== */

const statsQueryKey = [...queryKeys.transcriptions.all, 'stats'] as const;

/* ========================================================================
   HOOK
   ======================================================================== */

/**
 * Fetch transcription statistics for the current user.
 *
 * - Stale after 30 seconds (CRITICAL)
 * - Refetches every 30 seconds for near-real-time dashboard updates
 */
export function useStats(): UseQueryResult<TranscriptionStats, Error> {
  return useQuery({
    queryKey: statsQueryKey,
    queryFn: () => transcriptionApi.getStats(),
    staleTime: QUERY_STALE_TIME.CRITICAL,
    refetchInterval: 30_000,
  });
}

export default useStats;
