import apiClient from '@/lib/apiClient';
import type {
  AudioEditRequest,
  AudioFile,
  PodcastEpisode,
  PodcastEpisodeCreateRequest,
  RSSFeedConfig,
  ShowNotesResponse,
  SplitResponse,
  WaveformResponse,
} from './types';

const BASE = '/api/audio-studio';

/* ========================================================================
   Audio Files
   ======================================================================== */

export const uploadAudio = async (
  file: File,
  onProgress?: (pct: number) => void,
): Promise<AudioFile> => {
  const formData = new FormData();
  formData.append('file', file);
  const resp = await apiClient.post(`${BASE}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total));
    },
  });
  return resp.data;
};

export const listAudio = async (skip = 0, limit = 50): Promise<AudioFile[]> =>
  (await apiClient.get(BASE, { params: { skip, limit } })).data;

export const getAudio = async (id: string): Promise<AudioFile> =>
  (await apiClient.get(`${BASE}/${id}`)).data;

export const deleteAudio = async (id: string): Promise<void> => {
  await apiClient.delete(`${BASE}/${id}`);
};

/* ========================================================================
   Editing
   ======================================================================== */

export const editAudio = async (id: string, data: AudioEditRequest): Promise<AudioFile> =>
  (await apiClient.post(`${BASE}/${id}/edit`, data)).data;

/* ========================================================================
   AI Features
   ======================================================================== */

export const transcribeAudio = async (id: string): Promise<AudioFile> =>
  (await apiClient.post(`${BASE}/${id}/transcribe`)).data;

export const generateChapters = async (id: string): Promise<AudioFile> =>
  (await apiClient.post(`${BASE}/${id}/chapters`)).data;

export const generateShowNotes = async (id: string): Promise<ShowNotesResponse> =>
  (await apiClient.post(`${BASE}/${id}/show-notes`)).data;

export const getWaveform = async (id: string): Promise<WaveformResponse> =>
  (await apiClient.get(`${BASE}/${id}/waveform`)).data;

export const splitAudio = async (
  id: string,
  minSilenceMs = 1000,
  silenceThreshDb = -40,
): Promise<SplitResponse> =>
  (await apiClient.post(`${BASE}/${id}/split`, { min_silence_ms: minSilenceMs, silence_thresh_db: silenceThreshDb })).data;

/* ========================================================================
   Export
   ======================================================================== */

export const getExportUrl = (id: string, format: string): string =>
  `${BASE}/${id}/export/${format}`;

/* ========================================================================
   Podcast Episodes
   ======================================================================== */

export const createEpisode = async (data: PodcastEpisodeCreateRequest): Promise<PodcastEpisode> =>
  (await apiClient.post(`${BASE}/episodes`, data)).data;

export const listEpisodes = async (skip = 0, limit = 50): Promise<PodcastEpisode[]> =>
  (await apiClient.get(`${BASE}/episodes`, { params: { skip, limit } })).data;

/* ========================================================================
   RSS Feed
   ======================================================================== */

export const generateRSSFeed = async (config: RSSFeedConfig): Promise<string> =>
  (await apiClient.post(`${BASE}/rss-feed`, config, { responseType: 'text' })).data;

/* ========================================================================
   Aggregate Export
   ======================================================================== */

export const audioStudioApi = {
  uploadAudio,
  listAudio,
  getAudio,
  deleteAudio,
  editAudio,
  transcribeAudio,
  generateChapters,
  generateShowNotes,
  getWaveform,
  splitAudio,
  getExportUrl,
  createEpisode,
  listEpisodes,
  generateRSSFeed,
} as const;

export default audioStudioApi;
