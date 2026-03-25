/**
 * AI Workflows Types
 */

export interface WorkflowNode {
  id: string;
  type: string;
  action: string;
  label: string;
  config: Record<string, unknown>;
  position_x: number;
  position_y: number;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  condition?: string | null;
}

export interface Workflow {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  trigger_type: string;
  trigger_config: Record<string, unknown>;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  status: string;
  is_template: boolean;
  template_category: string | null;
  run_count: number;
  last_run_at: string | null;
  schedule_cron: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  user_id: string;
  status: string;
  trigger_type: string;
  current_node: number;
  total_nodes: number;
  results: Record<string, unknown>[];
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  created_at: string;
}

export interface WorkflowCreateRequest {
  name: string;
  description?: string;
  trigger_type?: string;
  trigger_config?: Record<string, unknown>;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  schedule_cron?: string;
}

export interface WorkflowUpdateRequest {
  name?: string;
  description?: string;
  trigger_type?: string;
  nodes?: WorkflowNode[];
  edges?: WorkflowEdge[];
  status?: string;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  trigger_type: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  icon: string;
}
