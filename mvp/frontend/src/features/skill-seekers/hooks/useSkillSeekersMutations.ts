'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';

import { createJob, deleteJob } from '../api';
import type { ScrapeJob, ScrapeJobCreateRequest } from '../types';

/**
 * Create a new scrape job.
 */
export function useCreateScrapeJob() {
  const qc = useQueryClient();
  return useMutation<ScrapeJob, Error, ScrapeJobCreateRequest>({
    mutationFn: createJob,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['skill-seekers-jobs'] });
    },
  });
}

/**
 * Delete a scrape job.
 */
export function useDeleteScrapeJob() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteJob,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['skill-seekers-jobs'] });
    },
  });
}
