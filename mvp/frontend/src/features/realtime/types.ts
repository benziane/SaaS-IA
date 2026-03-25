export interface RealtimeSession {
  id: string; user_id: string; title: string | null; mode: string;
  status: string; provider: string; model: string | null;
  system_prompt: string | null; knowledge_base_id: string | null;
  config_json: string; total_turns: number; audio_duration_s: number;
  tokens_used: number; started_at: string; ended_at: string | null; created_at: string;
}
export interface SessionMessage {
  role: string; content: string; content_type: string;
  timestamp: string; metadata: Record<string, unknown>;
}
export interface SessionCreateRequest {
  title?: string; mode?: string; provider?: string;
  system_prompt?: string; knowledge_base_id?: string; config?: Record<string, unknown>;
}
