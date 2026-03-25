'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { askData, autoAnalyze, deleteDataset, listAnalyses, listDatasets, uploadDataset } from '../api';
import type { DataAnalysis, Dataset } from '../types';

export function useDatasets() { return useQuery<Dataset[]>({ queryKey: ['datasets'], queryFn: listDatasets }); }
export function useUploadDataset() {
  const qc = useQueryClient();
  return useMutation<Dataset, Error, File>({ mutationFn: uploadDataset, onSuccess: () => qc.invalidateQueries({ queryKey: ['datasets'] }) });
}
export function useDeleteDataset() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({ mutationFn: deleteDataset, onSuccess: () => qc.invalidateQueries({ queryKey: ['datasets'] }) });
}
export function useAskData(datasetId: string) {
  const qc = useQueryClient();
  return useMutation<DataAnalysis, Error, { question: string; analysisType?: string }>({
    mutationFn: ({ question, analysisType }) => askData(datasetId, question, analysisType),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['analyses', datasetId] }),
  });
}
export function useAutoAnalyze(datasetId: string) {
  const qc = useQueryClient();
  return useMutation<DataAnalysis, Error, string>({
    mutationFn: (depth) => autoAnalyze(datasetId, depth),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['analyses', datasetId] }),
  });
}
export function useAnalyses(datasetId: string | null) {
  return useQuery<DataAnalysis[]>({ queryKey: ['analyses', datasetId], queryFn: () => listAnalyses(datasetId!), enabled: !!datasetId });
}
