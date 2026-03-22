/**
 * Transcription API - Grade S++
 * API calls for transcription feature
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type {
  Transcription,
  TranscriptionCreateRequest,
  TranscriptionFilters,
  TranscriptionListResponse,
  TranscriptionStats,
  TranscriptionUploadRequest,
} from './types';

/* ========================================================================
   API ENDPOINTS
   ======================================================================== */

const TRANSCRIPTION_ENDPOINTS = {
  LIST: '/api/transcription',
  CREATE: '/api/transcription',
  UPLOAD: '/api/transcription/upload',
  STATS: '/api/transcription/stats',
  GET: (id: string) => `/api/transcription/${id}`,
  DELETE: (id: string) => `/api/transcription/${id}`,
} as const;

/* ========================================================================
   API FUNCTIONS
   ======================================================================== */

/**
 * List transcriptions with filters
 */
export async function listTranscriptions(
  filters?: TranscriptionFilters
): Promise<TranscriptionListResponse> {
  const params = new URLSearchParams();

  if (filters?.status) {
    params.append('status', filters.status);
  }
  if (filters?.skip !== undefined) {
    params.append('skip', filters.skip.toString());
  }
  if (filters?.limit !== undefined) {
    params.append('limit', filters.limit.toString());
  }

  // Backend returns a plain array; wrap into paginated format
  const response: AxiosResponse<Transcription[]> = await apiClient.get(
    `${TRANSCRIPTION_ENDPOINTS.LIST}?${params.toString()}`
  );

  const skip = filters?.skip ?? 0;
  const limit = filters?.limit ?? 100;
  return {
    items: response.data,
    total: response.data.length,
    skip,
    limit,
    has_more: response.data.length >= limit,
  };
}

/**
 * Create a new transcription
 */
export async function createTranscription(
  data: TranscriptionCreateRequest
): Promise<Transcription> {
  const response: AxiosResponse<Transcription> = await apiClient.post(
    TRANSCRIPTION_ENDPOINTS.CREATE,
    data
  );
  return response.data;
}

/**
 * Get a single transcription by ID
 */
export async function getTranscription(id: string): Promise<Transcription> {
  const response: AxiosResponse<Transcription> = await apiClient.get(
    TRANSCRIPTION_ENDPOINTS.GET(id)
  );
  return response.data;
}

/**
 * Get transcription statistics for the current user
 */
export async function getStats(): Promise<TranscriptionStats> {
  const response: AxiosResponse<TranscriptionStats> = await apiClient.get(
    TRANSCRIPTION_ENDPOINTS.STATS
  );
  return response.data;
}

/**
 * Upload a file for transcription
 */
export async function uploadTranscription(
  data: TranscriptionUploadRequest,
  onUploadProgress?: (progress: number) => void
): Promise<Transcription> {
  const formData = new FormData();
  formData.append('file', data.file);
  if (data.language) {
    formData.append('language', data.language);
  }

  const response: AxiosResponse<Transcription> = await apiClient.post(
    TRANSCRIPTION_ENDPOINTS.UPLOAD,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percent);
        }
      },
    }
  );
  return response.data;
}

/**
 * Delete a transcription
 */
export async function deleteTranscription(id: string): Promise<void> {
  await apiClient.delete(TRANSCRIPTION_ENDPOINTS.DELETE(id));
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export const transcriptionApi = {
  listTranscriptions,
  createTranscription,
  uploadTranscription,
  getTranscription,
  getStats,
  deleteTranscription,
} as const;

export default transcriptionApi;

