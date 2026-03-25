/**
 * Skill Seekers API
 * API calls for the Skill Seekers feature
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type {
  FilePreview,
  PaginatedJobs,
  ScrapeJob,
  ScrapeJobCreateRequest,
  ScrapeJobStats,
  SkillSeekersStatus,
} from './types';

/* ========================================================================
   API ENDPOINTS
   ======================================================================== */

const SKILL_SEEKERS_ENDPOINTS = {
  JOBS: '/api/skill-seekers/jobs',
  STATS: '/api/skill-seekers/jobs/stats',
  STATUS: '/api/skill-seekers/status',
  JOB: (id: string) => `/api/skill-seekers/jobs/${id}`,
  DELETE: (id: string) => `/api/skill-seekers/jobs/${id}`,
  RETRY: (id: string) => `/api/skill-seekers/jobs/${id}/retry`,
  CANCEL: (id: string) => `/api/skill-seekers/jobs/${id}/cancel`,
  PREVIEW: (id: string, filename: string) =>
    `/api/skill-seekers/jobs/${id}/preview/${filename}`,
  DOWNLOAD: (id: string, filename: string) =>
    `/api/skill-seekers/jobs/${id}/download/${filename}`,
} as const;

/* ========================================================================
   API FUNCTIONS
   ======================================================================== */

/**
 * Create a new scrape job
 */
export async function createJob(data: ScrapeJobCreateRequest): Promise<ScrapeJob> {
  const response: AxiosResponse<ScrapeJob> = await apiClient.post(
    SKILL_SEEKERS_ENDPOINTS.JOBS,
    data
  );
  return response.data;
}

/**
 * List scrape jobs with pagination
 */
export async function listJobs(skip = 0, limit = 20, status?: string): Promise<PaginatedJobs> {
  const params: Record<string, unknown> = { skip, limit };
  if (status) params.status = status;
  const response: AxiosResponse<PaginatedJobs> = await apiClient.get(
    SKILL_SEEKERS_ENDPOINTS.JOBS,
    { params }
  );
  return response.data;
}

/**
 * Get a single scrape job by ID
 */
export async function getJob(id: string): Promise<ScrapeJob> {
  const response: AxiosResponse<ScrapeJob> = await apiClient.get(
    SKILL_SEEKERS_ENDPOINTS.JOB(id)
  );
  return response.data;
}

/**
 * Delete a scrape job
 */
export async function deleteJob(id: string): Promise<void> {
  await apiClient.delete(SKILL_SEEKERS_ENDPOINTS.DELETE(id));
}

/**
 * Check CLI status
 */
export async function getStatus(): Promise<SkillSeekersStatus> {
  const response: AxiosResponse<SkillSeekersStatus> = await apiClient.get(
    SKILL_SEEKERS_ENDPOINTS.STATUS
  );
  return response.data;
}

/**
 * Retry a failed scrape job
 */
export async function retryJob(id: string): Promise<ScrapeJob> {
  const response: AxiosResponse<ScrapeJob> = await apiClient.post(
    SKILL_SEEKERS_ENDPOINTS.RETRY(id)
  );
  return response.data;
}

/**
 * Cancel a running/pending scrape job
 */
export async function cancelJob(id: string): Promise<void> {
  await apiClient.post(SKILL_SEEKERS_ENDPOINTS.CANCEL(id));
}

/**
 * Preview output file content
 */
export async function previewFile(jobId: string, filename: string): Promise<FilePreview> {
  const response: AxiosResponse<FilePreview> = await apiClient.get(
    SKILL_SEEKERS_ENDPOINTS.PREVIEW(jobId, filename)
  );
  return response.data;
}

/**
 * Get scrape job stats for the current user
 */
export async function getStats(): Promise<ScrapeJobStats> {
  const response: AxiosResponse<ScrapeJobStats> = await apiClient.get(
    SKILL_SEEKERS_ENDPOINTS.STATS
  );
  return response.data;
}

/**
 * Get a signed download URL (token-based, no JWT required)
 */
export async function getSignedDownloadUrl(jobId: string, filename: string): Promise<string> {
  const response = await apiClient.get<{ token: string; url: string }>(
    `/api/skill-seekers/jobs/${jobId}/download-token/${filename}`
  );
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';
  return `${baseUrl}${response.data.url}`;
}

/**
 * Get the download URL for an output file (legacy, requires JWT)
 */
export function getDownloadUrl(jobId: string, filename: string): string {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';
  return `${baseUrl}${SKILL_SEEKERS_ENDPOINTS.DOWNLOAD(jobId, filename)}`;
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export const skillSeekersApi = {
  createJob,
  listJobs,
  getJob,
  deleteJob,
  retryJob,
  cancelJob,
  previewFile,
  getStatus,
  getStats,
  getDownloadUrl,
  getSignedDownloadUrl,
} as const;

export default skillSeekersApi;
