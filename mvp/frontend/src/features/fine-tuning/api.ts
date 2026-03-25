import apiClient from '@/lib/apiClient';
import type { AvailableModel, FineTuneJob, ModelEvaluation, TrainingDataset } from './types';

export const createDataset = async (data: { name: string; dataset_type?: string; samples?: { instruction: string; input: string; output: string }[] }): Promise<TrainingDataset> =>
  (await apiClient.post('/api/fine-tuning/datasets', data)).data;
export const createDatasetFromSource = async (data: { name: string; source_type: string; max_samples?: number }): Promise<TrainingDataset> =>
  (await apiClient.post('/api/fine-tuning/datasets/from-source', data)).data;
export const listDatasets = async (): Promise<TrainingDataset[]> => (await apiClient.get('/api/fine-tuning/datasets')).data;
export const deleteDataset = async (id: string): Promise<void> => { await apiClient.delete(`/api/fine-tuning/datasets/${id}`); };
export const assessQuality = async (id: string): Promise<TrainingDataset> => (await apiClient.post(`/api/fine-tuning/datasets/${id}/assess-quality`)).data;
export const createJob = async (data: { name: string; dataset_id: string; base_model?: string; hyperparams?: Record<string, unknown> }): Promise<FineTuneJob> =>
  (await apiClient.post('/api/fine-tuning/jobs', data)).data;
export const listJobs = async (): Promise<FineTuneJob[]> => (await apiClient.get('/api/fine-tuning/jobs')).data;
export const getJob = async (id: string): Promise<FineTuneJob> => (await apiClient.get(`/api/fine-tuning/jobs/${id}`)).data;
export const evaluateModel = async (jobId: string, prompts: { prompt: string; expected_output: string }[]): Promise<ModelEvaluation> =>
  (await apiClient.post(`/api/fine-tuning/jobs/${jobId}/evaluate`, { test_prompts: prompts })).data;
export const listModels = async (): Promise<AvailableModel[]> => (await apiClient.get('/api/fine-tuning/models')).data;
