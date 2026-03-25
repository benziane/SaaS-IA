/**
 * Marketplace API
 */

import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type {
  ListingCreateRequest,
  ListingUpdateRequest,
  ListingsQueryParams,
  MarketplaceCategory,
  MarketplaceInstall,
  MarketplaceListing,
  MarketplaceReview,
  ReviewCreateRequest,
} from './types';

const ENDPOINTS = {
  LISTINGS: '/api/marketplace/listings',
  LISTING: (id: string) => `/api/marketplace/listings/${id}`,
  PUBLISH: (id: string) => `/api/marketplace/listings/${id}/publish`,
  UNPUBLISH: (id: string) => `/api/marketplace/listings/${id}/unpublish`,
  INSTALL: (id: string) => `/api/marketplace/listings/${id}/install`,
  REVIEWS: (id: string) => `/api/marketplace/listings/${id}/reviews`,
  CATEGORIES: '/api/marketplace/categories',
  FEATURED: '/api/marketplace/featured',
  INSTALLED: '/api/marketplace/installed',
  MY_LISTINGS: '/api/marketplace/my-listings',
} as const;

export async function browseListings(params?: ListingsQueryParams): Promise<MarketplaceListing[]> {
  const response: AxiosResponse<MarketplaceListing[]> = await apiClient.get(ENDPOINTS.LISTINGS, { params });
  return response.data;
}

export async function getListing(id: string): Promise<MarketplaceListing> {
  const response: AxiosResponse<MarketplaceListing> = await apiClient.get(ENDPOINTS.LISTING(id));
  return response.data;
}

export async function createListing(data: ListingCreateRequest): Promise<MarketplaceListing> {
  const response: AxiosResponse<MarketplaceListing> = await apiClient.post(ENDPOINTS.LISTINGS, data);
  return response.data;
}

export async function updateListing(id: string, data: ListingUpdateRequest): Promise<MarketplaceListing> {
  const response: AxiosResponse<MarketplaceListing> = await apiClient.put(ENDPOINTS.LISTING(id), data);
  return response.data;
}

export async function deleteListing(id: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.LISTING(id));
}

export async function publishListing(id: string): Promise<MarketplaceListing> {
  const response: AxiosResponse<MarketplaceListing> = await apiClient.post(ENDPOINTS.PUBLISH(id));
  return response.data;
}

export async function unpublishListing(id: string): Promise<MarketplaceListing> {
  const response: AxiosResponse<MarketplaceListing> = await apiClient.post(ENDPOINTS.UNPUBLISH(id));
  return response.data;
}

export async function installListing(id: string): Promise<MarketplaceInstall> {
  const response: AxiosResponse<MarketplaceInstall> = await apiClient.post(ENDPOINTS.INSTALL(id));
  return response.data;
}

export async function uninstallListing(id: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.INSTALL(id));
}

export async function listInstalled(): Promise<MarketplaceInstall[]> {
  const response: AxiosResponse<MarketplaceInstall[]> = await apiClient.get(ENDPOINTS.INSTALLED);
  return response.data;
}

export async function getReviews(listingId: string, limit?: number, offset?: number): Promise<MarketplaceReview[]> {
  const params = { limit, offset };
  const response: AxiosResponse<MarketplaceReview[]> = await apiClient.get(ENDPOINTS.REVIEWS(listingId), { params });
  return response.data;
}

export async function addReview(listingId: string, data: ReviewCreateRequest): Promise<MarketplaceReview> {
  const response: AxiosResponse<MarketplaceReview> = await apiClient.post(ENDPOINTS.REVIEWS(listingId), data);
  return response.data;
}

export async function getCategories(): Promise<MarketplaceCategory[]> {
  const response: AxiosResponse<MarketplaceCategory[]> = await apiClient.get(ENDPOINTS.CATEGORIES);
  return response.data;
}

export async function getFeatured(limit?: number): Promise<MarketplaceListing[]> {
  const params = limit ? { limit } : {};
  const response: AxiosResponse<MarketplaceListing[]> = await apiClient.get(ENDPOINTS.FEATURED, { params });
  return response.data;
}

export async function getMyListings(): Promise<MarketplaceListing[]> {
  const response: AxiosResponse<MarketplaceListing[]> = await apiClient.get(ENDPOINTS.MY_LISTINGS);
  return response.data;
}
