/**
 * Transcription Hooks - Grade S++
 * React Query hooks for transcriptions
 */

import { useQuery, type UseQueryResult } from '@tanstack/react-query';

import { QUERY_STALE_TIME, queryKeys } from '@/lib/queryClient';

import { transcriptionApi } from '../api';
import type { Transcription, TranscriptionFilters, TranscriptionListResponse } from '../types';

/* ========================================================================
   USE TRANSCRIPTIONS
   ======================================================================== */

/**
 * List transcriptions with filters
 */
export function useTranscriptions(
  filters?: TranscriptionFilters
): UseQueryResult<TranscriptionListResponse, Error> {
  return useQuery({
    queryKey: queryKeys.transcriptions.list(filters),
    queryFn: () => transcriptionApi.listTranscriptions(filters),
    staleTime: QUERY_STALE_TIME.CRITICAL, // 30 seconds - frequent updates
    refetchInterval: 5000, // Poll every 5 seconds for real-time updates
  });
}

/* ========================================================================
   USE TRANSCRIPTION
   ======================================================================== */

/**
 * Get a single transcription by ID
 */
export function useTranscription(id: string): UseQueryResult<Transcription, Error> {
  return useQuery({
    queryKey: queryKeys.transcriptions.detail(id),
    queryFn: () => transcriptionApi.getTranscription(id),
    staleTime: QUERY_STALE_TIME.CRITICAL,
    refetchInterval: 3000, // Poll every 3 seconds for status updates
    enabled: !!id,
  });
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default {
  useTranscriptions,
  useTranscription,
};

