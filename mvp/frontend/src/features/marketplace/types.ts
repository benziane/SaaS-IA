/**
 * Marketplace Types
 */

export interface MarketplaceListing {
  id: string;
  author_id: string;
  author_name: string;
  title: string;
  description: string;
  type: 'module' | 'template' | 'prompt' | 'workflow' | 'dataset';
  category: string;
  price: number;
  version: string;
  content: Record<string, unknown>;
  tags: string[];
  preview_images: string[];
  rating: number;
  reviews_count: number;
  installs_count: number;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface ListingCreateRequest {
  title: string;
  description: string;
  type: string;
  category: string;
  price?: number;
  version?: string;
  content?: Record<string, unknown>;
  tags?: string[];
  preview_images?: string[];
}

export interface ListingUpdateRequest {
  title?: string;
  description?: string;
  price?: number;
  version?: string;
  content?: Record<string, unknown>;
  tags?: string[];
}

export interface MarketplaceReview {
  id: string;
  user_id: string;
  user_name: string;
  listing_id: string;
  rating: number;
  comment: string | null;
  created_at: string;
}

export interface ReviewCreateRequest {
  rating: number;
  comment?: string;
}

export interface MarketplaceInstall {
  id: string;
  user_id: string;
  listing_id: string;
  installed_at: string;
  version: string;
}

export interface MarketplaceCategory {
  id: string;
  name: string;
  icon: string;
}

export interface ListingsQueryParams {
  type?: string;
  category?: string;
  sort_by?: string;
  search?: string;
  limit?: number;
  offset?: number;
}
