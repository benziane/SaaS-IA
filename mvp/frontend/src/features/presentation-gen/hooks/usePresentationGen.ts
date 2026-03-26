/**
 * Presentation Gen hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  addSlide,
  createPresentation,
  deletePresentation,
  exportPresentation,
  generateFromTranscript,
  getPresentation,
  getTemplates,
  listPresentations,
  removeSlide,
  updateSlide,
} from '../api';
import type {
  ExportRequest,
  Presentation,
  PresentationCreateRequest,
  PresentationFromTranscriptRequest,
  SlideInsertRequest,
  SlideUpdateRequest,
} from '../types';

const QUERY_KEY = 'presentation-gen';

export function usePresentations() {
  return useQuery<Presentation[]>({
    queryKey: [QUERY_KEY, 'list'],
    queryFn: listPresentations,
  });
}

export function usePresentation(id: string | null) {
  return useQuery<Presentation>({
    queryKey: [QUERY_KEY, 'detail', id],
    queryFn: () => getPresentation(id!),
    enabled: !!id,
  });
}

export function useCreatePresentation() {
  const queryClient = useQueryClient();
  return useMutation<Presentation, Error, PresentationCreateRequest>({
    mutationFn: createPresentation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, 'list'] });
    },
  });
}

export function useDeletePresentation() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deletePresentation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, 'list'] });
    },
  });
}

export function useUpdateSlide(presentationId: string) {
  const queryClient = useQueryClient();
  return useMutation<Presentation, Error, { slideNumber: number; data: SlideUpdateRequest }>({
    mutationFn: ({ slideNumber, data }) => updateSlide(presentationId, slideNumber, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, 'detail', presentationId] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, 'list'] });
    },
  });
}

export function useAddSlide(presentationId: string) {
  const queryClient = useQueryClient();
  return useMutation<Presentation, Error, { afterSlide: number; data: SlideInsertRequest }>({
    mutationFn: ({ afterSlide, data }) => addSlide(presentationId, afterSlide, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, 'detail', presentationId] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, 'list'] });
    },
  });
}

export function useRemoveSlide(presentationId: string) {
  const queryClient = useQueryClient();
  return useMutation<Presentation, Error, number>({
    mutationFn: (slideNumber) => removeSlide(presentationId, slideNumber),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, 'detail', presentationId] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, 'list'] });
    },
  });
}

export function useExportPresentation(presentationId: string) {
  return useMutation({
    mutationFn: (data: ExportRequest) => exportPresentation(presentationId, data),
  });
}

export function useGenerateFromTranscript() {
  const queryClient = useQueryClient();
  return useMutation<Presentation, Error, PresentationFromTranscriptRequest>({
    mutationFn: generateFromTranscript,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, 'list'] });
    },
  });
}

export function useTemplates() {
  return useQuery({
    queryKey: [QUERY_KEY, 'templates'],
    queryFn: getTemplates,
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}
