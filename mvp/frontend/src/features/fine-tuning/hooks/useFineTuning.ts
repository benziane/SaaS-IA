'use client';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { assessQuality, createDataset, createDatasetFromSource, createJob, deleteDataset, evaluateModel, listDatasets, listJobs, listModels } from '../api';
import type { AvailableModel, FineTuneJob, ModelEvaluation, TrainingDataset } from '../types';

export function useFTDatasets() { return useQuery<TrainingDataset[]>({ queryKey: ['ft-datasets'], queryFn: listDatasets }); }
export function useCreateFTDataset() {
  const qc = useQueryClient();
  return useMutation<TrainingDataset, Error, { name: string; dataset_type?: string; samples?: { instruction: string; input: string; output: string }[] }>({
    mutationFn: createDataset, onSuccess: () => qc.invalidateQueries({ queryKey: ['ft-datasets'] }),
  });
}
export function useCreateFromSource() {
  const qc = useQueryClient();
  return useMutation<TrainingDataset, Error, { name: string; source_type: string; max_samples?: number }>({
    mutationFn: createDatasetFromSource, onSuccess: () => qc.invalidateQueries({ queryKey: ['ft-datasets'] }),
  });
}
export function useDeleteFTDataset() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({ mutationFn: deleteDataset, onSuccess: () => qc.invalidateQueries({ queryKey: ['ft-datasets'] }) });
}
export function useAssessQuality() {
  const qc = useQueryClient();
  return useMutation<TrainingDataset, Error, string>({ mutationFn: assessQuality, onSuccess: () => qc.invalidateQueries({ queryKey: ['ft-datasets'] }) });
}
export function useFTJobs() { return useQuery<FineTuneJob[]>({ queryKey: ['ft-jobs'], queryFn: listJobs }); }
export function useCreateFTJob() {
  const qc = useQueryClient();
  return useMutation<FineTuneJob, Error, { name: string; dataset_id: string; base_model?: string; hyperparams?: Record<string, unknown> }>({
    mutationFn: createJob, onSuccess: () => qc.invalidateQueries({ queryKey: ['ft-jobs'] }),
  });
}
export function useEvaluateModel() {
  return useMutation<ModelEvaluation, Error, { jobId: string; prompts: { prompt: string; expected_output: string }[] }>({
    mutationFn: ({ jobId, prompts }) => evaluateModel(jobId, prompts),
  });
}
export function useAvailableModels() { return useQuery<AvailableModel[]>({ queryKey: ['ft-models'], queryFn: listModels, staleTime: 3600000 }); }
