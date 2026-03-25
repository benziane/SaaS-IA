'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { extractErrorMessage } from '@/lib/apiClient';

import { createAnalysis, deleteAnalysis, compareRepos } from '../api';
import type { AnalysisCreateRequest, CompareRequest, CompareResult, RepoAnalysis } from '../types';

/**
 * Create a new repo analysis.
 */
export function useCreateAnalysis() {
  const qc = useQueryClient();
  return useMutation<RepoAnalysis, Error, AnalysisCreateRequest>({
    mutationFn: createAnalysis,
    onSuccess: (created) => {
      void qc.invalidateQueries({ queryKey: ['repo-analyzer-analyses'] });
      toast.success('Analysis started', {
        description: `Analyzing ${created.repo_name}`,
      });
    },
    onError: (error: Error) => {
      toast.error('Failed to create analysis', {
        description: extractErrorMessage(error),
      });
    },
  });
}

/**
 * Delete a repo analysis.
 */
export function useDeleteAnalysis() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteAnalysis,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['repo-analyzer-analyses'] });
      toast.success('Analysis deleted');
    },
    onError: (error: Error) => {
      toast.error('Failed to delete analysis', {
        description: extractErrorMessage(error),
      });
    },
  });
}

/**
 * Compare multiple repos.
 */
export function useCompareRepos() {
  return useMutation<CompareResult, Error, CompareRequest>({
    mutationFn: compareRepos,
    onSuccess: () => {
      toast.success('Comparison complete');
    },
    onError: (error: Error) => {
      toast.error('Failed to compare repos', {
        description: extractErrorMessage(error),
      });
    },
  });
}
