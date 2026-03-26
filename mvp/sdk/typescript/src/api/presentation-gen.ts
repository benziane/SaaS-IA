import { BaseAPI } from "./base";
import {
  Presentation,
  PresentationCreateRequest,
  PresentationFromTranscriptRequest,
  PresentationExportRequest,
  PresentationSlide,
  PresentationTemplate,
  PaginationParams,
} from "../types";

/**
 * Presentation Gen API — AI slide generation with 5 templates,
 * export to HTML/MD/PDF.
 */
export class PresentationGenAPI extends BaseAPI {
  // -- CRUD ----------------------------------------------------------------

  /** Generate a presentation from a topic. */
  async create(data: PresentationCreateRequest): Promise<Presentation> {
    return this._post<Presentation>("/api/presentations", data);
  }

  /** List presentations. */
  async list(params?: PaginationParams): Promise<Presentation[]> {
    return this._get<Presentation[]>("/api/presentations", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get presentation with slides. */
  async get(id: string): Promise<Presentation> {
    return this._get<Presentation>(`/api/presentations/${id}`);
  }

  /** Delete a presentation. */
  async delete(id: string): Promise<void> {
    return this._delete(`/api/presentations/${id}`);
  }

  // -- Slide editing -------------------------------------------------------

  /** Update a slide at a given position. */
  async updateSlide(presentationId: string, position: number, data: Partial<PresentationSlide>): Promise<PresentationSlide> {
    return this._put<PresentationSlide>(`/api/presentations/${presentationId}/slides/${position}`, data);
  }

  /** Insert a slide after a given position. */
  async insertSlide(presentationId: string, afterPosition: number, data: Partial<PresentationSlide>): Promise<PresentationSlide> {
    return this._post<PresentationSlide>(`/api/presentations/${presentationId}/slides/${afterPosition}`, data);
  }

  /** Remove a slide. */
  async removeSlide(presentationId: string, position: number): Promise<void> {
    return this._delete(`/api/presentations/${presentationId}/slides/${position}`);
  }

  // -- Export --------------------------------------------------------------

  /** Export presentation (HTML, Markdown, or PDF). */
  async export(id: string, data: PresentationExportRequest): Promise<string> {
    return this._post<string>(`/api/presentations/${id}/export`, data);
  }

  // -- From transcript -----------------------------------------------------

  /** Generate a presentation from a transcription. */
  async fromTranscript(data: PresentationFromTranscriptRequest): Promise<Presentation> {
    return this._post<Presentation>("/api/presentations/from-transcript", data);
  }

  // -- Templates -----------------------------------------------------------

  /** List available presentation templates. */
  async listTemplates(): Promise<PresentationTemplate[]> {
    return this._get<PresentationTemplate[]>("/api/presentations/templates");
  }
}
