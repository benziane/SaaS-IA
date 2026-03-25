/**
 * Content Studio API
 */

import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type {
  ContentFormat,
  ContentProject,
  ContentUpdateRequest,
  GenerateRequest,
  GeneratedContent,
  ProjectCreateRequest,
} from './types';

const ENDPOINTS = {
  PROJECTS: '/api/content-studio/projects',
  PROJECT: (id: string) => `/api/content-studio/projects/${id}`,
  GENERATE: (id: string) => `/api/content-studio/projects/${id}/generate`,
  CONTENTS: (id: string) => `/api/content-studio/projects/${id}/contents`,
  CONTENT: (id: string) => `/api/content-studio/contents/${id}`,
  REGENERATE: (id: string) => `/api/content-studio/contents/${id}/regenerate`,
  FROM_URL: '/api/content-studio/from-url',
  FORMATS: '/api/content-studio/formats',
} as const;

export async function createProject(data: ProjectCreateRequest): Promise<ContentProject> {
  const response: AxiosResponse<ContentProject> = await apiClient.post(ENDPOINTS.PROJECTS, data);
  return response.data;
}

export async function listProjects(): Promise<ContentProject[]> {
  const response: AxiosResponse<ContentProject[]> = await apiClient.get(ENDPOINTS.PROJECTS);
  return response.data;
}

export async function deleteProject(id: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.PROJECT(id));
}

export async function generateContents(projectId: string, data: GenerateRequest): Promise<GeneratedContent[]> {
  const response: AxiosResponse<GeneratedContent[]> = await apiClient.post(ENDPOINTS.GENERATE(projectId), data);
  return response.data;
}

export async function getProjectContents(projectId: string): Promise<GeneratedContent[]> {
  const response: AxiosResponse<GeneratedContent[]> = await apiClient.get(ENDPOINTS.CONTENTS(projectId));
  return response.data;
}

export async function updateContent(id: string, data: ContentUpdateRequest): Promise<GeneratedContent> {
  const response: AxiosResponse<GeneratedContent> = await apiClient.put(ENDPOINTS.CONTENT(id), data);
  return response.data;
}

export async function regenerateContent(id: string, data?: { custom_instructions?: string; provider?: string }): Promise<GeneratedContent> {
  const response: AxiosResponse<GeneratedContent> = await apiClient.post(ENDPOINTS.REGENERATE(id), data || {});
  return response.data;
}

export async function listFormats(): Promise<{ formats: ContentFormat[] }> {
  const response: AxiosResponse<{ formats: ContentFormat[] }> = await apiClient.get(ENDPOINTS.FORMATS);
  return response.data;
}
