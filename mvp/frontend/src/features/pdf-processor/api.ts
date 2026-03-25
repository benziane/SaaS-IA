import apiClient from '@/lib/apiClient';
import type {
  PDFCompareResult,
  PDFExportResult,
  PDFQueryResponse,
  PDFRead,
  PDFTableResult,
  PDFUploadResponse,
} from './types';

export const uploadPDF = async (file: File): Promise<PDFUploadResponse> => {
  const fd = new FormData();
  fd.append('file', file);
  return (await apiClient.post('/api/pdf/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })).data;
};

export const listPDFs = async (): Promise<PDFUploadResponse[]> =>
  (await apiClient.get('/api/pdf/')).data;

export const getPDF = async (id: string): Promise<PDFRead> =>
  (await apiClient.get(`/api/pdf/${id}`)).data;

export const deletePDF = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/pdf/${id}`);
};

export const summarizePDF = async (id: string, style = 'executive'): Promise<{ summary: string; style: string; provider?: string }> =>
  (await apiClient.post(`/api/pdf/${id}/summarize`, { style })).data;

export const extractKeywords = async (id: string): Promise<{ keywords: string[] }> =>
  (await apiClient.post(`/api/pdf/${id}/keywords`)).data;

export const queryPDF = async (id: string, question: string): Promise<PDFQueryResponse> =>
  (await apiClient.post(`/api/pdf/${id}/query`, { question, pdf_id: id })).data;

export const exportPDF = async (id: string, format: string): Promise<PDFExportResult> =>
  (await apiClient.get(`/api/pdf/${id}/export/${format}`)).data;

export const comparePDFs = async (pdfIds: string[], comparisonType = 'content'): Promise<PDFCompareResult> =>
  (await apiClient.post('/api/pdf/compare', { pdf_ids: pdfIds, comparison_type: comparisonType })).data;

export const extractTables = async (id: string): Promise<PDFTableResult> =>
  (await apiClient.post(`/api/pdf/${id}/tables`)).data;

export const ocrPDF = async (id: string): Promise<{ text: string; pages?: unknown[]; total_pages?: number }> =>
  (await apiClient.post(`/api/pdf/${id}/ocr`)).data;
