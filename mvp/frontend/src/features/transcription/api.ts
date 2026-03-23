/**
 * Transcription API - Grade S++
 * API calls for transcription feature
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type {
  AutoChapterResponse,
  LiveStreamCapture,
  LiveStreamStatus,
  PlaylistTranscribeResponse,
  SmartTranscribeResponse,
  Transcription,
  TranscriptionCreateRequest,
  TranscriptionFilters,
  TranscriptionListResponse,
  TranscriptionStats,
  TranscriptionUploadRequest,
  VideoAnalyzeResponse,
  YouTubeMetadata,
} from './types';

/* ========================================================================
   API ENDPOINTS
   ======================================================================== */

const TRANSCRIPTION_ENDPOINTS = {
  LIST: '/api/transcription',
  CREATE: '/api/transcription',
  UPLOAD: '/api/transcription/upload',
  STATS: '/api/transcription/stats',
  SMART_TRANSCRIBE: '/api/transcription/smart-transcribe',
  METADATA: '/api/transcription/metadata',
  PLAYLIST: '/api/transcription/playlist',
  AUTO_CHAPTER: '/api/transcription/auto-chapter',
  STREAM_STATUS: '/api/transcription/stream/status',
  STREAM_CAPTURE: '/api/transcription/stream/capture',
  VIDEO_ANALYZE: '/api/transcription/video/analyze',
  GET: (id: string) => `/api/transcription/${id}`,
  DELETE: (id: string) => `/api/transcription/${id}`,
} as const;

/* ========================================================================
   API FUNCTIONS
   ======================================================================== */

/**
 * List transcriptions with filters
 */
export async function listTranscriptions(
  filters?: TranscriptionFilters
): Promise<TranscriptionListResponse> {
  const params = new URLSearchParams();

  if (filters?.status) {
    params.append('status', filters.status);
  }
  if (filters?.skip !== undefined) {
    params.append('skip', filters.skip.toString());
  }
  if (filters?.limit !== undefined) {
    params.append('limit', filters.limit.toString());
  }

  // Backend returns a plain array; wrap into paginated format
  const response: AxiosResponse<Transcription[]> = await apiClient.get(
    `${TRANSCRIPTION_ENDPOINTS.LIST}?${params.toString()}`
  );

  const skip = filters?.skip ?? 0;
  const limit = filters?.limit ?? 100;
  return {
    items: response.data,
    total: response.data.length,
    skip,
    limit,
    has_more: response.data.length >= limit,
  };
}

/**
 * Create a new transcription
 */
export async function createTranscription(
  data: TranscriptionCreateRequest
): Promise<Transcription> {
  const response: AxiosResponse<Transcription> = await apiClient.post(
    TRANSCRIPTION_ENDPOINTS.CREATE,
    data
  );
  return response.data;
}

/**
 * Get a single transcription by ID
 */
export async function getTranscription(id: string): Promise<Transcription> {
  const response: AxiosResponse<Transcription> = await apiClient.get(
    TRANSCRIPTION_ENDPOINTS.GET(id)
  );
  return response.data;
}

/**
 * Get transcription statistics for the current user
 */
export async function getStats(): Promise<TranscriptionStats> {
  const response: AxiosResponse<TranscriptionStats> = await apiClient.get(
    TRANSCRIPTION_ENDPOINTS.STATS
  );
  return response.data;
}

/**
 * Upload a file for transcription
 */
export async function uploadTranscription(
  data: TranscriptionUploadRequest,
  onUploadProgress?: (progress: number) => void
): Promise<Transcription> {
  const formData = new FormData();
  formData.append('file', data.file);
  if (data.language) {
    formData.append('language', data.language);
  }

  const response: AxiosResponse<Transcription> = await apiClient.post(
    TRANSCRIPTION_ENDPOINTS.UPLOAD,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percent);
        }
      },
    }
  );
  return response.data;
}

/**
 * Delete a transcription
 */
export async function deleteTranscription(id: string): Promise<void> {
  await apiClient.delete(TRANSCRIPTION_ENDPOINTS.DELETE(id));
}

/* ========================================================================
   YOUTUBE ENHANCED API FUNCTIONS
   ======================================================================== */

/**
 * Smart transcribe a YouTube video using the best available provider
 */
export async function smartTranscribe(
  videoUrl: string,
  language: string = 'auto',
  preferProvider: string = 'auto'
): Promise<SmartTranscribeResponse> {
  const response = await apiClient.post(TRANSCRIPTION_ENDPOINTS.SMART_TRANSCRIBE, {
    video_url: videoUrl,
    language,
    prefer_provider: preferProvider,
  });
  return response.data;
}

/**
 * Extract metadata from a YouTube video
 */
export async function getMetadata(videoUrl: string): Promise<YouTubeMetadata> {
  const response = await apiClient.post(TRANSCRIPTION_ENDPOINTS.METADATA, {
    video_url: videoUrl,
  });
  return response.data;
}

/**
 * Transcribe all videos in a YouTube playlist
 */
export async function transcribePlaylist(
  playlistUrl: string,
  language: string = 'auto',
  maxVideos: number = 20
): Promise<PlaylistTranscribeResponse> {
  const response = await apiClient.post(TRANSCRIPTION_ENDPOINTS.PLAYLIST, {
    playlist_url: playlistUrl,
    language,
    max_videos: maxVideos,
  });
  return response.data;
}

/**
 * Auto-chapter a YouTube video with AI summaries
 */
export async function autoChapter(videoUrl: string): Promise<AutoChapterResponse> {
  const response = await apiClient.post(TRANSCRIPTION_ENDPOINTS.AUTO_CHAPTER, {
    video_url: videoUrl,
  });
  return response.data;
}

/**
 * Check the status of a live stream
 */
export async function checkStreamStatus(streamUrl: string): Promise<LiveStreamStatus> {
  const response = await apiClient.post(TRANSCRIPTION_ENDPOINTS.STREAM_STATUS, { stream_url: streamUrl });
  return response.data;
}

/**
 * Capture a segment of a live stream
 */
export async function captureStream(streamUrl: string, durationSeconds: number = 300): Promise<LiveStreamCapture> {
  const response = await apiClient.post(TRANSCRIPTION_ENDPOINTS.STREAM_CAPTURE, { stream_url: streamUrl, duration_seconds: durationSeconds });
  return response.data;
}

/**
 * Analyze video frames with AI Vision
 */
export async function analyzeVideo(videoUrl: string, intervalSeconds: number = 60, maxFrames: number = 10): Promise<VideoAnalyzeResponse> {
  const response = await apiClient.post(TRANSCRIPTION_ENDPOINTS.VIDEO_ANALYZE, { video_url: videoUrl, interval_seconds: intervalSeconds, max_frames: maxFrames });
  return response.data;
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export const transcriptionApi = {
  listTranscriptions,
  createTranscription,
  uploadTranscription,
  getTranscription,
  getStats,
  deleteTranscription,
  smartTranscribe,
  getMetadata,
  transcribePlaylist,
  autoChapter,
  checkStreamStatus,
  captureStream,
  analyzeVideo,
} as const;

export default transcriptionApi;

