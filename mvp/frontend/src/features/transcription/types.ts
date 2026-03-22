/**
 * Transcription Types - Grade S++
 * Type definitions for transcription feature
 */

/* ========================================================================
   ENUMS
   ======================================================================== */

export enum TranscriptionStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/* ========================================================================
   TRANSCRIPTION
   ======================================================================== */

export type TranscriptionSourceType = 'youtube' | 'upload' | 'url';

export interface Transcription {
  id: string;
  video_url: string;
  source_type: TranscriptionSourceType;
  original_filename: string | null;
  language: string | null;
  status: TranscriptionStatus;
  text: string | null;
  confidence: number | null;
  duration_seconds: number | null;
  error: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  user_id: string;
}

/* ========================================================================
   REQUESTS
   ======================================================================== */

export interface TranscriptionCreateRequest {
  video_url: string;
  language?: string;
}

export interface TranscriptionUploadRequest {
  file: File;
  language?: string;
}

/* ========================================================================
   RESPONSES
   ======================================================================== */

/**
 * Generic paginated response matching the backend PaginatedResponse schema.
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export type TranscriptionListResponse = PaginatedResponse<Transcription>;

/* ========================================================================
   STATS
   ======================================================================== */

export interface RecentTranscription {
  id: string;
  video_url: string;
  status: TranscriptionStatus;
  created_at: string;
}

export interface TranscriptionStats {
  total_transcriptions: number;
  completed: number;
  failed: number;
  pending: number;
  processing: number;
  total_duration_seconds: number;
  avg_confidence: number | null;
  recent_transcriptions: RecentTranscription[];
}

/* ========================================================================
   FORM DATA
   ======================================================================== */

export interface TranscriptionFormData {
  video_url: string;
  language?: string;
}

/* ========================================================================
   FILTERS
   ======================================================================== */

export interface TranscriptionFilters {
  status?: TranscriptionStatus;
  skip?: number;
  limit?: number;
}

