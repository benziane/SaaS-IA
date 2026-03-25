export interface GeneratedVideo {
  id: string; user_id: string; title: string; description: string | null;
  video_type: string; prompt: string; provider: string;
  source_type: string | null; source_id: string | null;
  video_url: string | null; thumbnail_url: string | null;
  duration_s: number | null; width: number; height: number;
  format: string; status: string; error: string | null;
  settings_json: string; created_at: string; updated_at: string;
}
export interface VideoProject {
  id: string; user_id: string; name: string; description: string | null;
  video_count: number; total_duration_s: number; created_at: string; updated_at: string;
}
export interface GenerateVideoRequest {
  title: string; prompt: string; video_type?: string; provider?: string;
  duration_s?: number; width?: number; height?: number; style?: string; settings?: Record<string, unknown>;
}
