/**
 * Knowledge Base API
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type { AskResponse, KBDocument, SearchResponse } from './types';

const KB_ENDPOINTS = {
  UPLOAD: '/api/knowledge/upload',
  DOCUMENTS: '/api/knowledge/documents',
  DELETE: (id: string) => `/api/knowledge/documents/${id}`,
  SEARCH: '/api/knowledge/search',
  ASK: '/api/knowledge/ask',
} as const;

export async function uploadDocument(
  file: File,
  onProgress?: (pct: number) => void
): Promise<KBDocument> {
  const formData = new FormData();
  formData.append('file', file);

  const response: AxiosResponse<KBDocument> = await apiClient.post(
    KB_ENDPOINTS.UPLOAD,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    }
  );
  return response.data;
}

export async function listDocuments(): Promise<KBDocument[]> {
  const response: AxiosResponse<KBDocument[]> = await apiClient.get(KB_ENDPOINTS.DOCUMENTS);
  return response.data;
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(KB_ENDPOINTS.DELETE(id));
}

export async function searchDocuments(query: string, limit?: number): Promise<SearchResponse> {
  const response: AxiosResponse<SearchResponse> = await apiClient.post(KB_ENDPOINTS.SEARCH, {
    query,
    limit: limit || 5,
  });
  return response.data;
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const response: AxiosResponse<AskResponse> = await apiClient.post(KB_ENDPOINTS.ASK, {
    question,
  });
  return response.data;
}

export const knowledgeApi = { uploadDocument, listDocuments, deleteDocument, searchDocuments, askQuestion } as const;
export default knowledgeApi;
