import { BaseAPI } from "./base";
import {
  Document,
  DocumentChunk,
  KnowledgeSearchRequest,
  KnowledgeSearchResponse,
  AskRequest,
  AskResponse,
  SearchStatus,
} from "../types";

/**
 * Knowledge Base API — document upload, chunking, hybrid search
 * (pgvector + TF-IDF), and RAG question answering.
 */
export class KnowledgeAPI extends BaseAPI {
  // -- Documents -----------------------------------------------------------

  /** Upload a document (TXT, MD, CSV; max 10 MB). */
  async upload(file: Blob | File): Promise<Document> {
    const form = new FormData();
    form.append("file", file);
    return this._request<Document>("/api/knowledge/upload", {
      method: "POST",
      body: form,
    });
  }

  /** List user documents. */
  async listDocuments(): Promise<Document[]> {
    return this._get<Document[]>("/api/knowledge/documents");
  }

  /** List chunks for a document. */
  async listChunks(documentId: string): Promise<DocumentChunk[]> {
    return this._get<DocumentChunk[]>(`/api/knowledge/documents/${documentId}/chunks`);
  }

  /** Delete a document and all its chunks. */
  async deleteDocument(documentId: string): Promise<void> {
    return this._delete(`/api/knowledge/documents/${documentId}`);
  }

  // -- Search --------------------------------------------------------------

  /** Hybrid search (auto-detects best mode: TF-IDF, vector, or hybrid). */
  async search(data: KnowledgeSearchRequest): Promise<KnowledgeSearchResponse> {
    return this._post<KnowledgeSearchResponse>("/api/knowledge/search", data);
  }

  /** Vector-only search using pgvector. */
  async vectorSearch(data: KnowledgeSearchRequest): Promise<KnowledgeSearchResponse> {
    return this._post<KnowledgeSearchResponse>("/api/knowledge/search/vector", data);
  }

  /** Get available search modes and their status. */
  async searchStatus(): Promise<SearchStatus> {
    return this._get<SearchStatus>("/api/knowledge/search/status");
  }

  // -- RAG -----------------------------------------------------------------

  /** Ask a question — searches knowledge base and generates an AI answer. */
  async ask(data: AskRequest): Promise<AskResponse> {
    return this._post<AskResponse>("/api/knowledge/ask", data);
  }

  // -- Maintenance ---------------------------------------------------------

  /** Reindex all chunks with fresh embeddings. */
  async reindexEmbeddings(): Promise<{ status: string; reindexed: number }> {
    return this._post<{ status: string; reindexed: number }>("/api/knowledge/reindex-embeddings");
  }
}
