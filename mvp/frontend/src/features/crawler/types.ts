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
