'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteImage, generateImage, generateThumbnail, listImages, listStyles } from '../api';
import type { GeneratedImage, GenerateImageRequest } from '../types';

export function useImages() { return useQuery<GeneratedImage[]>({ queryKey: ['images'], queryFn: listImages }); }
export function useGenerateImage() {
  const qc = useQueryClient();
  return useMutation<GeneratedImage, Error, GenerateImageRequest>({ mutationFn: generateImage, onSuccess: () => qc.invalidateQueries({ queryKey: ['images'] }) });
}
export function useGenerateThumbnail() {
  const qc = useQueryClient();
  return useMutation<GeneratedImage, Error, { source_type: string; source_id?: string; text?: string; style?: string }>({
    mutationFn: generateThumbnail, onSuccess: () => qc.invalidateQueries({ queryKey: ['images'] }),
  });
}
export function useDeleteImage() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({ mutationFn: deleteImage, onSuccess: () => qc.invalidateQueries({ queryKey: ['images'] }) });
}
export function useImageStyles() { return useQuery({ queryKey: ['image-styles'], queryFn: listStyles, staleTime: 3600000 }); }
