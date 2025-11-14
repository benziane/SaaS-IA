/**
 * Transcription Mutations - Grade S++
 * React Query mutations for transcriptions
 */

import { useMutation, useQueryClient, type UseMutationResult } from '@tanstack/react-query';
import { toast } from 'sonner';

import { extractErrorMessage } from '@/lib/apiClient';
import { queryKeys } from '@/lib/queryClient';

import { transcriptionApi } from '../api';
import type { Transcription, TranscriptionCreateRequest } from '../types';

/* ========================================================================
   USE CREATE TRANSCRIPTION
   ======================================================================== */

/**
 * Create transcription mutation
 */
export function useCreateTranscription(): UseMutationResult<
  Transcription,
  Error,
  TranscriptionCreateRequest
> {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: TranscriptionCreateRequest) => transcriptionApi.createTranscription(data),
    onSuccess: (created) => {
      // Invalidate list queries
      void queryClient.invalidateQueries({ queryKey: queryKeys.transcriptions.lists() });
      
      toast.success('Transcription started', {
        description: `Processing: ${created.video_url}`,
      });
    },
    onError: (error: Error) => {
      toast.error('Failed to start transcription', {
        description: extractErrorMessage(error),
      });
    },
  });
}

/* ========================================================================
   USE DELETE TRANSCRIPTION
   ======================================================================== */

/**
 * Delete transcription mutation
 */
export function useDeleteTranscription(): UseMutationResult<void, Error, string> {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => transcriptionApi.deleteTranscription(id),
    onSuccess: (_, id) => {
      // Invalidate list queries
      void queryClient.invalidateQueries({ queryKey: queryKeys.transcriptions.lists() });
      
      // Remove detail query
      void queryClient.removeQueries({ queryKey: queryKeys.transcriptions.detail(id) });
      
      toast.success('Transcription deleted', {
        description: 'The transcription has been removed.',
      });
    },
    onError: (error: Error) => {
      toast.error('Failed to delete transcription', {
        description: extractErrorMessage(error),
      });
    },
  });
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default {
  useCreateTranscription,
  useDeleteTranscription,
};

