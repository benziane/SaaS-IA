/**
 * Multi-Agent Crew API
 */
import apiClient from '@/lib/apiClient';
import type { Crew, CrewCreateRequest, CrewRun, CrewTemplate } from './types';

const EP = {
  LIST: '/api/crews',
  CREATE: '/api/crews',
  TEMPLATES: '/api/crews/templates',
  FROM_TEMPLATE: (id: string) => `/api/crews/from-template/${id}`,
  GET: (id: string) => `/api/crews/${id}`,
  DELETE: (id: string) => `/api/crews/${id}`,
  RUN: (id: string) => `/api/crews/${id}/run`,
  RUNS: (id: string) => `/api/crews/${id}/runs`,
} as const;

export const listCrews = async (): Promise<Crew[]> => (await apiClient.get(EP.LIST)).data;
export const createCrew = async (data: CrewCreateRequest): Promise<Crew> => (await apiClient.post(EP.CREATE, data)).data;
export const deleteCrew = async (id: string): Promise<void> => { await apiClient.delete(EP.DELETE(id)); };
export const runCrew = async (id: string, instruction: string, inputData?: Record<string, unknown>): Promise<CrewRun> =>
  (await apiClient.post(EP.RUN(id), { instruction, input_data: inputData || {} })).data;
export const listCrewRuns = async (crewId: string): Promise<CrewRun[]> => (await apiClient.get(EP.RUNS(crewId))).data;
export const listCrewTemplates = async (category?: string): Promise<CrewTemplate[]> =>
  (await apiClient.get(EP.TEMPLATES, { params: category ? { category } : {} })).data;
export const createCrewFromTemplate = async (templateId: string, name?: string): Promise<Crew> =>
  (await apiClient.post(EP.FROM_TEMPLATE(templateId), null, { params: name ? { name } : {} })).data;
