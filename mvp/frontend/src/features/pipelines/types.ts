/**
 * Pipeline Types
 * Type definitions for AI pipeline builder
 */

export interface PipelineStep {
  id: string;
  type: string;
  config: Record<string, unknown>;
  position: number;
}

export interface Pipeline {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  steps: PipelineStep[];
  status: string;
  is_template: boolean;
  created_at: string;
  updated_at: string;
}

export interface PipelineCreateRequest {
  name: string;
  description?: string;
  steps: PipelineStep[];
  is_template?: boolean;
}

export interface PipelineUpdateRequest {
  name?: string;
  description?: string;
  steps?: PipelineStep[];
  status?: string;
}

export interface PipelineExecution {
  id: string;
  pipeline_id: string;
  user_id: string;
  status: string;
  current_step: number;
  total_steps: number;
  results: Record<string, unknown>[];
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}
