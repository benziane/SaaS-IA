/**
 * Conversation Hooks - Grade S++
 * React Query hooks for conversations
 */

import { useQuery, type UseQueryResult } from '@tanstack/react-query';

import { QUERY_STALE_TIME, queryKeys } from '@/lib/queryClient';

import { conversationApi } from '../api';
import type { ConversationListResponse, ConversationWithMessages } from '../types';

/* ========================================================================
   USE CONVERSATIONS
   ======================================================================== */

/**
 * List conversations with pagination and polling
 */
export function useConversations(
  skip?: number,
  limit?: number
): UseQueryResult<ConversationListResponse, Error> {
  return useQuery({
    queryKey: queryKeys.conversations.list({ skip, limit }),
    queryFn: () => conversationApi.listConversations(skip, limit),
    staleTime: QUERY_STALE_TIME.CRITICAL, // 30 seconds - conversations can change often
    refetchInterval: 10000, // Poll every 10 seconds for list updates
  });
}

/* ========================================================================
   USE CONVERSATION
   ======================================================================== */

/**
 * Get a single conversation with its messages
 */
export function useConversation(
  id: string
): UseQueryResult<ConversationWithMessages, Error> {
  return useQuery({
    queryKey: queryKeys.conversations.detail(id),
    queryFn: () => conversationApi.getConversation(id),
    staleTime: QUERY_STALE_TIME.CRITICAL,
    enabled: !!id,
  });
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default {
  useConversations,
  useConversation,
};
