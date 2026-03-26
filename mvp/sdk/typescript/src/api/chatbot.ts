import { BaseAPI } from "./base";
import {
  Chatbot,
  ChatbotCreateRequest,
  ChatbotUpdateRequest,
  ChatbotAnalytics,
  ChatbotChannel,
  ChatMessage,
  ChatResponse,
  PaginationParams,
} from "../types";

/**
 * AI Chatbot Builder API — RAG chatbots with embed widget deployment
 * and multi-channel support.
 */
export class ChatbotAPI extends BaseAPI {
  // -- CRUD ----------------------------------------------------------------

  /** Create a chatbot. */
  async create(data: ChatbotCreateRequest): Promise<Chatbot> {
    return this._post<Chatbot>("/api/chatbots", data);
  }

  /** List chatbots. */
  async list(params?: PaginationParams): Promise<Chatbot[]> {
    return this._get<Chatbot[]>("/api/chatbots", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get chatbot details. */
  async get(id: string): Promise<Chatbot> {
    return this._get<Chatbot>(`/api/chatbots/${id}`);
  }

  /** Update chatbot settings. */
  async update(id: string, data: ChatbotUpdateRequest): Promise<Chatbot> {
    return this._put<Chatbot>(`/api/chatbots/${id}`, data);
  }

  /** Soft-delete a chatbot. */
  async delete(id: string): Promise<void> {
    return this._delete(`/api/chatbots/${id}`);
  }

  // -- Publishing ----------------------------------------------------------

  /** Publish chatbot and generate an embed token. */
  async publish(id: string): Promise<{ embed_token: string }> {
    return this._post<{ embed_token: string }>(`/api/chatbots/${id}/publish`);
  }

  /** Unpublish chatbot and revoke embed token. */
  async unpublish(id: string): Promise<void> {
    return this._post(`/api/chatbots/${id}/unpublish`);
  }

  // -- Channels ------------------------------------------------------------

  /** Add a deployment channel. */
  async addChannel(chatbotId: string, data: { type: string; config?: Record<string, unknown> }): Promise<ChatbotChannel> {
    return this._post<ChatbotChannel>(`/api/chatbots/${chatbotId}/channels`, data);
  }

  /** Remove a deployment channel. */
  async removeChannel(chatbotId: string, channelType: string): Promise<void> {
    return this._delete(`/api/chatbots/${chatbotId}/channels/${channelType}`);
  }

  // -- Analytics -----------------------------------------------------------

  /** Get chatbot analytics. */
  async analytics(id: string): Promise<ChatbotAnalytics> {
    return this._get<ChatbotAnalytics>(`/api/chatbots/${id}/analytics`);
  }

  /** Get embed HTML/JS snippet. */
  async embedCode(id: string): Promise<{ html: string; js: string }> {
    return this._get<{ html: string; js: string }>(`/api/chatbots/${id}/embed-code`);
  }

  // -- Public widget (no auth required) ------------------------------------

  /** Chat with a published chatbot via its embed token. */
  async widgetChat(token: string, data: ChatMessage): Promise<ChatResponse> {
    return this._post<ChatResponse>(`/api/chatbots/widget/${token}/chat`, data);
  }

  /** Get chat history for a widget session. */
  async widgetHistory(token: string, sessionId: string): Promise<ChatResponse[]> {
    return this._get<ChatResponse[]>(`/api/chatbots/widget/${token}/history/${sessionId}`);
  }

  /** Get widget configuration. */
  async widgetConfig(token: string): Promise<Record<string, unknown>> {
    return this._get<Record<string, unknown>>(`/api/chatbots/widget/${token}/config`);
  }
}
