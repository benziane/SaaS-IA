import apiClient from '@/lib/apiClient';

import type {
  PlaylistResult,
  StreamCaptureResult,
  StreamStatusResult,
  TranscriptResult,
  ValidateResult,
  VideoAnalyzeResult,
  YouTubeMetadata,
} from './types';

export const validateYouTube = (url: string) =>
  apiClient.post<ValidateResult>('/api/youtube/validate', { video_url: url }).then(r => r.data);

export const getYouTubeMetadata = (url: string) =>
  apiClient.post<YouTubeMetadata>('/api/youtube/metadata', { video_url: url }).then(r => r.data);

export const getYouTubeTranscript = (url: string, language = 'auto') =>
  apiClient.post<TranscriptResult>('/api/youtube/transcript', { video_url: url, language }).then(r => r.data);

export const smartTranscribeYT = (url: string, language = 'auto') =>
  apiClient.post<TranscriptResult>('/api/youtube/smart', { video_url: url, language }).then(r => r.data);

export const transcribeYTPlaylist = (url: string, language = 'auto', max_videos = 50) =>
  apiClient.post<PlaylistResult>('/api/youtube/playlist', { playlist_url: url, language, max_videos }).then(r => r.data);

export const checkYTStreamStatus = (url: string) =>
  apiClient.post<StreamStatusResult>('/api/youtube/stream/status', { stream_url: url }).then(r => r.data);

export const captureYTStream = (url: string, duration_seconds = 300) =>
  apiClient.post<StreamCaptureResult>('/api/youtube/stream/capture', { stream_url: url, duration_seconds }).then(r => r.data);

export const analyzeYTVideo = (url: string) =>
  apiClient.post<VideoAnalyzeResult>('/api/youtube/analyze', { video_url: url, interval_seconds: 30, max_frames: 10, prompt: 'Describe what is happening in this video frame' }).then(r => r.data);
