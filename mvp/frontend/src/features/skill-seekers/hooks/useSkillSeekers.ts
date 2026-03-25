'use client';

import { useQuery } from '@tanstack/react-query';

import { listJobs, getJob, getStatus, getStats } from '../api';
import type { PaginatedJobs, ScrapeJob, ScrapeJobStats, SkillSeekersStatus } from '../types';
import { ScrapeJobStatus } from '../types';

/**
 * List scrape jobs with pagination.
 * Auto-polls every 2s when any job is running.
 */
export function useSkillSeekersJobs(skip = 0, limit = 20) {
  return useQuery<PaginatedJobs>({
    queryKey: ['skill-seekers-jobs', skip, limit],
    queryFn: () => listJobs(skip, limit),
    staleTime: 5_000,
    refetchInterval: (query) => {
      const hasRunning = query.state.data?.items.some(
        (j) => j.status === ScrapeJobStatus.PENDING || j.status === ScrapeJobStatus.RUNNING
      );
      return hasRunning ? 2_000 : false;
    },
  });
}

/**
 * Get a single scrape job by ID.
 * Auto-polls every 2s while the job is running.
 */
export function useSkillSeekersJob(id: string) {
  return useQuery<ScrapeJob>({
    queryKey: ['skill-seekers-job', id],
    queryFn: () => getJob(id),
    enabled: !!id,
    staleTime: 5_000,
    refetchInterval: (query) => {
      const isActive =
        query.state.data?.status === ScrapeJobStatus.PENDING ||
        query.state.data?.status === ScrapeJobStatus.RUNNING;
      return isActive ? 2_000 : false;
    },
  });
}

/**
 * Check CLI installation status.
 */
export function useSkillSeekersStatus() {
  return useQuery<SkillSeekersStatus>({
    queryKey: ['skill-seekers-status'],
    queryFn: getStatus,
    staleTime: 60_000,
  });
}

/**
 * Get scrape job statistics for the current user.
 */
export function useSkillSeekersStats() {
  return useQuery<ScrapeJobStats>({
    queryKey: ['skill-seekers-stats'],
    queryFn: getStats,
    staleTime: 30_000,
  });
}
