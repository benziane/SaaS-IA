/**
 * API Keys Types
 */

export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  permissions: string[];
  rate_limit_per_day: number;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
}

export interface APIKeyCreated {
  id: string;
  name: string;
  key: string;
  key_prefix: string;
  permissions: string[];
  rate_limit_per_day: number;
  message: string;
}

export interface APIKeyCreateRequest {
  name: string;
  permissions?: string[];
  rate_limit_per_day?: number;
}
