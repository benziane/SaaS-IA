/**
 * Knowledge Base hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { askQuestion, deleteDocument, listDocuments, searchDocuments, uploadDocument } from '../api';
import type { AskResponse, KBDocument, SearchResponse } from '../types';

export function useDocuments() {
  return useQuery<KBDocument[]>({
    queryKey: ['knowledge', 'documents'],
    queryFn: listDocuments,
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation<KBDocument, Error, File>({
    mutationFn: (file) => uploadDocument(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['knowledge', 'documents'] }),
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteDocument,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['knowledge', 'documents'] }),
  });
}

export function useSearch() {
  return useMutation<SearchResponse, Error, string>({
    mutationFn: (query) => searchDocuments(query),
  });
}

export function useAsk() {
  return useMutation<AskResponse, Error, string>({
    mutationFn: askQuestion,
  });
}
