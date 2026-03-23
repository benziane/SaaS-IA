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

/* ========================================================================
   YOUTUBE ENHANCED TYPES
   ======================================================================== */

export interface YouTubeMetadata {
  video_id: string;
  title: string;
  description: string;
  uploader: string;
  channel_url: string;
  duration_seconds: number;
  view_count: number;
  like_count: number;
  upload_date: string;
  thumbnail: string;
  tags: string[];
  categories: string[];
  chapters: { title: string; start_time: number; end_time: number }[];
  language: string;
  is_live: boolean;
}

export interface TranscriptSegment {
  text: string;
  start: number;
  end: number;
  duration: number;
  confidence: number | null;
}

export interface SmartTranscribeResponse {
  text: string;
  segments: TranscriptSegment[];
  language: string;
  duration_seconds: number;
  confidence: number;
  provider: string;
  is_manual: boolean;
  error: string | null;
}

export interface VideoTranscriptResult {
  video_id: string;
  title: string;
  url: string;
  transcript: string;
  provider: string;
  duration: number;
  language: string;
  success: boolean;
  error: string | null;
  metadata: YouTubeMetadata | null;
}

export interface PlaylistTranscribeResponse {
  success: boolean;
  total: number;
  transcribed: number;
  results: VideoTranscriptResult[];
  error: string | null;
}

export interface ChapterSummary {
  title: string;
  start_time: number;
  end_time: number;
  text: string;
  summary: string;
}

export interface AutoChapterResponse {
  video_id: string;
  title: string;
  chapters: ChapterSummary[];
  full_summary: string;
  provider: string;
}

