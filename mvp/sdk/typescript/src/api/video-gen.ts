import { BaseAPI } from "./base";
import {
  GeneratedVideo,
  VideoGenerateRequest,
  VideoClipsRequest,
  VideoAvatarRequest,
  VideoFromSourceRequest,
  VideoType,
  PaginationParams,
} from "../types";

/**
 * Video Gen API — text-to-video generation (6 types) with ffmpeg processing.
 */
export class VideoGenAPI extends BaseAPI {
  // -- Generation ----------------------------------------------------------

  /** Generate a video from a text prompt. */
  async generate(data: VideoGenerateRequest): Promise<GeneratedVideo> {
    return this._post<GeneratedVideo>("/api/videos/generate", data);
  }

  /** Generate highlight clips from a transcription. */
  async clips(data: VideoClipsRequest): Promise<GeneratedVideo[]> {
    return this._post<GeneratedVideo[]>("/api/videos/clips", data);
  }

  /** Generate a talking avatar video. */
  async avatar(data: VideoAvatarRequest): Promise<GeneratedVideo> {
    return this._post<GeneratedVideo>("/api/videos/avatar", data);
  }

  /** Generate video from a transcription or document. */
  async fromSource(data: VideoFromSourceRequest): Promise<GeneratedVideo> {
    return this._post<GeneratedVideo>("/api/videos/from-source", data);
  }

  // -- CRUD ----------------------------------------------------------------

  /** List generated videos. */
  async list(params?: PaginationParams): Promise<GeneratedVideo[]> {
    return this._get<GeneratedVideo[]>("/api/videos/", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Delete a video. */
  async delete(id: string): Promise<void> {
    return this._delete(`/api/videos/${id}`);
  }

  // -- Projects ------------------------------------------------------------

  /** Create a video project. */
  async createProject(data: { name: string; description?: string }): Promise<Record<string, unknown>> {
    return this._post("/api/videos/projects", data);
  }

  /** List video projects. */
  async listProjects(params?: PaginationParams): Promise<Record<string, unknown>[]> {
    return this._get("/api/videos/projects", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  // -- Reference -----------------------------------------------------------

  /** List available video types. */
  async listTypes(): Promise<Array<{ id: VideoType; name: string; description: string }>> {
    return this._get("/api/videos/types");
  }
}
