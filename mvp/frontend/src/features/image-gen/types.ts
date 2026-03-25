export interface GeneratedImage {
  id: string; user_id: string; prompt: string; negative_prompt: string | null;
  style: string; provider: string; model: string | null; width: number; height: number;
  image_url: string | null; thumbnail_url: string | null; source_type: string;
  source_id: string | null; status: string; error: string | null;
  metadata_json: string; created_at: string;
}
export interface ImageProject {
  id: string; user_id: string; name: string; description: string | null;
  image_count: number; created_at: string; updated_at: string;
}
export interface GenerateImageRequest {
  prompt: string; negative_prompt?: string; style?: string;
  provider?: string; width?: number; height?: number; project_id?: string;
}
