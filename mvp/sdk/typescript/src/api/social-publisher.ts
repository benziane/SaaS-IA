import { BaseAPI } from "./base";
import {
  SocialAccount,
  SocialPost,
  SocialPostCreateRequest,
  SocialPostAnalytics,
  PaginationParams,
} from "../types";

/**
 * Social Publisher API — multi-platform social media publishing,
 * scheduling, and analytics.
 */
export class SocialPublisherAPI extends BaseAPI {
  // -- Accounts ------------------------------------------------------------

  /** Connect a social media account. */
  async connectAccount(data: { platform: string; credentials: Record<string, string> }): Promise<SocialAccount> {
    return this._post<SocialAccount>("/api/social-publisher/accounts", data);
  }

  /** List connected accounts. */
  async listAccounts(): Promise<SocialAccount[]> {
    return this._get<SocialAccount[]>("/api/social-publisher/accounts");
  }

  /** Disconnect an account. */
  async disconnectAccount(id: string): Promise<void> {
    return this._delete(`/api/social-publisher/accounts/${id}`);
  }

  // -- Posts ---------------------------------------------------------------

  /** Create a post (draft or scheduled). */
  async createPost(data: SocialPostCreateRequest): Promise<SocialPost> {
    return this._post<SocialPost>("/api/social-publisher/posts", data);
  }

  /** List posts (filterable by status). */
  async listPosts(params?: PaginationParams & { status?: string }): Promise<SocialPost[]> {
    return this._get<SocialPost[]>("/api/social-publisher/posts", {
      limit: params?.limit,
      offset: params?.offset,
      status: params?.status,
    });
  }

  /** Get post details. */
  async getPost(id: string): Promise<SocialPost> {
    return this._get<SocialPost>(`/api/social-publisher/posts/${id}`);
  }

  /** Publish a post immediately. */
  async publishPost(id: string): Promise<SocialPost> {
    return this._post<SocialPost>(`/api/social-publisher/posts/${id}/publish`);
  }

  /** Schedule or reschedule a post. */
  async schedulePost(id: string, data: { scheduled_at: string }): Promise<SocialPost> {
    return this._put<SocialPost>(`/api/social-publisher/posts/${id}/schedule`, data);
  }

  /** Delete a draft or failed post. */
  async deletePost(id: string): Promise<void> {
    return this._delete(`/api/social-publisher/posts/${id}`);
  }

  /** Get post analytics. */
  async postAnalytics(id: string): Promise<SocialPostAnalytics> {
    return this._get<SocialPostAnalytics>(`/api/social-publisher/posts/${id}/analytics`);
  }

  // -- Content recycling ---------------------------------------------------

  /** Recycle Content Studio content for social media. */
  async recycle(data: { content_id: string; platforms: string[] }): Promise<SocialPost> {
    return this._post<SocialPost>("/api/social-publisher/recycle", data);
  }

  // -- Reference -----------------------------------------------------------

  /** List supported platforms. */
  async listPlatforms(): Promise<Array<{ id: string; name: string }>> {
    return this._get("/api/social-publisher/platforms");
  }
}
