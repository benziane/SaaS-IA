'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createSession, endSession, getRealtimeConfig, getTranscript, listSessions, sendMessage } from '../api';
import type { RealtimeSession, SessionCreateRequest } from '../types';

export function useRealtimeSessions() {
  return useQuery<RealtimeSession[]>({ queryKey: ['realtime-sessions'], queryFn: listSessions });
}
export function useCreateSession() {
  const qc = useQueryClient();
  return useMutation<RealtimeSession, Error, SessionCreateRequest>({
    mutationFn: createSession,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['realtime-sessions'] }),
  });
}
export function useSendMessage(sessionId: string) {
  const qc = useQueryClient();
  return useMutation<Record<string, unknown>, Error, string>({
    mutationFn: (content) => sendMessage(sessionId, content),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['realtime-sessions'] }),
  });
}
export function useEndSession() {
  const qc = useQueryClient();
  return useMutation<RealtimeSession, Error, string>({
    mutationFn: endSession,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['realtime-sessions'] }),
  });
}
export function useTranscript(sessionId: string | null) {
  return useQuery({ queryKey: ['realtime-transcript', sessionId], queryFn: () => getTranscript(sessionId!), enabled: !!sessionId });
}
export function useRealtimeConfig() {
  return useQuery({ queryKey: ['realtime-config'], queryFn: getRealtimeConfig, staleTime: 60 * 60 * 1000 });
}
