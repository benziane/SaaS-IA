export interface Dataset {
  id: string; user_id: string; name: string; filename: string; file_type: string;
  file_size: number; row_count: number; column_count: number;
  columns_json: string; preview_json: string; stats_json: string;
  status: string; error: string | null; created_at: string; updated_at: string;
}
export interface ChartSpec { type: string; title: string; data: Record<string, unknown>; config: Record<string, unknown>; }
export interface InsightItem { insight: string; confidence: number; category: string; }
export interface DataAnalysis {
  id: string; dataset_id: string; user_id: string; question: string;
  analysis_type: string; answer: string | null; charts: ChartSpec[];
  insights: InsightItem[]; code_executed: string | null;
  status: string; provider: string | null; error: string | null; created_at: string;
}
