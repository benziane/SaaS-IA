/**
 * Pipeline hooks
 * React Query hooks for pipeline operations
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createPipeline,
  deletePipeline,
  executePipeline,
  listExecutions,
  listPipelines,
  updatePipeline,
} from '../api';
import type { Pipeline, PipelineCreateRequest, PipelineExecution, PipelineUpdateRequest } from '../types';

export function usePipelines() {
  return useQuery<Pipeline[]>({
    queryKey: ['pipelines'],
    queryFn: listPipelines,
  });
}

export function useCreatePipeline() {
  const queryClient = useQueryClient();
  return useMutation<Pipeline, Error, PipelineCreateRequest>({
    mutationFn: createPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
    },
  });
}

export function useUpdatePipeline() {
  const queryClient = useQueryClient();
  return useMutation<Pipeline, Error, { id: string; data: PipelineUpdateRequest }>({
    mutationFn: ({ id, data }) => updatePipeline(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
    },
  });
}

export function useDeletePipeline() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deletePipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
    },
  });
}

export function useExecutePipeline() {
  return useMutation<PipelineExecution, Error, string>({
    mutationFn: executePipeline,
  });
}

export function useExecutions(pipelineId: string) {
  return useQuery<PipelineExecution[]>({
    queryKey: ['pipelines', pipelineId, 'executions'],
    queryFn: () => listExecutions(pipelineId),
    enabled: !!pipelineId,
  });
}
