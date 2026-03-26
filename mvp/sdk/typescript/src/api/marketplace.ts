import { BaseAPI } from "./base";
import {
  MarketplaceListing,
  MarketplaceReview,
  ListingCreateRequest,
  ListingUpdateRequest,
  ReviewCreateRequest,
  ListingCategory,
  PaginationParams,
} from "../types";

/**
 * Marketplace API — browse, publish, install, and review community
 * modules, templates, prompts, and more (8 categories).
 */
export class MarketplaceAPI extends BaseAPI {
  // -- Public browsing (no auth required) ----------------------------------

  /** Browse marketplace listings. */
  async browse(params?: PaginationParams & { category?: ListingCategory; search?: string }): Promise<MarketplaceListing[]> {
    return this._get<MarketplaceListing[]>("/api/marketplace/listings", {
      limit: params?.limit,
      offset: params?.offset,
      category: params?.category,
      search: params?.search,
    });
  }

  /** Get listing details. */
  async getListing(id: string): Promise<MarketplaceListing> {
    return this._get<MarketplaceListing>(`/api/marketplace/listings/${id}`);
  }

  /** Get reviews for a listing. */
  async getReviews(listingId: string): Promise<MarketplaceReview[]> {
    return this._get<MarketplaceReview[]>(`/api/marketplace/listings/${listingId}/reviews`);
  }

  /** List categories. */
  async categories(): Promise<Array<{ id: ListingCategory; name: string; count: number }>> {
    return this._get("/api/marketplace/categories");
  }

  /** Get featured listings. */
  async featured(): Promise<MarketplaceListing[]> {
    return this._get<MarketplaceListing[]>("/api/marketplace/featured");
  }

  // -- Authoring (auth required) -------------------------------------------

  /** Create a new listing. */
  async createListing(data: ListingCreateRequest): Promise<MarketplaceListing> {
    return this._post<MarketplaceListing>("/api/marketplace/listings", data);
  }

  /** Update a listing. */
  async updateListing(id: string, data: ListingUpdateRequest): Promise<MarketplaceListing> {
    return this._put<MarketplaceListing>(`/api/marketplace/listings/${id}`, data);
  }

  /** Publish a listing. */
  async publish(id: string): Promise<void> {
    return this._post(`/api/marketplace/listings/${id}/publish`);
  }

  /** Unpublish a listing. */
  async unpublish(id: string): Promise<void> {
    return this._post(`/api/marketplace/listings/${id}/unpublish`);
  }

  /** Soft-delete a listing. */
  async deleteListing(id: string): Promise<void> {
    return this._delete(`/api/marketplace/listings/${id}`);
  }

  /** List own listings. */
  async myListings(): Promise<MarketplaceListing[]> {
    return this._get<MarketplaceListing[]>("/api/marketplace/my-listings");
  }

  // -- Install / uninstall -------------------------------------------------

  /** Install a listing. */
  async install(listingId: string): Promise<{ status: string }> {
    return this._post<{ status: string }>(`/api/marketplace/listings/${listingId}/install`);
  }

  /** Uninstall a listing. */
  async uninstall(listingId: string): Promise<void> {
    return this._delete(`/api/marketplace/listings/${listingId}/install`);
  }

  /** List installed items. */
  async installed(): Promise<MarketplaceListing[]> {
    return this._get<MarketplaceListing[]>("/api/marketplace/installed");
  }

  // -- Reviews -------------------------------------------------------------

  /** Add a review to a listing. */
  async addReview(listingId: string, data: ReviewCreateRequest): Promise<MarketplaceReview> {
    return this._post<MarketplaceReview>(`/api/marketplace/listings/${listingId}/reviews`, data);
  }
}
