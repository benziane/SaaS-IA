import { BaseAPI } from "./base";
import {
  Conversation,
  ConversationWithMessages,
  ConversationCreateRequest,
  MessageCreateRequest,
  Message,
  PaginatedResponse,
  PaginationParams,
} from "../types";

/**
 * Conversation API — contextual AI chat with history, optionally linked to a
 * transcription for grounded Q&A.
 */
export class ConversationAPI extends BaseAPI {
  /** Create a new conversation (optionally linked to a transcription). */
  async create(data?: ConversationCreateRequest): Promise<Conversation> {
    return this._post<Conversation>("/api/conversations/", data ?? {});
  }

  /** List conversations (paginated). */
  async list(params?: PaginationParams): Promise<PaginatedResponse<Conversation>> {
    return this._get<PaginatedResponse<Conversation>>("/api/conversations/", {
      limit: params?.limit,
      offset: params?.offset,
    });
  }

  /** Get a conversation with its full message history. */
  async get(id: string): Promise<ConversationWithMessages> {
    return this._get<ConversationWithMessages>(`/api/conversations/${id}`);
  }

  /** Delete a conversation and all its messages. */
  async delete(id: string): Promise<void> {
    return this._delete(`/api/conversations/${id}`);
  }

  /** Send a message and receive the AI response (synchronous). */
  async sendMessage(conversationId: string, data: MessageCreateRequest): Promise<Message> {
    return this._post<Message>(`/api/conversations/${conversationId}/messages`, data);
  }
}
