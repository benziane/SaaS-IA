/**
 * Conversation API - Grade S++
 * API calls for conversation/chat feature
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type {
  Conversation,
  ConversationCreateRequest,
  ConversationListResponse,
  ConversationWithMessages,
} from './types';

/* ========================================================================
   API ENDPOINTS
   ======================================================================== */

const CONVERSATION_ENDPOINTS = {
  LIST: '/api/conversation',
  CREATE: '/api/conversation',
  GET: (id: string) => `/api/conversation/${id}`,
  DELETE: (id: string) => `/api/conversation/${id}`,
} as const;

/* ========================================================================
   API FUNCTIONS
   ======================================================================== */

/**
 * List conversations with pagination
 */
export async function listConversations(
  skip?: number,
  limit?: number
): Promise<ConversationListResponse> {
  const params = new URLSearchParams();

  if (skip !== undefined) {
    params.append('skip', skip.toString());
  }
  if (limit !== undefined) {
    params.append('limit', limit.toString());
  }

  const queryString = params.toString();
  const url = queryString
    ? `${CONVERSATION_ENDPOINTS.LIST}?${queryString}`
    : CONVERSATION_ENDPOINTS.LIST;

  // Backend returns a plain array; wrap into paginated format
  const response: AxiosResponse<Conversation[]> = await apiClient.get(url);

  const effectiveSkip = skip ?? 0;
  const effectiveLimit = limit ?? 100;
  return {
    items: response.data,
    total: response.data.length,
    skip: effectiveSkip,
    limit: effectiveLimit,
    has_more: response.data.length >= effectiveLimit,
  };
}

/**
 * Create a new conversation, optionally linked to a transcription
 */
export async function createConversation(
  transcriptionId?: string
): Promise<Conversation> {
  const body: ConversationCreateRequest = {};
  if (transcriptionId) {
    body.transcription_id = transcriptionId;
  }

  const response: AxiosResponse<Conversation> = await apiClient.post(
    CONVERSATION_ENDPOINTS.CREATE,
    body
  );
  return response.data;
}

/**
 * Get a single conversation with its messages
 */
export async function getConversation(
  id: string
): Promise<ConversationWithMessages> {
  const response: AxiosResponse<ConversationWithMessages> = await apiClient.get(
    CONVERSATION_ENDPOINTS.GET(id)
  );
  return response.data;
}

/**
 * Delete a conversation
 */
export async function deleteConversation(id: string): Promise<void> {
  await apiClient.delete(CONVERSATION_ENDPOINTS.DELETE(id));
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export const conversationApi = {
  listConversations,
  createConversation,
  getConversation,
  deleteConversation,
} as const;

export default conversationApi;
