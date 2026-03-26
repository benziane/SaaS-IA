import { BaseAPI } from "./base";
import {
  Transcription,
  TranscriptionCreateRequest,
  SmartTranscribeRequest,
  SmartTranscribeResponse,
  TranscriptionWithSpeakers,
  Chapter,
  Summary,
  Keyword,
  SearchTranscriptionResult,
  BatchTranscribeResponse,
  YouTubeMetadata,
  PlaylistTranscribeRequest,
  PlaylistTranscribeResponse,
  LiveStreamStatusResponse,
  LiveStreamCaptureRequest,
  LiveStreamCaptureResponse,
  VideoAnalyzeRequest,
  VideoAnalyzeResponse,
  PaginatedResponse,
  PaginationParams,
} from "../types";

/**
 * Transcription API — YouTube / audio / video transcription with speaker
 * diarization, chaptering, export, batch processing and live-stream capture.
 */
export class TranscriptionAPI extends BaseAPI {
  // -- CRUD ----------------------------------------------------------------

  /** Create a transcription job from a URL (YouTube, audio, video). */
  async create(data: TranscriptionCreateRequest): Promise<Transcription> {
    return this._post<Transcription>("/api/transcription/", data);
  }

  /** Upload an audio/video file for transcription. */
  async upload(file: Blob | File, language?: string): Promise<Transcription> {
    const form = new FormData();
    form.append("file", file);
    if (language) form.append("language", language);
    return this._request<Transcription>("/api/transcription/upload", {
      method: "POST",
      body: form,
    });
  }

  /** List transcriptions (paginated). */
  async list(params?: PaginationParams): Promise<PaginatedResponse<Transcription>> {
    return this._get<PaginatedResponse<Transcription>>("/api/transcription/", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get transcription by ID. */
  async get(id: string): Promise<Transcription> {
    return this._get<Transcription>(`/api/transcription/${id}`);
  }

  /** Delete a transcription. */
  async delete(id: string): Promise<void> {
    return this._delete(`/api/transcription/${id}`);
  }

  /** Get transcription statistics. */
  async stats(): Promise<Record<string, unknown>> {
    return this._get<Record<string, unknown>>("/api/transcription/stats");
  }

  // -- Speaker diarization ------------------------------------------------

  /** Get transcription with speaker diarization. */
  async speakers(id: string): Promise<TranscriptionWithSpeakers> {
    return this._get<TranscriptionWithSpeakers>(`/api/transcription/${id}/speakers`);
  }

  // -- Smart transcription ------------------------------------------------

  /** Smart transcription with automatic provider routing. */
  async smartTranscribe(data: SmartTranscribeRequest): Promise<SmartTranscribeResponse> {
    return this._post<SmartTranscribeResponse>("/api/transcription/smart-transcribe", data);
  }

  // -- Chaptering & summary -----------------------------------------------

  /** Auto-generate chapters with summaries. */
  async chapters(id: string): Promise<{ chapters: Chapter[] }> {
    return this._post<{ chapters: Chapter[] }>("/api/transcription/auto-chapter", {
      transcription_id: id,
    });
  }

  /** Generate a summary of a transcription. */
  async summary(id: string, style?: string): Promise<Summary> {
    return this._post<Summary>(`/api/transcription/${id}/summary`, { style });
  }

  /** Extract keywords from a transcription. */
  async keywords(id: string): Promise<Keyword[]> {
    return this._get<Keyword[]>(`/api/transcription/${id}/keywords`);
  }

  // -- Export --------------------------------------------------------------

  /** Export transcription in the given format. */
  async export(id: string, format: "srt" | "vtt" | "txt" | "md" | "json"): Promise<string> {
    return this._get<string>(`/api/transcription/${id}/export`, { format });
  }

  // -- Batch ---------------------------------------------------------------

  /** Submit batch transcription jobs. */
  async batch(urls: string[]): Promise<BatchTranscribeResponse> {
    return this._post<BatchTranscribeResponse>("/api/transcription/batch", { urls });
  }

  // -- Metadata ------------------------------------------------------------

  /** Extract YouTube video metadata. */
  async metadata(url: string): Promise<YouTubeMetadata> {
    return this._post<YouTubeMetadata>("/api/transcription/metadata", { url });
  }

  // -- Playlist ------------------------------------------------------------

  /** Transcribe an entire YouTube playlist. */
  async playlist(data: PlaylistTranscribeRequest): Promise<PlaylistTranscribeResponse> {
    return this._post<PlaylistTranscribeResponse>("/api/transcription/playlist", data);
  }

  // -- Live stream ---------------------------------------------------------

  /** Check if a live stream is active. */
  async streamStatus(url: string): Promise<LiveStreamStatusResponse> {
    return this._post<LiveStreamStatusResponse>("/api/transcription/stream/status", { url });
  }

  /** Capture a segment of a live stream. */
  async streamCapture(data: LiveStreamCaptureRequest): Promise<LiveStreamCaptureResponse> {
    return this._post<LiveStreamCaptureResponse>("/api/transcription/stream/capture", data);
  }

  // -- Video analysis ------------------------------------------------------

  /** Analyze video frames with Vision AI. */
  async analyzeVideo(data: VideoAnalyzeRequest): Promise<VideoAnalyzeResponse> {
    return this._post<VideoAnalyzeResponse>("/api/transcription/video/analyze", data);
  }

  // -- Search --------------------------------------------------------------

  /** Search across all transcriptions. */
  async search(query: string, limit?: number): Promise<SearchTranscriptionResult[]> {
    return this._get<SearchTranscriptionResult[]>("/api/transcription/search", {
      query,
      limit,
    });
  }
}
