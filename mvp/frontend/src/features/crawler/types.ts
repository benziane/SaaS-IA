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

// ── v6-v8 Types ──────────────────────────────────────

export interface FastScrapeResponse {
  url: string;
  title: string;
  markdown: string;
  fit_markdown: string;
  text_length: number;
  links_internal: string[];
  links_external: string[];
  status_code?: number;
  scraper: string;
  success: boolean;
  error?: string;
}

export interface AdaptiveCrawlRequest {
  url: string;
  query: string;
  max_pages?: number;
  max_depth?: number;
  strategy?: 'statistical' | 'embedding';
  confidence_threshold?: number;
}

export interface AdaptiveCrawlPageResult {
  url: string;
  title: string;
  markdown: string;
  depth: number;
  score?: number;
  success: boolean;
  error?: string;
}

export interface AdaptiveCrawlResponse {
  url: string;
  query: string;
  pages: AdaptiveCrawlPageResult[];
  total_pages: number;
  succeeded: number;
  failed: number;
  confidence?: number;
  is_sufficient?: boolean;
  success: boolean;
  error?: string;
}

export interface HubCrawlRequest {
  url: string;
  site_profile: string;
  use_fit_markdown?: boolean;
}

export interface HubCrawlResponse {
  url: string;
  site_profile: string;
  data?: Record<string, unknown>;
  success: boolean;
  error?: string;
}

export interface PdfScrapeRequest {
  url: string;
  extract_images?: boolean;
}

export interface PdfScrapeResponse {
  url: string;
  markdown: string;
  text_length: number;
  success: boolean;
  error?: string;
}

export interface CosineExtractRequest {
  url: string;
  word_count_threshold?: number;
  max_dist?: number;
  top_k?: number;
  sim_threshold?: number;
  semantic_filter?: string;
}

export interface CosineCluster {
  index: number;
  tags: string[];
  content: string;
}

export interface CosineExtractResponse {
  url: string;
  clusters: CosineCluster[];
  total_clusters: number;
  success: boolean;
  error?: string;
}

export interface LxmlExtractRequest {
  url: string;
  schema: Record<string, unknown>;
}

export interface LxmlExtractResponse {
  url: string;
  data?: unknown;
  success: boolean;
  error?: string;
}

export interface DockerCrawlRequest {
  urls: string[];
  docker_url?: string;
  timeout?: number;
}

export interface DockerCrawlResult {
  url: string;
  title: string;
  markdown: string;
  success: boolean;
  error?: string;
}

export interface DockerCrawlResponse {
  total: number;
  succeeded: number;
  failed: number;
  results: DockerCrawlResult[];
  success: boolean;
  error?: string;
}

export interface RegexChunkRequest {
  text: string;
  patterns?: string[];
}

export interface RegexChunkResponse {
  chunks: string[];
  total_chunks: number;
  success: boolean;
  error?: string;
}

export interface C4ACompileRequest {
  script: string;
}

export interface C4ACompileResponse {
  js_code: string;
  success: boolean;
  error?: string;
}

export interface C4AValidateRequest {
  script: string;
}

export interface C4AValidateResponse {
  valid: boolean;
  errors: string[];
}

export interface BrowserProfileCreateRequest {
  profile_name?: string;
}

export interface BrowserProfileResponse {
  profile_name?: string;
  profile_path?: string;
  profiles: Record<string, unknown>[];
  success: boolean;
  error?: string;
}
