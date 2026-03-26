import { BaseAPI } from "./base";
import { PdfResult } from "../types";

/**
 * PDF Processor API — extract text and tables from PDF files using
 * PyMuPDF + pdfplumber.
 */
export class PDFAPI extends BaseAPI {
  /** Upload and process a PDF file. */
  async process(file: Blob | File): Promise<PdfResult> {
    const form = new FormData();
    form.append("file", file);
    return this._request<PdfResult>("/api/pdf/process", {
      method: "POST",
      body: form,
    });
  }

  /** List processed PDFs. */
  async list(): Promise<PdfResult[]> {
    return this._get<PdfResult[]>("/api/pdf/");
  }

  /** Get a processed PDF result. */
  async get(id: string): Promise<PdfResult> {
    return this._get<PdfResult>(`/api/pdf/${id}`);
  }

  /** Delete a processed PDF. */
  async delete(id: string): Promise<void> {
    return this._delete(`/api/pdf/${id}`);
  }
}
