'use client';

import { useMutation } from '@tanstack/react-query';
import {
  indexUrl,
  scrapeUrl,
  scrapeWithVision,
  batchScrape,
  deepCrawl,
  extractCss,
  seedUrls,
} from '../api';
import type {
  IndexResponse,
  ScrapeResponse,
  ScrapeWithVisionResponse,
  BatchScrapeRequest,
  BatchScrapeResponse,
  DeepCrawlRequest,
  DeepCrawlResponse,
  ExtractResponse,
  SeedUrlsResponse,
} from '../types';

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

// ── v7 Hooks ───────────────────────────────────────

export function useBatchScrape() {
  return useMutation<BatchScrapeResponse, Error, BatchScrapeRequest>({
    mutationFn: (params) => batchScrape(params),
  });
}

export function useDeepCrawl() {
  return useMutation<DeepCrawlResponse, Error, DeepCrawlRequest>({
    mutationFn: (params) => deepCrawl(params),
  });
}

export function useExtractCss() {
  return useMutation<ExtractResponse, Error, { url: string; selector: string }>({
    mutationFn: ({ url, selector }) => extractCss(url, selector),
  });
}

export function useSeedUrls() {
  return useMutation<SeedUrlsResponse, Error, { domain: string; source?: string; maxUrls?: number }>({
    mutationFn: ({ domain, source, maxUrls }) => seedUrls(domain, source, maxUrls),
  });
}
