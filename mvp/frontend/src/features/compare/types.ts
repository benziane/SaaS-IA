/**
 * Compare Types
 * Type definitions for multi-model comparison
 */

export interface ProviderResult {
  provider: string;
  model: string;
  response: string;
  response_time_ms: number;
  error: string | null;
}

export interface CompareResponse {
  id: string;
  prompt: string;
  results: ProviderResult[];
  created_at: string;
}

export interface CompareRequest {
  prompt: string;
  providers: string[];
}

export interface VoteRequest {
  provider_name: string;
  quality_score: number;
}

export interface ProviderStats {
  provider: string;
  total_votes: number;
  avg_score: number;
  win_count: number;
}
