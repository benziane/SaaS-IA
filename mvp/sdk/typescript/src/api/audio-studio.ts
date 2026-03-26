import { BaseAPI } from "./base";
import { AudioResult, PaginationParams } from "../types";

/**
 * Audio Studio API — audio editing with pydub + noisereduce (stub).
 */
export class AudioStudioAPI extends BaseAPI {
  /** Upload an audio file for processing. */
  async upload(file: Blob | File): Promise<AudioResult> {
    const form = new FormData();
    form.append("file", file);
    return this._request<AudioResult>("/api/audio/upload", {
      method: "POST",
      body: form,
    });
  }

  /** List processed audio files. */
  async list(params?: PaginationParams): Promise<AudioResult[]> {
    return this._get<AudioResult[]>("/api/audio/", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get audio result. */
  async get(id: string): Promise<AudioResult> {
    return this._get<AudioResult>(`/api/audio/${id}`);
  }

  /** Delete an audio file. */
  async delete(id: string): Promise<void> {
    return this._delete(`/api/audio/${id}`);
  }
}
