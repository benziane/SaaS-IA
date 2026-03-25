/**
 * AI Workflows hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createFromTemplate,
  createWorkflow,
  deleteWorkflow,
  listRuns,
  listTemplates,
  listWorkflows,
  triggerWorkflow,
  updateWorkflow,
} from '../api';
import type {
  Workflow,
  WorkflowCreateRequest,
  WorkflowRun,
  WorkflowTemplate,
  WorkflowUpdateRequest,
} from '../types';

export function useWorkflows() {
  return useQuery<Workflow[]>({
    queryKey: ['workflows'],
    queryFn: listWorkflows,
  });
}

export function useCreateWorkflow() {
  const queryClient = useQueryClient();
  return useMutation<Workflow, Error, WorkflowCreateRequest>({
    mutationFn: createWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}

export function useUpdateWorkflow() {
  const queryClient = useQueryClient();
  return useMutation<Workflow, Error, { id: string; data: WorkflowUpdateRequest }>({
    mutationFn: ({ id, data }) => updateWorkflow(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}

export function useDeleteWorkflow() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}

export function useTriggerWorkflow() {
  const queryClient = useQueryClient();
  return useMutation<WorkflowRun, Error, { id: string; inputData?: Record<string, unknown> }>({
    mutationFn: ({ id, inputData }) => triggerWorkflow(id, inputData),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['workflow-runs', variables.id] });
    },
  });
}

export function useWorkflowRuns(workflowId: string | null) {
  return useQuery<WorkflowRun[]>({
    queryKey: ['workflow-runs', workflowId],
    queryFn: () => listRuns(workflowId!),
    enabled: !!workflowId,
  });
}

export function useTemplates(category?: string) {
  return useQuery<WorkflowTemplate[]>({
    queryKey: ['workflow-templates', category],
    queryFn: () => listTemplates(category),
  });
}

export function useCreateFromTemplate() {
  const queryClient = useQueryClient();
  return useMutation<Workflow, Error, { templateId: string; name?: string }>({
    mutationFn: ({ templateId, name }) => createFromTemplate(templateId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
}
