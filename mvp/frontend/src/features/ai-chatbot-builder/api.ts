/**
 * AI Chatbot Builder API
 */

import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type {
  ChannelConfig,
  Chatbot,
  ChatbotAnalytics,
  ChatbotCreateRequest,
  ChatbotUpdateRequest,
  ChatResponse,
  EmbedCode,
} from './types';

const ENDPOINTS = {
  CHATBOTS: '/api/chatbots',
  CHATBOT: (id: string) => `/api/chatbots/${id}`,
  PUBLISH: (id: string) => `/api/chatbots/${id}/publish`,
  UNPUBLISH: (id: string) => `/api/chatbots/${id}/unpublish`,
  CHANNELS: (id: string) => `/api/chatbots/${id}/channels`,
  CHANNEL: (id: string, type: string) => `/api/chatbots/${id}/channels/${type}`,
  ANALYTICS: (id: string) => `/api/chatbots/${id}/analytics`,
  EMBED_CODE: (id: string) => `/api/chatbots/${id}/embed-code`,
  PUBLIC_CHAT: (token: string) => `/api/chatbots/widget/${token}/chat`,
  PUBLIC_HISTORY: (token: string, sessionId: string) => `/api/chatbots/widget/${token}/history/${sessionId}`,
  PUBLIC_CONFIG: (token: string) => `/api/chatbots/widget/${token}/config`,
} as const;

export async function createChatbot(data: ChatbotCreateRequest): Promise<Chatbot> {
  const response: AxiosResponse<Chatbot> = await apiClient.post(ENDPOINTS.CHATBOTS, data);
  return response.data;
}

export async function listChatbots(): Promise<Chatbot[]> {
  const response: AxiosResponse<Chatbot[]> = await apiClient.get(ENDPOINTS.CHATBOTS);
  return response.data;
}

export async function getChatbot(id: string): Promise<Chatbot> {
  const response: AxiosResponse<Chatbot> = await apiClient.get(ENDPOINTS.CHATBOT(id));
  return response.data;
}

export async function updateChatbot(id: string, data: ChatbotUpdateRequest): Promise<Chatbot> {
  const response: AxiosResponse<Chatbot> = await apiClient.put(ENDPOINTS.CHATBOT(id), data);
  return response.data;
}

export async function deleteChatbot(id: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.CHATBOT(id));
}

export async function publishChatbot(id: string): Promise<Chatbot> {
  const response: AxiosResponse<Chatbot> = await apiClient.post(ENDPOINTS.PUBLISH(id));
  return response.data;
}

export async function unpublishChatbot(id: string): Promise<Chatbot> {
  const response: AxiosResponse<Chatbot> = await apiClient.post(ENDPOINTS.UNPUBLISH(id));
  return response.data;
}

export async function addChannel(id: string, config: ChannelConfig): Promise<Chatbot> {
  const response: AxiosResponse<Chatbot> = await apiClient.post(ENDPOINTS.CHANNELS(id), config);
  return response.data;
}

export async function removeChannel(id: string, channelType: string): Promise<Chatbot> {
  const response: AxiosResponse<Chatbot> = await apiClient.delete(ENDPOINTS.CHANNEL(id, channelType));
  return response.data;
}

export async function getAnalytics(id: string): Promise<ChatbotAnalytics> {
  const response: AxiosResponse<ChatbotAnalytics> = await apiClient.get(ENDPOINTS.ANALYTICS(id));
  return response.data;
}

export async function getEmbedCode(id: string): Promise<EmbedCode> {
  const response: AxiosResponse<EmbedCode> = await apiClient.get(ENDPOINTS.EMBED_CODE(id));
  return response.data;
}

export async function publicChat(
  embedToken: string,
  message: string,
  sessionId?: string,
): Promise<ChatResponse> {
  const response: AxiosResponse<ChatResponse> = await apiClient.post(
    ENDPOINTS.PUBLIC_CHAT(embedToken),
    { message, session_id: sessionId },
  );
  return response.data;
}
