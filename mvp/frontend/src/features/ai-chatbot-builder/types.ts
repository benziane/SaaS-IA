/**
 * AI Chatbot Builder Types
 */

export interface Chatbot {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  system_prompt: string;
  model: string;
  knowledge_base_ids: string[] | null;
  personality: string;
  welcome_message: string | null;
  theme: Record<string, unknown> | null;
  is_published: boolean;
  embed_token: string | null;
  channels: ChannelConfig[];
  conversations_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatbotCreateRequest {
  name: string;
  description?: string;
  system_prompt: string;
  model?: string;
  knowledge_base_ids?: string[];
  personality?: string;
  welcome_message?: string;
  theme?: Record<string, unknown>;
}

export interface ChatbotUpdateRequest {
  name?: string;
  description?: string;
  system_prompt?: string;
  model?: string;
  personality?: string;
  welcome_message?: string;
  theme?: Record<string, unknown>;
}

export interface ChatMessageCreate {
  message: string;
  session_id?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[] | null;
  created_at: string;
}

export interface ChatSource {
  filename: string;
  content: string;
  score: number;
}

export interface ChatResponse {
  session_id: string;
  message: ChatMessage;
  sources: ChatSource[];
}

export interface ChannelConfig {
  type: 'web_widget' | 'whatsapp' | 'telegram' | 'slack' | 'api';
  config: Record<string, unknown>;
  is_active: boolean;
}

export interface ChatbotAnalytics {
  chatbot_id: string;
  total_conversations: number;
  total_messages: number;
  avg_messages_per_conversation: number;
  satisfaction_score: number | null;
  top_questions: { question: string; count: number }[];
}

export interface EmbedCode {
  embed_token: string;
  html_snippet: string;
  script_url: string;
}

export interface WidgetConfig {
  name: string;
  welcome_message: string | null;
  theme: Record<string, unknown> | null;
  personality: string;
}
