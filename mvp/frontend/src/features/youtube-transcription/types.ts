export interface ValidateResult { valid: boolean; video_id: string | null; url: string; }
export interface TranscriptResult { video_id: string; text: string; language: string; duration_seconds: number; provider: string; is_manual: boolean; }
export interface YouTubeMetadata { video_id: string; title: string; uploader: string; duration_seconds: number; view_count: number; like_count: number; thumbnail?: string; is_live: boolean; description: string; tags: string[]; chapters: Array<{ start_time: number; title: string }>; }
export interface PlaylistVideoResult { video_id: string; title: string; success: boolean; transcript: string; provider: string; error?: string; }
export interface PlaylistResult { success: boolean; total: number; transcribed: number; results: PlaylistVideoResult[]; }
export interface StreamStatusResult { is_live: boolean; was_live: boolean; title: string; uploader: string; concurrent_viewers?: number; url: string; error?: string; }
export interface StreamCaptureResult { success: boolean; url: string; title: string; duration_seconds: number; capture_method: string; transcript?: string; provider?: string; error?: string; }
export interface VideoFrameResult { timestamp: number; description: string; }
export interface VideoAnalyzeResult { video_id: string; title: string; frames_analyzed: number; analyses: VideoFrameResult[]; summary: string; }
