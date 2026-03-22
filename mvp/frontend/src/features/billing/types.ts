/**
 * Billing Types
 * Type definitions for billing and quota features
 */

export interface Plan {
  id: string;
  name: string;
  display_name: string;
  max_transcriptions_month: number;
  max_audio_minutes_month: number;
  max_ai_calls_month: number;
  price_cents: number;
  is_active: boolean;
}

export interface UserQuota {
  plan: Plan;
  transcriptions_used: number;
  transcriptions_limit: number;
  audio_minutes_used: number;
  audio_minutes_limit: number;
  ai_calls_used: number;
  ai_calls_limit: number;
  period_start: string;
  period_end: string;
  usage_percent: number;
}
