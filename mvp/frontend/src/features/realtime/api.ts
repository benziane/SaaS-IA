import apiClient from '@/lib/apiClient';
import type { RealtimeSession, SessionCreateRequest } from './types';

export const createSession = async (data: SessionCreateRequest): Promise<RealtimeSession> => (await apiClient.post('/api/realtime/sessions', data)).data;
export const listSessions = async (): Promise<RealtimeSession[]> => (await apiClient.get('/api/realtime/sessions')).data;
export const getSession = async (id: string): Promise<RealtimeSession> => (await apiClient.get(`/api/realtime/sessions/${id}`)).data;
export const sendMessage = async (sessionId: string, content: string, contentType = 'text') =>
  (await apiClient.post(`/api/realtime/sessions/${sessionId}/message`, { content, content_type: contentType })).data;
export const endSession = async (id: string): Promise<RealtimeSession> => (await apiClient.post(`/api/realtime/sessions/${id}/end`)).data;
export const getTranscript = async (id: string) => (await apiClient.get(`/api/realtime/sessions/${id}/transcript`)).data;
export const getRealtimeConfig = async () => (await apiClient.get('/api/realtime/config')).data;
