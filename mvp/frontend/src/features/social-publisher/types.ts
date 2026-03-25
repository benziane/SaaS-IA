/**
 * Social Publisher Types
 */

export interface SocialAccount {
  id: string;
  user_id: string;
  platform: string;
  account_name: string;
  is_active: boolean;
  created_at: string;
}

export interface SocialAccountCreateRequest {
  platform: 'twitter' | 'linkedin' | 'instagram' | 'tiktok' | 'facebook';
  access_token: string;
  account_name: string;
}

export interface SocialPost {
  id: string;
  user_id: string;
  content: string;
  platforms: string[];
  status: 'draft' | 'scheduled' | 'publishing' | 'published' | 'failed';
  published_at: string | null;
  schedule_at: string | null;
  results: Record<string, unknown>;
  media_urls: string[];
  hashtags: string[];
  created_at: string;
  updated_at: string;
}

export interface PostCreateRequest {
  content: string;
  platforms: string[];
  schedule_at?: string;
  media_urls?: string[];
  hashtags?: string[];
}

export interface PostListResponse {
  posts: SocialPost[];
  total: number;
  limit: number;
  offset: number;
}

export interface PostAnalytics {
  post_id: string;
  platform: string;
  impressions: number;
  engagements: number;
  clicks: number;
  shares: number;
}

export interface RecycleRequest {
  content_id: string;
  platforms: string[];
  custom_instructions?: string;
}

export interface SocialPlatform {
  id: string;
  name: string;
  description: string;
  max_length: number;
  icon: string;
}
