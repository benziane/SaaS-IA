'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteProfile, dubContent, listBuiltinVoices, listProfiles, listSyntheses, synthesize } from '../api';
import type { BuiltinVoice, SpeechSynthesis, SynthesizeRequest, VoiceProfile } from '../types';

export function useVoiceProfiles() {
  return useQuery<VoiceProfile[]>({ queryKey: ['voice-profiles'], queryFn: listProfiles });
}
export function useDeleteProfile() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({ mutationFn: deleteProfile, onSuccess: () => qc.invalidateQueries({ queryKey: ['voice-profiles'] }) });
}
export function useSynthesize() {
  const qc = useQueryClient();
  return useMutation<SpeechSynthesis, Error, SynthesizeRequest>({
    mutationFn: synthesize,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['syntheses'] }),
  });
}
export function useSyntheses() {
  return useQuery<SpeechSynthesis[]>({ queryKey: ['syntheses'], queryFn: listSyntheses });
}
export function useBuiltinVoices(provider?: string) {
  return useQuery<BuiltinVoice[]>({ queryKey: ['builtin-voices', provider], queryFn: () => listBuiltinVoices(provider) });
}
export function useDub() {
  const qc = useQueryClient();
  return useMutation<SpeechSynthesis, Error, { source_type: string; source_id?: string; target_language: string }>({
    mutationFn: dubContent,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['syntheses'] }),
  });
}
