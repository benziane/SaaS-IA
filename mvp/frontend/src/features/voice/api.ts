import apiClient from '@/lib/apiClient';
import type { BuiltinVoice, SpeechSynthesis, SynthesizeRequest, VoiceProfile } from './types';

export const listProfiles = async (): Promise<VoiceProfile[]> => (await apiClient.get('/api/voice/profiles')).data;
export const deleteProfile = async (id: string): Promise<void> => { await apiClient.delete(`/api/voice/profiles/${id}`); };
export const synthesize = async (data: SynthesizeRequest): Promise<SpeechSynthesis> => (await apiClient.post('/api/voice/synthesize', data)).data;
export const listSyntheses = async (): Promise<SpeechSynthesis[]> => (await apiClient.get('/api/voice/syntheses')).data;
export const listBuiltinVoices = async (provider?: string): Promise<BuiltinVoice[]> =>
  (await apiClient.get('/api/voice/voices', { params: provider ? { provider } : {} })).data;
export const dubContent = async (data: { source_type: string; source_id?: string; target_language: string; voice_id?: string }) =>
  (await apiClient.post('/api/voice/dub', data)).data as SpeechSynthesis;
