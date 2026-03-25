export interface TrainingSample { instruction: string; input: string; output: string; system?: string; }
export interface TrainingDataset {
  id: string; user_id: string; name: string; description: string | null;
  dataset_type: string; source_type: string; sample_count: number;
  validation_split: number; quality_score: number | null; status: string;
  created_at: string; updated_at: string;
}
export interface FineTuneJob {
  id: string; user_id: string; dataset_id: string; name: string;
  base_model: string; provider: string; status: string;
  hyperparams_json: string; metrics_json: string;
  result_model_id: string | null; error: string | null;
  epochs_completed: number; total_epochs: number;
  estimated_cost_usd: number; actual_cost_usd: number;
  started_at: string | null; completed_at: string | null; created_at: string;
}
export interface ModelEvaluation {
  id: string; job_id: string; eval_type: string; metrics_json: string;
  base_model_score: number | null; tuned_model_score: number | null;
  improvement_pct: number | null; summary: string | null; created_at: string;
}
export interface AvailableModel {
  id: string; name: string; provider: string; parameters: string;
  cost_per_1k_tokens: number; supports_lora: boolean; max_context: number;
}
