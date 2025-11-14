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

export interface Transcription {
  id: string;
  video_url: string;
  status: TranscriptionStatus;
  text: string | null;
  confidence: number | null;
  error: string | null;
  created_at: string;
  updated_at: string;
  user_id: number;
}

/* ========================================================================
   REQUESTS
   ======================================================================== */

export interface TranscriptionCreateRequest {
  video_url: string;
}

/* ========================================================================
   RESPONSES
   ======================================================================== */

export interface TranscriptionListResponse {
  items: Transcription[];
  total: number;
}

/* ========================================================================
   FORM DATA
   ======================================================================== */

export interface TranscriptionFormData {
  video_url: string;
}

/* ========================================================================
   FILTERS
   ======================================================================== */

export interface TranscriptionFilters {
  status?: TranscriptionStatus;
  skip?: number;
  limit?: number;
}

