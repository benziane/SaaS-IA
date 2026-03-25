'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  comparePDFs,
  deletePDF,
  exportPDF,
  extractKeywords,
  extractTables,
  getPDF,
  listPDFs,
  ocrPDF,
  queryPDF,
  summarizePDF,
  uploadPDF,
} from '../api';
import type {
  PDFCompareResult,
  PDFExportResult,
  PDFQueryResponse,
  PDFRead,
  PDFTableResult,
  PDFUploadResponse,
} from '../types';

export function usePDFs() {
  return useQuery<PDFUploadResponse[]>({ queryKey: ['pdfs'], queryFn: listPDFs });
}

export function usePDF(id: string | null) {
  return useQuery<PDFRead>({
    queryKey: ['pdf', id],
    queryFn: () => getPDF(id!),
    enabled: !!id,
  });
}

export function useUploadPDF() {
  const qc = useQueryClient();
  return useMutation<PDFUploadResponse, Error, File>({
    mutationFn: uploadPDF,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pdfs'] }),
  });
}

export function useDeletePDF() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deletePDF,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pdfs'] }),
  });
}

export function useSummarizePDF(id: string) {
  const qc = useQueryClient();
  return useMutation<{ summary: string; style: string; provider?: string }, Error, string>({
    mutationFn: (style) => summarizePDF(id, style),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pdf', id] }),
  });
}

export function useExtractKeywords(id: string) {
  const qc = useQueryClient();
  return useMutation<{ keywords: string[] }, Error, void>({
    mutationFn: () => extractKeywords(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pdf', id] }),
  });
}

export function useQueryPDF(id: string) {
  return useMutation<PDFQueryResponse, Error, string>({
    mutationFn: (question) => queryPDF(id, question),
  });
}

export function useExportPDF(id: string) {
  return useMutation<PDFExportResult, Error, string>({
    mutationFn: (format) => exportPDF(id, format),
  });
}

export function useComparePDFs() {
  return useMutation<PDFCompareResult, Error, { pdfIds: string[]; comparisonType?: string }>({
    mutationFn: ({ pdfIds, comparisonType }) => comparePDFs(pdfIds, comparisonType),
  });
}

export function useExtractTables(id: string) {
  return useMutation<PDFTableResult, Error, void>({
    mutationFn: () => extractTables(id),
  });
}

export function useOCRPDF(id: string) {
  const qc = useQueryClient();
  return useMutation<{ text: string; pages?: unknown[]; total_pages?: number }, Error, void>({
    mutationFn: () => ocrPDF(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pdf', id] }),
  });
}
