export interface SandboxCell {
  id: string;
  cell_type: string;
  source: string;
  language: string;
  output: string | null;
  error: string | null;
  execution_time_ms: number | null;
  status: string;
}

export interface Sandbox {
  id: string;
  user_id: string;
  name: string;
  language: string;
  description: string | null;
  cells: SandboxCell[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CellResult {
  cell_id: string;
  output: string | null;
  error: string | null;
  execution_time_ms: number | null;
  status: string;
}

export interface CodeGenerateResponse {
  code: string;
  explanation: string;
  language: string;
}

export interface CodeExplainResponse {
  explanation: string;
  complexity: string | null;
}

export interface CodeDebugResponse {
  fixed_code: string;
  explanation: string;
  root_cause: string;
}
