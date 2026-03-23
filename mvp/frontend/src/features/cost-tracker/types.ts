export interface UsageLog {
  provider: string;
  model: string;
  module: string;
  action: string;
  total_tokens: number;
  cost_cents: number;
  latency_ms: number;
  success: boolean;
  created_at: string;
}

export interface CostSummary {
  total_cost_cents: number;
  total_tokens: number;
  total_calls: number;
  avg_latency_ms: number;
  period_start: string;
  period_end: string;
}

export interface ProviderBreakdown {
  provider: string;
  model: string;
  total_calls: number;
  total_tokens: number;
  total_cost_cents: number;
  avg_latency_ms: number;
  success_rate: number;
  label: string;
}

export interface ModuleBreakdown {
  module: string;
  total_calls: number;
  total_tokens: number;
  total_cost_cents: number;
}

export interface CostRecommendation {
  type: string;
  message: string;
  potential_savings_cents: number;
}

export interface CostAlert {
  level: 'info' | 'warning' | 'critical';
  title: string;
  message: string;
  metric: string;
  current_value: number;
  threshold_value: number;
}

export interface CostDashboard {
  summary: CostSummary;
  by_provider: ProviderBreakdown[];
  by_module: ModuleBreakdown[];
  recommendations: CostRecommendation[];
  recent_calls: UsageLog[];
}
