/**
 * Pipeline API
 * API calls for pipeline builder
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type {
  Pipeline,
  PipelineCreateRequest,
  PipelineExecution,
  PipelineUpdateRequest,
} from './types';

const PIPELINE_ENDPOINTS = {
  LIST: '/api/pipelines',
  CREATE: '/api/pipelines',
  GET: (id: string) => `/api/pipelines/${id}`,
  UPDATE: (id: string) => `/api/pipelines/${id}`,
  DELETE: (id: string) => `/api/pipelines/${id}`,
  EXECUTE: (id: string) => `/api/pipelines/${id}/execute`,
  EXECUTIONS: (id: string) => `/api/pipelines/${id}/executions`,
  EXECUTION: (id: string) => `/api/pipelines/executions/${id}`,
} as const;

export async function listPipelines(): Promise<Pipeline[]> {
  const response: AxiosResponse<Pipeline[]> = await apiClient.get(PIPELINE_ENDPOINTS.LIST);
  return response.data;
}

export async function createPipeline(data: PipelineCreateRequest): Promise<Pipeline> {
  const response: AxiosResponse<Pipeline> = await apiClient.post(PIPELINE_ENDPOINTS.CREATE, data);
  return response.data;
}

export async function getPipeline(id: string): Promise<Pipeline> {
  const response: AxiosResponse<Pipeline> = await apiClient.get(PIPELINE_ENDPOINTS.GET(id));
  return response.data;
}

export async function updatePipeline(id: string, data: PipelineUpdateRequest): Promise<Pipeline> {
  const response: AxiosResponse<Pipeline> = await apiClient.put(PIPELINE_ENDPOINTS.UPDATE(id), data);
  return response.data;
}

export async function deletePipeline(id: string): Promise<void> {
  await apiClient.delete(PIPELINE_ENDPOINTS.DELETE(id));
}

export async function executePipeline(id: string): Promise<PipelineExecution> {
  const response: AxiosResponse<PipelineExecution> = await apiClient.post(PIPELINE_ENDPOINTS.EXECUTE(id));
  return response.data;
}

export async function listExecutions(pipelineId: string): Promise<PipelineExecution[]> {
  const response: AxiosResponse<PipelineExecution[]> = await apiClient.get(PIPELINE_ENDPOINTS.EXECUTIONS(pipelineId));
  return response.data;
}

export const pipelineApi = {
  listPipelines,
  createPipeline,
  getPipeline,
  updatePipeline,
  deletePipeline,
  executePipeline,
  listExecutions,
} as const;

export default pipelineApi;
