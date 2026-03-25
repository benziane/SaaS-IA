export interface AudioFile {
  id: string;
  user_id: string;
  filename: string;
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  format: string;
  file_size_kb: number;
  transcript: string | null;
  chapters: Chapter[];
  status: string;
  waveform_data: number[] | null;
  created_at: string;
}

export interface Chapter {
  title: string;
  start_time: number;
  end_time: number;
  description: string | null;
}

export interface AudioEditOperation {
  type: 'trim' | 'fade_in' | 'fade_out' | 'normalize' | 'noise_reduction' | 'speed_change' | 'merge';
  params: Record<string, unknown>;
}

export interface AudioEditRequest {
  operations: AudioEditOperation[];
}

export interface PodcastEpisode {
  id: string;
  user_id: string;
  audio_id: string;
  title: string;
  description: string;
  show_notes: string | null;
  publish_date: string | null;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface PodcastEpisodeCreateRequest {
  title: string;
  description?: string;
  audio_id: string;
  chapters?: Chapter[];
  show_notes?: string;
  publish_date?: string;
}

export interface RSSFeedConfig {
  title: string;
  description?: string;
  author?: string;
  email?: string;
  language?: string;
  category?: string;
  image_url?: string;
}

export interface WaveformResponse {
  audio_id: string;
  waveform: number[];
  points: number;
}

export interface SplitResponse {
  audio_id: string;
  segments: SplitSegment[];
  count: number;
}

export interface SplitSegment {
  index: number;
  start_seconds: number;
  end_seconds: number;
  duration_seconds: number;
  filename: string;
}

export interface ShowNotesResponse {
  audio_id: string;
  show_notes: {
    summary: string;
    key_points: string[];
    quotes: string[];
    resources: string[];
    guests: string[];
  };
}
