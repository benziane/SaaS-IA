/**
 * Multi-Agent Crew Types
 */

export interface AgentDefinition {
  id: string;
  role: string;
  name: string;
  goal: string;
  backstory?: string;
  tools: string[];
  provider?: string;
  max_iterations: number;
}

export interface Crew {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  goal: string | null;
  agents: AgentDefinition[];
  process_type: string;
  status: string;
  is_template: boolean;
  template_category: string | null;
  run_count: number;
  created_at: string;
  updated_at: string;
}

export interface AgentMessage {
  agent_id: string;
  agent_name: string;
  role: string;
  content: string;
  tool_used: string | null;
  iteration: number;
  timestamp: string;
}

export interface CrewRun {
  id: string;
  crew_id: string;
  user_id: string;
  status: string;
  instruction: string;
  current_agent: number;
  total_agents: number;
  messages: AgentMessage[];
  final_output: string | null;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  tokens_used: number;
  created_at: string;
}

export interface CrewCreateRequest {
  name: string;
  description?: string;
  goal?: string;
  agents: AgentDefinition[];
  process_type?: string;
}

export interface CrewTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  goal: string;
  agents: AgentDefinition[];
  process_type: string;
  icon: string;
}
