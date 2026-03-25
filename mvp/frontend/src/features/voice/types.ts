export interface VoiceProfile {
  id: string; user_id: string; name: string; description: string | null;
  provider: string; language: string; sample_duration_s: number | null;
  status: string; settings_json: string; created_at: string; updated_at: string;
}
export interface SpeechSynthesis {
  id: string; user_id: string; voice_id: string | null; source_type: string;
  provider: string; output_format: string; audio_url: string | null;
  duration_s: number | null; language: string; target_language: string | null;
  status: string; error: string | null; created_at: string; updated_at: string;
}
export interface BuiltinVoice {
  id: string; name: string; language: string; gender: string; provider: string;
  preview_url?: string;
}
export interface SynthesizeRequest {
  text: string; voice_id?: string; provider?: string;
  output_format?: string; language?: string; speed?: number;
}
