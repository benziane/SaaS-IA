/**
 * TypeScript types for transcription data
 */

export type TranscriptionStatus =
  | 'pending'
  | 'downloading'
  | 'extracting'
  | 'transcribing'
  | 'post_processing'
  | 'completed'
  | 'failed';

export type LanguageCode = 'en' | 'fr' | 'ar' | 'auto';

export interface Transcription {
  id: number;
  youtube_url: string;
  video_id: string;
  video_title?: string;
  video_duration?: number;
  channel_name?: string;
  language: LanguageCode;
  detected_language?: string;
  status: TranscriptionStatus;
  progress: number;
  error_message?: string;
  raw_transcript?: string;
  corrected_transcript?: string;
  transcription_service?: string;
  model_used?: string;
  processing_time?: number;
  confidence_score?: number;
  word_count?: number;
  metadata?: Record<string, any>;
  is_public: boolean;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}

export interface TranscriptionList {
  transcriptions: Transcription[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TranscriptionStats {
  total_transcriptions: number;
  completed: number;
  in_progress: number;
  failed: number;
  total_duration: number;
  total_processing_time: number;
  average_confidence: number;
  languages: Record<string, number>;
}

export interface VideoPreview {
  video_id: string;
  title: string;
  duration: number;
  channel: string;
  description?: string;
  thumbnail?: string;
  upload_date?: string;
  view_count?: number;
}
