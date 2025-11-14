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
} from './types';

/* ========================================================================
   API ENDPOINTS
   ======================================================================== */

const TRANSCRIPTION_ENDPOINTS = {
  LIST: '/api/transcription',
  CREATE: '/api/transcription',
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
  
  const response: AxiosResponse<Transcription[]> = await apiClient.get(
    `${TRANSCRIPTION_ENDPOINTS.LIST}?${params.toString()}`
  );
  
  // Backend returns array, we need to wrap it
  return {
    items: response.data,
    total: response.data.length, // TODO: Backend should return total count
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
  getTranscription,
  deleteTranscription,
} as const;

export default transcriptionApi;

