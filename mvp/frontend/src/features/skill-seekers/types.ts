/**
 * Skill Seekers Types
 * Type definitions for the Skill Seekers feature
 */

/* ========================================================================
   ENUMS
   ======================================================================== */

export enum ScrapeJobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/* ========================================================================
   SCRAPE JOB
   ======================================================================== */

export interface ScrapeJob {
  id: string;
  user_id: string;
  repos: string[];
  targets: string[];
  enhance: boolean;
  status: ScrapeJobStatus;
  progress: number;
  current_step: string;
  output_files: string[];
  error: string | null;
  created_at: string;
  updated_at: string;
}

/* ========================================================================
   REQUESTS
   ======================================================================== */

export interface ScrapeJobCreateRequest {
  repos: string[];
  targets: string[];
  enhance: boolean;
}

/* ========================================================================
   RESPONSES
   ======================================================================== */

export interface PaginatedJobs {
  items: ScrapeJob[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface SkillSeekersStatus {
  installed: boolean;
  mock_mode: boolean;
}
