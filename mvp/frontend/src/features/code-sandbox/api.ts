import apiClient from '@/lib/apiClient';
import type { CellResult, CodeDebugResponse, CodeExplainResponse, CodeGenerateResponse, Sandbox } from './types';

export const createSandbox = async (data: { name: string; language?: string; description?: string }): Promise<Sandbox> =>
  (await apiClient.post('/api/sandbox/sandboxes', data)).data;

export const listSandboxes = async (): Promise<Sandbox[]> =>
  (await apiClient.get('/api/sandbox/sandboxes')).data;

export const getSandbox = async (id: string): Promise<Sandbox> =>
  (await apiClient.get(`/api/sandbox/sandboxes/${id}`)).data;

export const deleteSandbox = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/sandbox/sandboxes/${id}`);
};

export const addCell = async (sandboxId: string, data: { source: string; cell_type?: string; language?: string }): Promise<Record<string, unknown>> =>
  (await apiClient.post(`/api/sandbox/sandboxes/${sandboxId}/cells`, data)).data;

export const updateCell = async (sandboxId: string, cellId: string, source: string): Promise<Record<string, unknown>> =>
  (await apiClient.put(`/api/sandbox/sandboxes/${sandboxId}/cells/${cellId}`, { source })).data;

export const deleteCell = async (sandboxId: string, cellId: string): Promise<void> => {
  await apiClient.delete(`/api/sandbox/sandboxes/${sandboxId}/cells/${cellId}`);
};

export const executeCell = async (sandboxId: string, cellId: string): Promise<CellResult> =>
  (await apiClient.post(`/api/sandbox/sandboxes/${sandboxId}/cells/${cellId}/execute`)).data;

export const generateCode = async (prompt: string, language?: string, context?: string): Promise<CodeGenerateResponse> =>
  (await apiClient.post('/api/sandbox/generate', { prompt, language, context })).data;

export const explainCode = async (code: string): Promise<CodeExplainResponse> =>
  (await apiClient.post('/api/sandbox/explain', { code })).data;

export const debugCode = async (code: string, error: string): Promise<CodeDebugResponse> =>
  (await apiClient.post('/api/sandbox/debug', { code, error })).data;
