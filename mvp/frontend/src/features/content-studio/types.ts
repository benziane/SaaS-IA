/**
 * Content Studio Types
 */

export interface ContentProject {
  id: string;
  user_id: string;
  title: string;
  source_type: string;
  language: string;
  tone: string;
  target_audience: string | null;
  keywords: string | null;
  created_at: string;
  updated_at: string;
}

export interface GeneratedContent {
  id: string;
  project_id: string;
  format: string;
  title: string | null;
  content: string;
  metadata_json: string;
  status: string;
  provider: string | null;
  word_count: number;
  version: number;
  scheduled_at: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateRequest {
  title: string;
  source_type: 'text' | 'transcription' | 'document' | 'url';
  source_text?: string;
  source_id?: string;
  language?: string;
  tone?: string;
  target_audience?: string;
  keywords?: string[];
}

export interface GenerateRequest {
  formats: string[];
  provider?: string;
  custom_instructions?: string;
}

export interface ContentUpdateRequest {
  title?: string;
  content?: string;
  status?: string;
}

export interface ContentFormat {
  id: string;
  name: string;
  description: string;
  icon: string;
}
