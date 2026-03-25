/**
 * Presentation Gen API
 */

import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type {
  ExportRequest,
  ExportResult,
  Presentation,
  PresentationCreateRequest,
  PresentationFromTranscriptRequest,
  PresentationTemplate,
  SlideInsertRequest,
  SlideUpdateRequest,
} from './types';

const ENDPOINTS = {
  LIST: '/api/presentations',
  DETAIL: (id: string) => `/api/presentations/${id}`,
  TEMPLATES: '/api/presentations/templates',
  SLIDE: (id: string, num: number) => `/api/presentations/${id}/slides/${num}`,
  EXPORT: (id: string) => `/api/presentations/${id}/export`,
  FROM_TRANSCRIPT: '/api/presentations/from-transcript',
} as const;

export async function createPresentation(data: PresentationCreateRequest): Promise<Presentation> {
  const response: AxiosResponse<Presentation> = await apiClient.post(ENDPOINTS.LIST, data);
  return response.data;
}

export async function listPresentations(): Promise<Presentation[]> {
  const response: AxiosResponse<Presentation[]> = await apiClient.get(ENDPOINTS.LIST);
  return response.data;
}

export async function getPresentation(id: string): Promise<Presentation> {
  const response: AxiosResponse<Presentation> = await apiClient.get(ENDPOINTS.DETAIL(id));
  return response.data;
}

export async function deletePresentation(id: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.DETAIL(id));
}

export async function updateSlide(
  presentationId: string,
  slideNumber: number,
  data: SlideUpdateRequest,
): Promise<Presentation> {
  const response: AxiosResponse<Presentation> = await apiClient.put(
    ENDPOINTS.SLIDE(presentationId, slideNumber),
    data,
  );
  return response.data;
}

export async function addSlide(
  presentationId: string,
  afterSlide: number,
  data: SlideInsertRequest,
): Promise<Presentation> {
  const response: AxiosResponse<Presentation> = await apiClient.post(
    ENDPOINTS.SLIDE(presentationId, afterSlide),
    data,
  );
  return response.data;
}

export async function removeSlide(
  presentationId: string,
  slideNumber: number,
): Promise<Presentation> {
  const response: AxiosResponse<Presentation> = await apiClient.delete(
    ENDPOINTS.SLIDE(presentationId, slideNumber),
  );
  return response.data;
}

export async function exportPresentation(
  id: string,
  data: ExportRequest,
): Promise<ExportResult> {
  const response: AxiosResponse<ExportResult> = await apiClient.post(ENDPOINTS.EXPORT(id), data);
  return response.data;
}

export async function generateFromTranscript(
  data: PresentationFromTranscriptRequest,
): Promise<Presentation> {
  const response: AxiosResponse<Presentation> = await apiClient.post(
    ENDPOINTS.FROM_TRANSCRIPT,
    data,
  );
  return response.data;
}

export async function getTemplates(): Promise<{ templates: PresentationTemplate[] }> {
  const response: AxiosResponse<{ templates: PresentationTemplate[] }> = await apiClient.get(
    ENDPOINTS.TEMPLATES,
  );
  return response.data;
}
