/**
 * Marketplace hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  addReview,
  browseListings,
  createListing,
  deleteListing,
  getCategories,
  getFeatured,
  getListing,
  getMyListings,
  getReviews,
  installListing,
  listInstalled,
  publishListing,
  uninstallListing,
  unpublishListing,
  updateListing,
} from '../api';
import type {
  ListingCreateRequest,
  ListingUpdateRequest,
  ListingsQueryParams,
  MarketplaceCategory,
  MarketplaceInstall,
  MarketplaceListing,
  MarketplaceReview,
  ReviewCreateRequest,
} from '../types';

export function useMarketplaceListings(params?: ListingsQueryParams) {
  return useQuery<MarketplaceListing[]>({
    queryKey: ['marketplace-listings', params],
    queryFn: () => browseListings(params),
  });
}

export function useMarketplaceListing(id: string | null) {
  return useQuery<MarketplaceListing>({
    queryKey: ['marketplace-listing', id],
    queryFn: () => getListing(id!),
    enabled: !!id,
  });
}

export function useMarketplaceFeatured() {
  return useQuery<MarketplaceListing[]>({
    queryKey: ['marketplace-featured'],
    queryFn: () => getFeatured(),
  });
}

export function useMarketplaceCategories() {
  return useQuery<MarketplaceCategory[]>({
    queryKey: ['marketplace-categories'],
    queryFn: getCategories,
  });
}

export function useMyListings() {
  return useQuery<MarketplaceListing[]>({
    queryKey: ['marketplace-my-listings'],
    queryFn: getMyListings,
  });
}

export function useInstalledListings() {
  return useQuery<MarketplaceInstall[]>({
    queryKey: ['marketplace-installed'],
    queryFn: listInstalled,
  });
}

export function useListingReviews(listingId: string | null) {
  return useQuery<MarketplaceReview[]>({
    queryKey: ['marketplace-reviews', listingId],
    queryFn: () => getReviews(listingId!),
    enabled: !!listingId,
  });
}

export function useCreateListing() {
  const queryClient = useQueryClient();
  return useMutation<MarketplaceListing, Error, ListingCreateRequest>({
    mutationFn: createListing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace-listings'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-my-listings'] });
    },
  });
}

export function useUpdateListing() {
  const queryClient = useQueryClient();
  return useMutation<MarketplaceListing, Error, { id: string; data: ListingUpdateRequest }>({
    mutationFn: ({ id, data }) => updateListing(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace-listings'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-my-listings'] });
    },
  });
}

export function useDeleteListing() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteListing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace-listings'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-my-listings'] });
    },
  });
}

export function usePublishListing() {
  const queryClient = useQueryClient();
  return useMutation<MarketplaceListing, Error, string>({
    mutationFn: publishListing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace-listings'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-my-listings'] });
    },
  });
}

export function useUnpublishListing() {
  const queryClient = useQueryClient();
  return useMutation<MarketplaceListing, Error, string>({
    mutationFn: unpublishListing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace-listings'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-my-listings'] });
    },
  });
}

export function useInstallListing() {
  const queryClient = useQueryClient();
  return useMutation<MarketplaceInstall, Error, string>({
    mutationFn: installListing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace-installed'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-listings'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-featured'] });
    },
  });
}

export function useUninstallListing() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: uninstallListing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace-installed'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-listings'] });
    },
  });
}

export function useAddReview() {
  const queryClient = useQueryClient();
  return useMutation<MarketplaceReview, Error, { listingId: string; data: ReviewCreateRequest }>({
    mutationFn: ({ listingId, data }) => addReview(listingId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['marketplace-reviews', variables.listingId] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-listings'] });
      queryClient.invalidateQueries({ queryKey: ['marketplace-featured'] });
    },
  });
}
