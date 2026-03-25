'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteVideo, generateAvatar, generateClips, generateVideo, listVideos, listVideoTypes } from '../api';
import type { GeneratedVideo, GenerateVideoRequest } from '../types';

export function useVideos() { return useQuery<GeneratedVideo[]>({ queryKey: ['videos'], queryFn: listVideos }); }
export function useGenerateVideo() {
  const qc = useQueryClient();
  return useMutation<GeneratedVideo, Error, GenerateVideoRequest>({ mutationFn: generateVideo, onSuccess: () => qc.invalidateQueries({ queryKey: ['videos'] }) });
}
export function useGenerateClips() {
  const qc = useQueryClient();
  return useMutation<GeneratedVideo[], Error, { transcription_id: string; max_clips?: number; format?: string }>({
    mutationFn: generateClips, onSuccess: () => qc.invalidateQueries({ queryKey: ['videos'] }),
  });
}
export function useGenerateAvatar() {
  const qc = useQueryClient();
  return useMutation<GeneratedVideo, Error, { text: string; avatar_style?: string; background?: string }>({
    mutationFn: generateAvatar, onSuccess: () => qc.invalidateQueries({ queryKey: ['videos'] }),
  });
}
export function useDeleteVideo() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({ mutationFn: deleteVideo, onSuccess: () => qc.invalidateQueries({ queryKey: ['videos'] }) });
}
export function useVideoTypes() { return useQuery({ queryKey: ['video-types'], queryFn: listVideoTypes, staleTime: 3600000 }); }
