/**
 * Skill Seekers API
 * API calls for the Skill Seekers feature
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type {
  PaginatedJobs,
  ScrapeJob,
  ScrapeJobCreateRequest,
  SkillSeekersStatus,
} from './types';

/* ========================================================================
   API ENDPOINTS
   ======================================================================== */

const SKILL_SEEKERS_ENDPOINTS = {
  JOBS: '/api/skill-seekers/jobs',
  STATUS: '/api/skill-seekers/status',
  JOB: (id: string) => `/api/skill-seekers/jobs/${id}`,
  DELETE: (id: string) => `/api/skill-seekers/jobs/${id}`,
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
export async function listJobs(skip = 0, limit = 20): Promise<PaginatedJobs> {
  const response: AxiosResponse<PaginatedJobs> = await apiClient.get(
    SKILL_SEEKERS_ENDPOINTS.JOBS,
    { params: { skip, limit } }
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
 * Get the download URL for an output file
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
  getStatus,
  getDownloadUrl,
} as const;

export default skillSeekersApi;
