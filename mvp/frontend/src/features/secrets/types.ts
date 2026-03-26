/**
 * Secrets Types
 * Type definitions for secret rotation tracking
 */

export interface SecretRegistration {
  id: string;
  name: string;
  secret_type: string;
  status: 'active' | 'rotating' | 'expired' | 'compromised';
  rotation_days: number;
  registered_at: string;
  last_rotated_at: string | null;
  next_rotation_at: string | null;
  rotation_count: number;
  age_days: number;
  notes: string | null;
}

export interface SecretAlert {
  name: string;
  type: string;
  status: string;
  urgency: 'critical' | 'overdue' | 'warning';
  message: string;
  overdue_days?: number;
  days_remaining?: number;
}

export interface SecretHealth {
  score: number;
  total: number;
  healthy: number;
  warning: number;
  overdue: number;
  compromised: number;
}

export interface SecretRegisterRequest {
  name: string;
  secret_type: string;
  rotation_days: number;
  notes?: string;
}

export interface SecretRotateRequest {
  hint?: string;
}
