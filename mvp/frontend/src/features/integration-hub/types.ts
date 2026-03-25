/**
 * Integration Hub Types
 */

export interface IntegrationConnector {
  id: string;
  user_id: string;
  name: string;
  type: string;
  provider: string;
  status: string;
  webhook_url: string | null;
  events_received: number;
  last_event_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WebhookEvent {
  id: string;
  connector_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  status: string;
  processed_at: string | null;
  created_at: string;
}

export interface IntegrationTrigger {
  id: string;
  connector_id: string;
  event_type: string;
  action_module: string;
  action_config: Record<string, unknown>;
  is_active: boolean;
  executions: number;
  created_at: string;
}

export interface ConnectorCreateRequest {
  name: string;
  type: string;
  provider?: string;
  config?: Record<string, unknown>;
  enabled?: boolean;
}

export interface TriggerCreateRequest {
  connector_id: string;
  event_type: string;
  action_module: string;
  action_config?: Record<string, unknown>;
}

export interface ProviderInfo {
  slug: string;
  name: string;
  description: string;
  supported_types: string[];
  icon: string;
  events: string[];
}

export interface ConnectorTestResult {
  success: boolean;
  provider: string;
  type: string;
  message: string;
  webhook_url?: string;
}
