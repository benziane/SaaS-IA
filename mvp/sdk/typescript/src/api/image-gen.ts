import { BaseAPI } from "./base";
import {
  GeneratedImage,
  ImageGenerateRequest,
  ImageThumbnailRequest,
  ImageBulkRequest,
  ImageStyle,
  PaginationParams,
} from "../types";

/**
 * Image Gen API — AI image generation (10 styles) with optional
 * Real-ESRGAN upscaling.
 */
export class ImageGenAPI extends BaseAPI {
  // -- Generation ----------------------------------------------------------

  /** Generate an image from a prompt. */
  async generate(data: ImageGenerateRequest): Promise<GeneratedImage> {
    return this._post<GeneratedImage>("/api/images/generate", data);
  }

  /** Generate a YouTube thumbnail. */
  async thumbnail(data: ImageThumbnailRequest): Promise<GeneratedImage> {
    return this._post<GeneratedImage>("/api/images/thumbnail", data);
  }

  /** Bulk generate multiple images. */
  async bulk(data: ImageBulkRequest): Promise<GeneratedImage[]> {
    return this._post<GeneratedImage[]>("/api/images/bulk", data);
  }

  // -- CRUD ----------------------------------------------------------------

  /** List generated images. */
  async list(params?: PaginationParams): Promise<GeneratedImage[]> {
    return this._get<GeneratedImage[]>("/api/images/", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Delete an image. */
  async delete(id: string): Promise<void> {
    return this._delete(`/api/images/${id}`);
  }

  // -- Upscale -------------------------------------------------------------

  /** Upscale an image with Real-ESRGAN. */
  async upscale(id: string): Promise<GeneratedImage> {
    return this._post<GeneratedImage>(`/api/images/${id}/upscale`);
  }

  // -- Projects ------------------------------------------------------------

  /** Create an image project. */
  async createProject(data: { name: string; description?: string }): Promise<Record<string, unknown>> {
    return this._post("/api/images/projects", data);
  }

  /** List image projects. */
  async listProjects(params?: PaginationParams): Promise<Record<string, unknown>[]> {
    return this._get("/api/images/projects", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  // -- Reference -----------------------------------------------------------

  /** List available image styles. */
  async listStyles(): Promise<Array<{ id: ImageStyle; name: string; description: string }>> {
    return this._get("/api/images/styles");
  }
}
