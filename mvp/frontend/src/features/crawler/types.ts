export interface ImageData {
  src: string;
  alt: string;
  score: number;
  description?: string;
}

export interface ScrapeResponse {
  url: string;
  title: string;
  markdown: string;
  text_length: number;
  images: ImageData[];
  image_count: number;
  screenshot_base64?: string;
  success: boolean;
  error?: string;
}

export interface ScrapeWithVisionResponse {
  url: string;
  title: string;
  markdown: string;
  images: ImageData[];
  vision_provider: string;
  success: boolean;
  error?: string;
}

export interface IndexResponse {
  url: string;
  pages_crawled: number;
  chunks_indexed: number;
  images_found: number;
  success: boolean;
  error?: string;
}

// ── v7 Types ───────────────────────────────────────

export interface ProxyConfig {
  server: string;
  username?: string;
  password?: string;
}

export interface DispatcherConfig {
  max_session_permit?: number;
  memory_threshold_percent?: number;
  rate_limit_base_delay_min?: number;
  rate_limit_base_delay_max?: number;
  rate_limit_max_delay?: number;
}

export interface BatchScrapeRequest {
  urls: string[];
  extract_images?: boolean;
  proxies?: ProxyConfig[];
  dispatcher?: DispatcherConfig;
}

export interface BatchResultItem {
  url: string;
  title: string;
  markdown: string;
  text_length: number;
  images: ImageData[];
  image_count: number;
  success: boolean;
  error?: string;
}

export interface BatchScrapeResponse {
  results: BatchResultItem[];
  total: number;
  successes: number;
  monitor_stats?: Record<string, unknown>;
  success: boolean;
  error?: string;
}

export interface DeepCrawlRequest {
  start_url: string;
  max_depth?: number;
  max_pages?: number;
  strategy?: 'bfs' | 'dfs' | 'bestfirst';
  extract_images?: boolean;
  composite_scorers?: string[];
  domain_authority_weights?: Record<string, number>;
  proxies?: ProxyConfig[];
  dispatcher?: DispatcherConfig;
}

export interface DeepCrawlResponse {
  results: BatchResultItem[];
  total_pages: number;
  monitor_stats?: Record<string, unknown>;
  success: boolean;
  error?: string;
}

export interface ExtractRequest {
  url: string;
  selector?: string;
  xpath?: string;
  regex_pattern?: string;
}

export interface ExtractResponse {
  url: string;
  results: string[];
  count: number;
  success: boolean;
  error?: string;
}

export interface SeedUrlsResponse {
  domain: string;
  urls: string[];
  total: number;
  source: string;
  success: boolean;
  error?: string;
}
