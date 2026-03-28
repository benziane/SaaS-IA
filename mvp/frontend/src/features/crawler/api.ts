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

export async function scrapeHttp(url: string): Promise<FastScrapeResponse> {
  const { data } = await apiClient.post<FastScrapeResponse>('/api/crawler/scrape-http', { url });
  return data;
}

// ── v6-v8 API functions ──────────────────────────────

export async function adaptiveCrawl(params: AdaptiveCrawlRequest): Promise<AdaptiveCrawlResponse> {
  const { data } = await apiClient.post<AdaptiveCrawlResponse>('/api/crawler/adaptive-crawl', params);
  return data;
}

export async function hubCrawl(params: HubCrawlRequest): Promise<HubCrawlResponse> {
  const { data } = await apiClient.post<HubCrawlResponse>('/api/crawler/hub/crawl', params);
  return data;
}

export async function scrapePdf(params: PdfScrapeRequest): Promise<PdfScrapeResponse> {
  const { data } = await apiClient.post<PdfScrapeResponse>('/api/crawler/scrape-pdf', params);
  return data;
}

export async function extractCosine(params: CosineExtractRequest): Promise<CosineExtractResponse> {
  const { data } = await apiClient.post<CosineExtractResponse>('/api/crawler/extract-cosine', params);
  return data;
}

export async function extractLxml(params: LxmlExtractRequest): Promise<LxmlExtractResponse> {
  const { data } = await apiClient.post<LxmlExtractResponse>('/api/crawler/extract-lxml', params);
  return data;
}

export async function dockerCrawl(params: DockerCrawlRequest): Promise<DockerCrawlResponse> {
  const { data } = await apiClient.post<DockerCrawlResponse>('/api/crawler/docker-crawl', params);
  return data;
}

export async function chunkRegex(params: RegexChunkRequest): Promise<RegexChunkResponse> {
  const { data } = await apiClient.post<RegexChunkResponse>('/api/crawler/chunk-regex', params);
  return data;
}

export async function compileC4A(script: string): Promise<C4ACompileResponse> {
  const { data } = await apiClient.post<C4ACompileResponse>('/api/crawler/c4a/compile', { script });
  return data;
}

export async function validateC4A(script: string): Promise<C4AValidateResponse> {
  const { data } = await apiClient.post<C4AValidateResponse>('/api/crawler/c4a/validate', { script });
  return data;
}

export async function compileC4AFile(filePath: string): Promise<C4ACompileResponse> {
  const { data } = await apiClient.post<C4ACompileResponse>('/api/crawler/c4a/compile-file', { file_path: filePath });
  return data;
}

export async function listBrowserProfiles(): Promise<BrowserProfileResponse> {
  const { data } = await apiClient.get<BrowserProfileResponse>('/api/crawler/profiles');
  return data;
}

export async function createBrowserProfile(profileName?: string): Promise<BrowserProfileResponse> {
  const { data } = await apiClient.post<BrowserProfileResponse>('/api/crawler/profiles', { profile_name: profileName });
  return data;
}

export async function deleteBrowserProfile(name: string): Promise<BrowserProfileResponse> {
  const { data } = await apiClient.delete<BrowserProfileResponse>(`/api/crawler/profiles/${name}`);
  return data;
}
