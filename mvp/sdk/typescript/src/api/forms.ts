import { BaseAPI } from "./base";
import {
  Form,
  FormCreateRequest,
  FormUpdateRequest,
  FormResponse,
  FormGenerateRequest,
  PaginationParams,
} from "../types";

/**
 * AI Forms API — conversational forms with AI generation, scoring,
 * and public sharing.
 */
export class FormsAPI extends BaseAPI {
  // -- CRUD ----------------------------------------------------------------

  /** Create a form. */
  async create(data: FormCreateRequest): Promise<Form> {
    return this._post<Form>("/api/forms", data);
  }

  /** List forms. */
  async list(params?: PaginationParams): Promise<Form[]> {
    return this._get<Form[]>("/api/forms", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get form details. */
  async get(id: string): Promise<Form> {
    return this._get<Form>(`/api/forms/${id}`);
  }

  /** Update a form. */
  async update(id: string, data: FormUpdateRequest): Promise<Form> {
    return this._put<Form>(`/api/forms/${id}`, data);
  }

  /** Soft-delete a form. */
  async delete(id: string): Promise<void> {
    return this._delete(`/api/forms/${id}`);
  }

  // -- Publishing ----------------------------------------------------------

  /** Publish form and generate share token. */
  async publish(id: string): Promise<{ share_token: string }> {
    return this._post<{ share_token: string }>(`/api/forms/${id}/publish`);
  }

  /** Close form to new responses. */
  async close(id: string): Promise<void> {
    return this._post(`/api/forms/${id}/close`);
  }

  // -- Responses -----------------------------------------------------------

  /** List form responses. */
  async listResponses(formId: string, params?: PaginationParams): Promise<FormResponse[]> {
    return this._get<FormResponse[]>(`/api/forms/${formId}/responses`, {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get a single response. */
  async getResponse(formId: string, responseId: string): Promise<FormResponse> {
    return this._get<FormResponse>(`/api/forms/${formId}/responses/${responseId}`);
  }

  /** AI analysis of all responses. */
  async analytics(formId: string): Promise<Record<string, unknown>> {
    return this._get<Record<string, unknown>>(`/api/forms/${formId}/analytics`);
  }

  /** AI scoring of a specific response. */
  async scoreResponse(formId: string, responseId: string): Promise<{ score: number; feedback: string }> {
    return this._post<{ score: number; feedback: string }>(`/api/forms/${formId}/responses/${responseId}/score`);
  }

  // -- AI generation -------------------------------------------------------

  /** Generate a form from a natural language prompt. */
  async generate(data: FormGenerateRequest): Promise<Form> {
    return this._post<Form>("/api/forms/generate", data);
  }

  // -- Public endpoints (no auth) ------------------------------------------

  /** Get a published form by its share token. */
  async getPublic(token: string): Promise<Form> {
    return this._get<Form>(`/api/forms/public/${token}`);
  }

  /** Submit a response to a public form. */
  async submitPublic(token: string, answers: Record<string, unknown>): Promise<FormResponse> {
    return this._post<FormResponse>(`/api/forms/public/${token}/submit`, { answers });
  }
}
