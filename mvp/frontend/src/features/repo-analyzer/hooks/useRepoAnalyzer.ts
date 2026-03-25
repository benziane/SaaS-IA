'use client';

import { useQuery } from '@tanstack/react-query';

import { listAnalyses, getAnalysis, getStatus } from '../api';
import type { PaginatedAnalyses, RepoAnalysis, RepoAnalyzerStatus } from '../types';
import { AnalysisStatus } from '../types';

/**
 * List repo analyses with pagination.
 * Auto-polls every 3s when any analysis is running.
 */
export function useRepoAnalyses(skip = 0, limit = 20) {
  return useQuery<PaginatedAnalyses>({
    queryKey: ['repo-analyzer-analyses', skip, limit],
    queryFn: () => listAnalyses(skip, limit),
    staleTime: 5_000,
    refetchInterval: (query) => {
      const hasRunning = query.state.data?.items.some(
        (a) => a.status === AnalysisStatus.PENDING || a.status === AnalysisStatus.RUNNING
      );
      return hasRunning ? 3_000 : false;
    },
  });
}

/**
 * Get a single repo analysis by ID.
 * Auto-polls every 2s while running.
 */
export function useRepoAnalysis(id: string) {
  return useQuery<RepoAnalysis>({
    queryKey: ['repo-analyzer-analysis', id],
    queryFn: () => getAnalysis(id),
    enabled: !!id,
    staleTime: 5_000,
    refetchInterval: (query) => {
      const isActive =
        query.state.data?.status === AnalysisStatus.PENDING ||
        query.state.data?.status === AnalysisStatus.RUNNING;
      return isActive ? 2_000 : false;
    },
  });
}

/**
 * Check git installation status.
 */
export function useRepoAnalyzerStatus() {
  return useQuery<RepoAnalyzerStatus>({
    queryKey: ['repo-analyzer-status'],
    queryFn: getStatus,
    staleTime: 60_000,
  });
}
