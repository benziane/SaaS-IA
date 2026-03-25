/**
 * Social Publisher API
 */

import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type {
  PostAnalytics,
  PostCreateRequest,
  PostListResponse,
  RecycleRequest,
  SocialAccount,
  SocialAccountCreateRequest,
  SocialPlatform,
  SocialPost,
} from './types';

const ENDPOINTS = {
  ACCOUNTS: '/api/social-publisher/accounts',
  ACCOUNT: (id: string) => `/api/social-publisher/accounts/${id}`,
  POSTS: '/api/social-publisher/posts',
  POST: (id: string) => `/api/social-publisher/posts/${id}`,
  PUBLISH: (id: string) => `/api/social-publisher/posts/${id}/publish`,
  SCHEDULE: (id: string) => `/api/social-publisher/posts/${id}/schedule`,
  ANALYTICS: (id: string) => `/api/social-publisher/posts/${id}/analytics`,
  RECYCLE: '/api/social-publisher/recycle',
  PLATFORMS: '/api/social-publisher/platforms',
} as const;

// -- Accounts --

export async function connectAccount(data: SocialAccountCreateRequest): Promise<SocialAccount> {
  const response: AxiosResponse<SocialAccount> = await apiClient.post(ENDPOINTS.ACCOUNTS, data);
  return response.data;
}

export async function listAccounts(): Promise<SocialAccount[]> {
  const response: AxiosResponse<SocialAccount[]> = await apiClient.get(ENDPOINTS.ACCOUNTS);
  return response.data;
}

export async function disconnectAccount(id: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.ACCOUNT(id));
}

// -- Posts --

export async function createPost(data: PostCreateRequest): Promise<SocialPost> {
  const response: AxiosResponse<SocialPost> = await apiClient.post(ENDPOINTS.POSTS, data);
  return response.data;
}

export async function listPosts(params?: {
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<PostListResponse> {
  const response: AxiosResponse<PostListResponse> = await apiClient.get(ENDPOINTS.POSTS, { params });
  return response.data;
}

export async function getPost(id: string): Promise<SocialPost> {
  const response: AxiosResponse<SocialPost> = await apiClient.get(ENDPOINTS.POST(id));
  return response.data;
}

export async function publishPost(id: string): Promise<SocialPost> {
  const response: AxiosResponse<SocialPost> = await apiClient.post(ENDPOINTS.PUBLISH(id));
  return response.data;
}

export async function schedulePost(id: string, schedule_at: string): Promise<SocialPost> {
  const response: AxiosResponse<SocialPost> = await apiClient.put(ENDPOINTS.SCHEDULE(id), { schedule_at });
  return response.data;
}

export async function deletePost(id: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.POST(id));
}

export async function getPostAnalytics(id: string): Promise<PostAnalytics[]> {
  const response: AxiosResponse<PostAnalytics[]> = await apiClient.get(ENDPOINTS.ANALYTICS(id));
  return response.data;
}

export async function recycleContent(data: RecycleRequest): Promise<SocialPost> {
  const response: AxiosResponse<SocialPost> = await apiClient.post(ENDPOINTS.RECYCLE, data);
  return response.data;
}

export async function listPlatforms(): Promise<{ platforms: SocialPlatform[] }> {
  const response: AxiosResponse<{ platforms: SocialPlatform[] }> = await apiClient.get(ENDPOINTS.PLATFORMS);
  return response.data;
}
