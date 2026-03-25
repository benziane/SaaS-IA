'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { extractErrorMessage } from '@/lib/apiClient';

import { createJob, deleteJob } from '../api';
import type { ScrapeJob, ScrapeJobCreateRequest } from '../types';

/**
 * Create a new scrape job.
 */
export function useCreateScrapeJob() {
  const qc = useQueryClient();
  return useMutation<ScrapeJob, Error, ScrapeJobCreateRequest>({
    mutationFn: createJob,
    onSuccess: (created) => {
      void qc.invalidateQueries({ queryKey: ['skill-seekers-jobs'] });
      toast.success('Scrape job started', {
        description: `Processing ${created.repos.length} repo(s)`,
      });
    },
    onError: (error: Error) => {
      toast.error('Failed to create scrape job', {
        description: extractErrorMessage(error),
      });
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
      void qc.invalidateQueries({ queryKey: ['skill-seekers-jobs'] });
      toast.success('Scrape job deleted');
    },
    onError: (error: Error) => {
      toast.error('Failed to delete scrape job', {
        description: extractErrorMessage(error),
      });
    },
  });
}
