/**
 * AI Chatbot Builder hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  addChannel,
  createChatbot,
  deleteChatbot,
  getAnalytics,
  getChatbot,
  getEmbedCode,
  listChatbots,
  publishChatbot,
  removeChannel,
  unpublishChatbot,
  updateChatbot,
} from '../api';
import type {
  ChannelConfig,
  Chatbot,
  ChatbotAnalytics,
  ChatbotCreateRequest,
  ChatbotUpdateRequest,
  EmbedCode,
} from '../types';

export function useChatbots() {
  return useQuery<Chatbot[]>({
    queryKey: ['chatbots'],
    queryFn: listChatbots,
  });
}

export function useChatbot(id: string | null) {
  return useQuery<Chatbot>({
    queryKey: ['chatbots', id],
    queryFn: () => getChatbot(id!),
    enabled: !!id,
  });
}

export function useCreateChatbot() {
  const queryClient = useQueryClient();
  return useMutation<Chatbot, Error, ChatbotCreateRequest>({
    mutationFn: createChatbot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] });
    },
  });
}

export function useUpdateChatbot() {
  const queryClient = useQueryClient();
  return useMutation<Chatbot, Error, { id: string; data: ChatbotUpdateRequest }>({
    mutationFn: ({ id, data }) => updateChatbot(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] });
    },
  });
}

export function useDeleteChatbot() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteChatbot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] });
    },
  });
}

export function usePublishChatbot() {
  const queryClient = useQueryClient();
  return useMutation<Chatbot, Error, string>({
    mutationFn: publishChatbot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] });
    },
  });
}

export function useUnpublishChatbot() {
  const queryClient = useQueryClient();
  return useMutation<Chatbot, Error, string>({
    mutationFn: unpublishChatbot,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] });
    },
  });
}

export function useAddChannel() {
  const queryClient = useQueryClient();
  return useMutation<Chatbot, Error, { id: string; config: ChannelConfig }>({
    mutationFn: ({ id, config }) => addChannel(id, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] });
    },
  });
}

export function useRemoveChannel() {
  const queryClient = useQueryClient();
  return useMutation<Chatbot, Error, { id: string; channelType: string }>({
    mutationFn: ({ id, channelType }) => removeChannel(id, channelType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatbots'] });
    },
  });
}

export function useChatbotAnalytics(id: string | null) {
  return useQuery<ChatbotAnalytics>({
    queryKey: ['chatbots', id, 'analytics'],
    queryFn: () => getAnalytics(id!),
    enabled: !!id,
  });
}

export function useEmbedCode(id: string | null) {
  return useQuery<EmbedCode>({
    queryKey: ['chatbots', id, 'embed-code'],
    queryFn: () => getEmbedCode(id!),
    enabled: !!id,
  });
}
