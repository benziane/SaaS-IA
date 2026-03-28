import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type {
  ScrapeResponse,
  ScrapeWithVisionResponse,
  IndexResponse,
  BatchScrapeRequest,
  BatchScrapeResponse,
  DeepCrawlRequest,
  DeepCrawlResponse,
  ExtractResponse,
  SeedUrlsResponse,
} from './types';

export async function scrapeUrl(url: string, extractImages: boolean = true): Promise<ScrapeResponse> {
  const response: AxiosResponse<ScrapeResponse> = await apiClient.post('/api/crawler/scrape', {
    url,
    extract_images: extractImages,
  });
  return response.data;
}

export async function scrapeWithVision(url: string, maxImages: number = 10): Promise<ScrapeWithVisionResponse> {
  const response: AxiosResponse<ScrapeWithVisionResponse> = await apiClient.post('/api/crawler/scrape-vision', {
    url,
    max_images: maxImages,
  });
  return response.data;
}

export async function indexUrl(url: string, crawlSubpages: boolean = false, maxPages: number = 5): Promise<IndexResponse> {
  const response: AxiosResponse<IndexResponse> = await apiClient.post('/api/crawler/index', {
    url,
    crawl_subpages: crawlSubpages,
    max_pages: maxPages,
  });
  return response.data;
}

// ── v7 API functions ───────────────────────────────

export async function batchScrape(params: BatchScrapeRequest): Promise<BatchScrapeResponse> {
  const { data } = await apiClient.post<BatchScrapeResponse>('/api/crawler/batch', params);
  return data;
}

export async function deepCrawl(params: DeepCrawlRequest): Promise<DeepCrawlResponse> {
  const { data } = await apiClient.post<DeepCrawlResponse>('/api/crawler/deep-crawl', params);
  return data;
}

export async function extractCss(url: string, selector: string): Promise<ExtractResponse> {
  const { data } = await apiClient.post<ExtractResponse>('/api/crawler/extract', { url, css_selector: selector });
  return data;
}

export async function extractXpath(url: string, xpath: string): Promise<ExtractResponse> {
  const { data } = await apiClient.post<ExtractResponse>('/api/crawler/extract-xpath', { url, xpath });
  return data;
}

export async function extractRegex(url: string, pattern: string): Promise<ExtractResponse> {
  const { data } = await apiClient.post<ExtractResponse>('/api/crawler/extract-regex', { url, regex_pattern: pattern });
  return data;
}

export async function seedUrls(domain: string, source: string = 'sitemap', maxUrls: number = 100): Promise<SeedUrlsResponse> {
  const { data } = await apiClient.post<SeedUrlsResponse>('/api/crawler/seed-urls', { domain, source, max_urls: maxUrls });
  return data;
}

export async function scrapeHttp(url: string): Promise<ScrapeResponse> {
  const { data } = await apiClient.post<ScrapeResponse>('/api/crawler/scrape-http', { url });
  return data;
}
