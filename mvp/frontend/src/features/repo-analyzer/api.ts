/**
 * Repo Analyzer API
 * API calls for the Repo Analyzer feature
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type {
  AnalysisCreateRequest,
  CompareRequest,
  CompareResult,
  PaginatedAnalyses,
  RepoAnalysis,
  RepoAnalyzerStatus,
} from './types';

/* ========================================================================
   API ENDPOINTS
   ======================================================================== */

const REPO_ANALYZER_ENDPOINTS = {
  ANALYZE: '/api/repo-analyzer/analyze',
  ANALYSES: '/api/repo-analyzer/analyses',
  STATUS: '/api/repo-analyzer/status',
  COMPARE: '/api/repo-analyzer/compare',
  ANALYSIS: (id: string) => `/api/repo-analyzer/${id}`,
  DELETE: (id: string) => `/api/repo-analyzer/${id}`,
} as const;

/* ========================================================================
   API FUNCTIONS
   ======================================================================== */

/**
 * Create a new repo analysis
 */
export async function createAnalysis(data: AnalysisCreateRequest): Promise<RepoAnalysis> {
  const response: AxiosResponse<RepoAnalysis> = await apiClient.post(
    REPO_ANALYZER_ENDPOINTS.ANALYZE,
    data
  );
  return response.data;
}

/**
 * List repo analyses with pagination
 */
export async function listAnalyses(skip = 0, limit = 20): Promise<PaginatedAnalyses> {
  const response: AxiosResponse<PaginatedAnalyses> = await apiClient.get(
    REPO_ANALYZER_ENDPOINTS.ANALYSES,
    { params: { skip, limit } }
  );
  return response.data;
}

/**
 * Get a single analysis by ID
 */
export async function getAnalysis(id: string): Promise<RepoAnalysis> {
  const response: AxiosResponse<RepoAnalysis> = await apiClient.get(
    REPO_ANALYZER_ENDPOINTS.ANALYSIS(id)
  );
  return response.data;
}

/**
 * Delete an analysis
 */
export async function deleteAnalysis(id: string): Promise<void> {
  await apiClient.delete(REPO_ANALYZER_ENDPOINTS.DELETE(id));
}

/**
 * Check git status
 */
export async function getStatus(): Promise<RepoAnalyzerStatus> {
  const response: AxiosResponse<RepoAnalyzerStatus> = await apiClient.get(
    REPO_ANALYZER_ENDPOINTS.STATUS
  );
  return response.data;
}

/**
 * Compare multiple repos
 */
export async function compareRepos(data: CompareRequest): Promise<CompareResult> {
  const response: AxiosResponse<CompareResult> = await apiClient.post(
    REPO_ANALYZER_ENDPOINTS.COMPARE,
    data
  );
  return response.data;
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export const repoAnalyzerApi = {
  createAnalysis,
  listAnalyses,
  getAnalysis,
  deleteAnalysis,
  getStatus,
  compareRepos,
} as const;

export default repoAnalyzerApi;
