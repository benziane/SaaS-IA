/**
 * Conversation Types - Grade S++
 * Type definitions for conversation/chat feature
 */

/* ========================================================================
   MESSAGE
   ======================================================================== */

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  provider: string | null;
  created_at: string;
}

/* ========================================================================
   CONVERSATION
   ======================================================================== */

export interface Conversation {
  id: string;
  title: string | null;
  transcription_id: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationWithMessages extends Conversation {
  messages: Message[];
}

/* ========================================================================
   REQUESTS
   ======================================================================== */

export interface ConversationCreateRequest {
  transcription_id?: string;
}

/* ========================================================================
   RESPONSES
   ======================================================================== */

export interface ConversationListResponse {
  items: Conversation[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

/* ========================================================================
   FILTERS
   ======================================================================== */

export interface ConversationFilters {
  skip?: number;
  limit?: number;
}
