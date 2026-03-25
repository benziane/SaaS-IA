/**
 * Presentation Gen Types
 */

export interface SlideContent {
  slide_number: number;
  title: string;
  content: string;
  notes: string | null;
  layout: string;
}

export interface Presentation {
  id: string;
  user_id: string;
  title: string;
  topic: string;
  num_slides: number;
  style: string;
  template: string;
  slides: SlideContent[];
  status: 'generating' | 'ready' | 'error';
  format: string;
  download_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface PresentationCreateRequest {
  title: string;
  topic: string;
  num_slides?: number;
  style?: string;
  template?: string;
  language?: string;
  source_text?: string;
  source_url?: string;
}

export interface PresentationFromTranscriptRequest {
  transcript_id: string;
  title?: string;
  num_slides?: number;
  style?: string;
  template?: string;
  language?: string;
}

export interface SlideUpdateRequest {
  title?: string;
  content?: string;
  notes?: string;
  layout?: string;
}

export interface SlideInsertRequest {
  title: string;
  content: string;
  notes?: string;
  layout?: string;
}

export interface ExportRequest {
  format: 'html' | 'markdown' | 'pdf';
}

export interface ExportResult {
  format: string;
  content: string | null;
  filename: string;
  note?: string;
}

export interface PresentationTemplate {
  id: string;
  name: string;
  description: string;
}
