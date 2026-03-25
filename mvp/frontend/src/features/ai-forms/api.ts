/**
 * AI Forms API
 */

import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type {
  Form,
  FormAnalysis,
  FormCreateRequest,
  FormGenerateRequest,
  FormResponseCreateRequest,
  FormResponseItem,
  FormUpdateRequest,
} from './types';

const ENDPOINTS = {
  FORMS: '/api/forms',
  FORM: (id: string) => `/api/forms/${id}`,
  PUBLISH: (id: string) => `/api/forms/${id}/publish`,
  CLOSE: (id: string) => `/api/forms/${id}/close`,
  RESPONSES: (id: string) => `/api/forms/${id}/responses`,
  RESPONSE: (id: string, responseId: string) => `/api/forms/${id}/responses/${responseId}`,
  SCORE: (id: string, responseId: string) => `/api/forms/${id}/responses/${responseId}/score`,
  ANALYTICS: (id: string) => `/api/forms/${id}/analytics`,
  GENERATE: '/api/forms/generate',
  PUBLIC_FORM: (token: string) => `/api/forms/public/${token}`,
  PUBLIC_SUBMIT: (token: string) => `/api/forms/public/${token}/submit`,
} as const;

export async function createForm(data: FormCreateRequest): Promise<Form> {
  const response: AxiosResponse<Form> = await apiClient.post(ENDPOINTS.FORMS, data);
  return response.data;
}

export async function listForms(): Promise<Form[]> {
  const response: AxiosResponse<Form[]> = await apiClient.get(ENDPOINTS.FORMS);
  return response.data;
}

export async function getForm(id: string): Promise<Form> {
  const response: AxiosResponse<Form> = await apiClient.get(ENDPOINTS.FORM(id));
  return response.data;
}

export async function updateForm(id: string, data: FormUpdateRequest): Promise<Form> {
  const response: AxiosResponse<Form> = await apiClient.put(ENDPOINTS.FORM(id), data);
  return response.data;
}

export async function deleteForm(id: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.FORM(id));
}

export async function publishForm(id: string): Promise<Form> {
  const response: AxiosResponse<Form> = await apiClient.post(ENDPOINTS.PUBLISH(id));
  return response.data;
}

export async function closeForm(id: string): Promise<Form> {
  const response: AxiosResponse<Form> = await apiClient.post(ENDPOINTS.CLOSE(id));
  return response.data;
}

export async function listResponses(formId: string): Promise<FormResponseItem[]> {
  const response: AxiosResponse<FormResponseItem[]> = await apiClient.get(ENDPOINTS.RESPONSES(formId));
  return response.data;
}

export async function getResponse(formId: string, responseId: string): Promise<FormResponseItem> {
  const response: AxiosResponse<FormResponseItem> = await apiClient.get(ENDPOINTS.RESPONSE(formId, responseId));
  return response.data;
}

export async function scoreResponse(formId: string, responseId: string): Promise<FormResponseItem> {
  const response: AxiosResponse<FormResponseItem> = await apiClient.post(ENDPOINTS.SCORE(formId, responseId));
  return response.data;
}

export async function getAnalytics(formId: string): Promise<FormAnalysis> {
  const response: AxiosResponse<FormAnalysis> = await apiClient.get(ENDPOINTS.ANALYTICS(formId));
  return response.data;
}

export async function generateForm(data: FormGenerateRequest): Promise<Form> {
  const response: AxiosResponse<Form> = await apiClient.post(ENDPOINTS.GENERATE, data);
  return response.data;
}

export async function publicGetForm(shareToken: string): Promise<Form> {
  const response: AxiosResponse<Form> = await apiClient.get(ENDPOINTS.PUBLIC_FORM(shareToken));
  return response.data;
}

export async function publicSubmitResponse(
  shareToken: string,
  data: FormResponseCreateRequest,
): Promise<FormResponseItem> {
  const response: AxiosResponse<FormResponseItem> = await apiClient.post(
    ENDPOINTS.PUBLIC_SUBMIT(shareToken),
    data,
  );
  return response.data;
}
