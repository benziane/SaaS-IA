'use client';

import { useMutation } from '@tanstack/react-query';
import { indexUrl, scrapeUrl, scrapeWithVision } from '../api';
import type { IndexResponse, ScrapeResponse, ScrapeWithVisionResponse } from '../types';

export function useScrape() {
  return useMutation<ScrapeResponse, Error, { url: string; extractImages?: boolean }>({
    mutationFn: ({ url, extractImages }) => scrapeUrl(url, extractImages),
  });
}

export function useScrapeWithVision() {
  return useMutation<ScrapeWithVisionResponse, Error, { url: string; maxImages?: number }>({
    mutationFn: ({ url, maxImages }) => scrapeWithVision(url, maxImages),
  });
}

export function useIndexUrl() {
  return useMutation<IndexResponse, Error, { url: string; crawlSubpages?: boolean; maxPages?: number }>({
    mutationFn: ({ url, crawlSubpages, maxPages }) => indexUrl(url, crawlSubpages, maxPages),
  });
}
