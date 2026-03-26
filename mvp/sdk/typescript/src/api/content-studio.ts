import { BaseAPI } from "./base";
import {
  ContentProject,
  ContentPiece,
  ContentProjectCreateRequest,
  ContentGenerateRequest,
  ContentFromUrlRequest,
  ContentFormat,
  PaginationParams,
} from "../types";

/**
 * Content Studio API — multi-format content generation (10 formats)
 * from topics, source text, or crawled URLs.
 */
export class ContentStudioAPI extends BaseAPI {
  // -- Projects ------------------------------------------------------------

  /** Create a content project. */
  async createProject(data: ContentProjectCreateRequest): Promise<ContentProject> {
    return this._post<ContentProject>("/api/content-studio/projects", data);
  }

  /** List content projects. */
  async listProjects(params?: PaginationParams): Promise<ContentProject[]> {
    return this._get<ContentProject[]>("/api/content-studio/projects", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Delete a project and all its content pieces. */
  async deleteProject(id: string): Promise<void> {
    return this._delete(`/api/content-studio/projects/${id}`);
  }

  // -- Content generation --------------------------------------------------

  /** Generate content in one or more formats for a project. */
  async generate(projectId: string, data: ContentGenerateRequest): Promise<ContentPiece[]> {
    return this._post<ContentPiece[]>(
      `/api/content-studio/projects/${projectId}/generate`,
      data
    );
  }

  /** Get all content pieces for a project. */
  async listContents(projectId: string): Promise<ContentPiece[]> {
    return this._get<ContentPiece[]>(
      `/api/content-studio/projects/${projectId}/contents`
    );
  }

  /** Update a content piece. */
  async updateContent(id: string, data: { content?: string; metadata?: Record<string, unknown> }): Promise<ContentPiece> {
    return this._put<ContentPiece>(`/api/content-studio/contents/${id}`, data);
  }

  /** Regenerate a content piece. */
  async regenerateContent(id: string): Promise<ContentPiece> {
    return this._post<ContentPiece>(`/api/content-studio/contents/${id}/regenerate`);
  }

  // -- URL-based generation ------------------------------------------------

  /** Crawl a URL and generate content from its text. */
  async fromUrl(data: ContentFromUrlRequest): Promise<ContentPiece[]> {
    return this._post<ContentPiece[]>("/api/content-studio/from-url", data);
  }

  // -- Reference data ------------------------------------------------------

  /** List available content formats. */
  async listFormats(): Promise<Array<{ id: ContentFormat; name: string; description: string }>> {
    return this._get("/api/content-studio/formats");
  }
}
