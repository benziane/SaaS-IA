import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type { ScrapeResponse, ScrapeWithVisionResponse, IndexResponse } from './types';

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
