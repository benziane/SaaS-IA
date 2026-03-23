export interface AgentStep {
  id: string;
  step_index: number;
  action: string;
  description: string;
  status: string;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface AgentRun {
  id: string;
  instruction: string;
  status: string;
  current_step: number;
  total_steps: number;
  steps: AgentStep[];
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface SentimentSegment {
  text: string;
  sentiment: string;
  score: number;
  emotions: string[];
}

export interface SentimentResponse {
  overall_sentiment: string;
  overall_score: number;
  segments: SentimentSegment[];
  emotion_summary: Record<string, number>;
  positive_percent: number;
  negative_percent: number;
  neutral_percent: number;
}
