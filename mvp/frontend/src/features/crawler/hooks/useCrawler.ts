'use client';

import { useMutation, useQuery } from '@tanstack/react-query';
import {
  indexUrl,
  scrapeUrl,
  scrapeWithVision,
  batchScrape,
  deepCrawl,
  extractCss,
  seedUrls,
  scrapeHttp,
  adaptiveCrawl,
  hubCrawl,
  scrapePdf,
  extractCosine,
  extractLxml,
  dockerCrawl,
  chunkRegex,
  compileC4A,
  validateC4A,
  compileC4AFile,
  listBrowserProfiles,
  createBrowserProfile,
  deleteBrowserProfile,
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
  FastScrapeResponse,
  AdaptiveCrawlRequest,
  AdaptiveCrawlResponse,
  HubCrawlRequest,
  HubCrawlResponse,
  PdfScrapeRequest,
  PdfScrapeResponse,
  CosineExtractRequest,
  CosineExtractResponse,
  LxmlExtractRequest,
  LxmlExtractResponse,
  DockerCrawlRequest,
  DockerCrawlResponse,
  RegexChunkRequest,
  RegexChunkResponse,
  C4ACompileResponse,
  C4AValidateResponse,
  BrowserProfileResponse,
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

// ── v6-v8 Hooks ──────────────────────────────────────

export function useScrapeHttp() {
  return useMutation<FastScrapeResponse, Error, { url: string }>({
    mutationFn: ({ url }) => scrapeHttp(url),
  });
}

export function useAdaptiveCrawl() {
  return useMutation<AdaptiveCrawlResponse, Error, AdaptiveCrawlRequest>({
    mutationFn: (params) => adaptiveCrawl(params),
  });
}

export function useHubCrawl() {
  return useMutation<HubCrawlResponse, Error, HubCrawlRequest>({
    mutationFn: (params) => hubCrawl(params),
  });
}

export function useScrapePdf() {
  return useMutation<PdfScrapeResponse, Error, PdfScrapeRequest>({
    mutationFn: (params) => scrapePdf(params),
  });
}

export function useExtractCosine() {
  return useMutation<CosineExtractResponse, Error, CosineExtractRequest>({
    mutationFn: (params) => extractCosine(params),
  });
}

export function useExtractLxml() {
  return useMutation<LxmlExtractResponse, Error, LxmlExtractRequest>({
    mutationFn: (params) => extractLxml(params),
  });
}

export function useDockerCrawl() {
  return useMutation<DockerCrawlResponse, Error, DockerCrawlRequest>({
    mutationFn: (params) => dockerCrawl(params),
  });
}

export function useChunkRegex() {
  return useMutation<RegexChunkResponse, Error, RegexChunkRequest>({
    mutationFn: (params) => chunkRegex(params),
  });
}

export function useCompileC4A() {
  return useMutation<C4ACompileResponse, Error, { script: string }>({
    mutationFn: ({ script }) => compileC4A(script),
  });
}

export function useValidateC4A() {
  return useMutation<C4AValidateResponse, Error, { script: string }>({
    mutationFn: ({ script }) => validateC4A(script),
  });
}

export function useCompileC4AFile() {
  return useMutation<C4ACompileResponse, Error, { filePath: string }>({
    mutationFn: ({ filePath }) => compileC4AFile(filePath),
  });
}

export function useBrowserProfiles() {
  return useQuery<BrowserProfileResponse, Error>({
    queryKey: ['crawler', 'browser-profiles'],
    queryFn: () => listBrowserProfiles(),
  });
}

export function useCreateBrowserProfile() {
  return useMutation<BrowserProfileResponse, Error, { profileName?: string }>({
    mutationFn: ({ profileName }) => createBrowserProfile(profileName),
  });
}

export function useDeleteBrowserProfile() {
  return useMutation<BrowserProfileResponse, Error, { name: string }>({
    mutationFn: ({ name }) => deleteBrowserProfile(name),
  });
}
