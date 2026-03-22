/**
 * Knowledge Base Types
 */

export interface KBDocument {
  id: string;
  filename: string;
  content_type: string;
  total_chunks: number;
  status: string;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  filename: string;
  content: string;
  score: number;
  chunk_index: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export interface AskResponse {
  question: string;
  answer: string;
  sources: SearchResult[];
  provider: string;
}
