export interface PDFUploadResponse {
  id: string;
  user_id: string;
  filename: string;
  num_pages: number;
  file_size_kb: number;
  status: string;
  created_at: string;
}

export interface PDFRead {
  id: string;
  user_id: string;
  filename: string;
  num_pages: number;
  file_size_kb: number;
  text_content: string | null;
  pages: PDFPage[];
  metadata: Record<string, unknown>;
  summary: string | null;
  keywords: string[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PDFPage {
  page_number: number;
  text: string;
  width?: number;
  height?: number;
}

export interface PDFQueryResponse {
  answer: string;
  sources: PDFSource[];
  confidence: number;
}

export interface PDFSource {
  chunk_index: number;
  text: string;
  relevance: number;
}

export interface PDFCompareResult {
  comparison: string;
  comparison_type: string;
  documents: { id: string; filename: string; num_pages: number }[];
  provider?: string;
}

export interface PDFExportResult {
  content: string;
  format: string;
  filename: string;
}

export interface PDFTableResult {
  tables: PDFTable[];
  total: number;
  engine?: string;
}

export interface PDFTable {
  page: number;
  table_index: number;
  headers: string[];
  rows: string[][];
  row_count: number;
}
