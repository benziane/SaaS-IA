/**
 * Conversation Mutations - Grade S++
 * React Query mutations for conversations
 */

import { useMutation, useQueryClient, type UseMutationResult } from '@tanstack/react-query';
import { toast } from 'sonner';

import { extractErrorMessage } from '@/lib/apiClient';
import { queryKeys } from '@/lib/queryClient';

import { conversationApi } from '../api';
import type { Conversation } from '../types';

/* ========================================================================
   USE CREATE CONVERSATION
   ======================================================================== */

/**
 * Create conversation mutation
 */
export function useCreateConversation(): UseMutationResult<
  Conversation,
  Error,
  string | undefined
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (transcriptionId?: string) =>
      conversationApi.createConversation(transcriptionId),
    onSuccess: () => {
      // Invalidate list queries
      void queryClient.invalidateQueries({ queryKey: queryKeys.conversations.lists() });

      toast.success('Conversation created', {
        description: 'A new conversation has been started.',
      });
    },
    onError: (error: Error) => {
      toast.error('Failed to create conversation', {
        description: extractErrorMessage(error),
      });
    },
  });
}

/* ========================================================================
   USE DELETE CONVERSATION
   ======================================================================== */

/**
 * Delete conversation mutation
 */
export function useDeleteConversation(): UseMutationResult<void, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => conversationApi.deleteConversation(id),
    onSuccess: (_, id) => {
      // Invalidate list queries
      void queryClient.invalidateQueries({ queryKey: queryKeys.conversations.lists() });

      // Remove detail query
      void queryClient.removeQueries({ queryKey: queryKeys.conversations.detail(id) });

      toast.success('Conversation deleted', {
        description: 'The conversation has been removed.',
      });
    },
    onError: (error: Error) => {
      toast.error('Failed to delete conversation', {
        description: extractErrorMessage(error),
      });
    },
  });
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default {
  useCreateConversation,
  useDeleteConversation,
};
