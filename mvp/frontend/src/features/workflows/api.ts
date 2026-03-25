/**
 * AI Workflows API
 */

import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type {
  Workflow,
  WorkflowCreateRequest,
  WorkflowRun,
  WorkflowTemplate,
  WorkflowUpdateRequest,
} from './types';

const ENDPOINTS = {
  LIST: '/api/workflows',
  CREATE: '/api/workflows',
  TEMPLATES: '/api/workflows/templates',
  FROM_TEMPLATE: (id: string) => `/api/workflows/from-template/${id}`,
  GET: (id: string) => `/api/workflows/${id}`,
  UPDATE: (id: string) => `/api/workflows/${id}`,
  DELETE: (id: string) => `/api/workflows/${id}`,
  RUN: (id: string) => `/api/workflows/${id}/run`,
  RUNS: (id: string) => `/api/workflows/${id}/runs`,
} as const;

export async function listWorkflows(): Promise<Workflow[]> {
  const response: AxiosResponse<Workflow[]> = await apiClient.get(ENDPOINTS.LIST);
  return response.data;
}

export async function createWorkflow(data: WorkflowCreateRequest): Promise<Workflow> {
  const response: AxiosResponse<Workflow> = await apiClient.post(ENDPOINTS.CREATE, data);
  return response.data;
}

export async function getWorkflow(id: string): Promise<Workflow> {
  const response: AxiosResponse<Workflow> = await apiClient.get(ENDPOINTS.GET(id));
  return response.data;
}

export async function updateWorkflow(id: string, data: WorkflowUpdateRequest): Promise<Workflow> {
  const response: AxiosResponse<Workflow> = await apiClient.put(ENDPOINTS.UPDATE(id), data);
  return response.data;
}

export async function deleteWorkflow(id: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.DELETE(id));
}

export async function triggerWorkflow(id: string, inputData?: Record<string, unknown>): Promise<WorkflowRun> {
  const response: AxiosResponse<WorkflowRun> = await apiClient.post(ENDPOINTS.RUN(id), { input_data: inputData || {} });
  return response.data;
}

export async function listRuns(workflowId: string): Promise<WorkflowRun[]> {
  const response: AxiosResponse<WorkflowRun[]> = await apiClient.get(ENDPOINTS.RUNS(workflowId));
  return response.data;
}

export async function listTemplates(category?: string): Promise<WorkflowTemplate[]> {
  const params = category ? { category } : {};
  const response: AxiosResponse<WorkflowTemplate[]> = await apiClient.get(ENDPOINTS.TEMPLATES, { params });
  return response.data;
}

export async function createFromTemplate(templateId: string, name?: string): Promise<Workflow> {
  const params = name ? { name } : {};
  const response: AxiosResponse<Workflow> = await apiClient.post(ENDPOINTS.FROM_TEMPLATE(templateId), null, { params });
  return response.data;
}
