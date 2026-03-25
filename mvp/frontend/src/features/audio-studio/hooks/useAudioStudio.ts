'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createEpisode,
  deleteAudio,
  editAudio,
  generateChapters,
  generateShowNotes,
  getAudio,
  getWaveform,
  listAudio,
  listEpisodes,
  splitAudio,
  transcribeAudio,
  uploadAudio,
} from '../api';
import type {
  AudioEditRequest,
  AudioFile,
  PodcastEpisode,
  PodcastEpisodeCreateRequest,
  ShowNotesResponse,
  SplitResponse,
  WaveformResponse,
} from '../types';

const KEYS = {
  audioList: ['audio-studio', 'list'] as const,
  audioDetail: (id: string) => ['audio-studio', 'detail', id] as const,
  waveform: (id: string) => ['audio-studio', 'waveform', id] as const,
  episodes: ['audio-studio', 'episodes'] as const,
};

/* -----------------------------------------------------------------------
   Audio file queries
   ----------------------------------------------------------------------- */

export function useAudioList() {
  return useQuery<AudioFile[]>({
    queryKey: KEYS.audioList,
    queryFn: () => listAudio(),
  });
}

export function useAudioDetail(id: string) {
  return useQuery<AudioFile>({
    queryKey: KEYS.audioDetail(id),
    queryFn: () => getAudio(id),
    enabled: !!id,
  });
}

export function useWaveform(id: string) {
  return useQuery<WaveformResponse>({
    queryKey: KEYS.waveform(id),
    queryFn: () => getWaveform(id),
    enabled: !!id,
  });
}

/* -----------------------------------------------------------------------
   Mutations
   ----------------------------------------------------------------------- */

export function useUploadAudio() {
  const qc = useQueryClient();
  return useMutation<AudioFile, Error, { file: File; onProgress?: (pct: number) => void }>({
    mutationFn: ({ file, onProgress }) => uploadAudio(file, onProgress),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.audioList }),
  });
}

export function useDeleteAudio() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteAudio,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.audioList }),
  });
}

export function useEditAudio() {
  const qc = useQueryClient();
  return useMutation<AudioFile, Error, { id: string; data: AudioEditRequest }>({
    mutationFn: ({ id, data }) => editAudio(id, data),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: KEYS.audioList });
      qc.invalidateQueries({ queryKey: KEYS.audioDetail(vars.id) });
    },
  });
}

export function useTranscribeAudio() {
  const qc = useQueryClient();
  return useMutation<AudioFile, Error, string>({
    mutationFn: transcribeAudio,
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: KEYS.audioDetail(id) });
    },
  });
}

export function useGenerateChapters() {
  const qc = useQueryClient();
  return useMutation<AudioFile, Error, string>({
    mutationFn: generateChapters,
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: KEYS.audioDetail(id) });
    },
  });
}

export function useGenerateShowNotes() {
  return useMutation<ShowNotesResponse, Error, string>({
    mutationFn: generateShowNotes,
  });
}

export function useSplitAudio() {
  return useMutation<SplitResponse, Error, { id: string; minSilenceMs?: number }>({
    mutationFn: ({ id, minSilenceMs }) => splitAudio(id, minSilenceMs),
  });
}

/* -----------------------------------------------------------------------
   Episode queries / mutations
   ----------------------------------------------------------------------- */

export function useEpisodeList() {
  return useQuery<PodcastEpisode[]>({
    queryKey: KEYS.episodes,
    queryFn: () => listEpisodes(),
  });
}

export function useCreateEpisode() {
  const qc = useQueryClient();
  return useMutation<PodcastEpisode, Error, PodcastEpisodeCreateRequest>({
    mutationFn: createEpisode,
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.episodes }),
  });
}
