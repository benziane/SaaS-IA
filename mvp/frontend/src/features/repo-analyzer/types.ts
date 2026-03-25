/**
 * Repo Analyzer Types
 * Type definitions for the Repo Analyzer feature
 */

/* ========================================================================
   ENUMS
   ======================================================================== */

export enum AnalysisStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export type AnalysisType =
  | 'structure'
  | 'tech_stack'
  | 'quality'
  | 'documentation'
  | 'dependencies'
  | 'security'
  | 'all';

export type AnalysisDepth = 'quick' | 'standard' | 'deep';

/* ========================================================================
   RESULT TYPES
   ======================================================================== */

export interface TechStackResult {
  languages: Record<string, number>;
  frameworks: string[];
  build_tools: string[];
  package_manager: string;
  runtime: string;
}

export interface QualityResult {
  score: number;
  grade: string;
  issues: string[];
  recommendations: string[];
}

export interface StructureResult {
  total_files: number;
  total_lines: number;
  tree: Record<string, unknown>;
  key_files: string[];
  extension_counts?: Record<string, number>;
}

export interface DependencyResult {
  total: number;
  direct: number;
  dev: number;
  outdated: string[];
  vulnerabilities: string[];
}

export interface SecurityResult {
  issues: Array<{
    type: string;
    file: string;
    severity: string;
    message: string;
    count?: number;
  }>;
  risk_level: string;
  secrets_found: number;
  env_files_committed: number;
}

export interface DocumentationResult {
  readme_suggestions: string[];
  architecture_overview: string;
  api_docs_suggestions: string[];
}

export interface AnalysisResults {
  structure?: StructureResult;
  tech_stack?: TechStackResult;
  quality?: QualityResult;
  dependencies?: DependencyResult;
  security?: SecurityResult;
  documentation?: DocumentationResult;
}

/* ========================================================================
   ANALYSIS
   ======================================================================== */

export interface RepoAnalysis {
  id: string;
  user_id: string;
  repo_url: string;
  repo_name: string;
  status: AnalysisStatus;
  analysis_types: AnalysisType[];
  depth: AnalysisDepth;
  results: AnalysisResults | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

/* ========================================================================
   REQUESTS
   ======================================================================== */

export interface AnalysisCreateRequest {
  repo_url: string;
  analysis_types: AnalysisType[];
  depth: AnalysisDepth;
}

export interface CompareRequest {
  repo_urls: string[];
  analysis_types: AnalysisType[];
}

/* ========================================================================
   RESPONSES
   ======================================================================== */

export interface PaginatedAnalyses {
  items: RepoAnalysis[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface RepoAnalyzerStatus {
  installed: boolean;
  mock_mode: boolean;
}

export interface CompareResult {
  repos: Array<Record<string, unknown>>;
  summary: Record<string, unknown>;
}
