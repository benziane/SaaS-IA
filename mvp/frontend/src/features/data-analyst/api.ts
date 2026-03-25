import apiClient from '@/lib/apiClient';
import type { DataAnalysis, Dataset } from './types';

export const uploadDataset = async (file: File): Promise<Dataset> => {
  const fd = new FormData(); fd.append('file', file);
  return (await apiClient.post('/api/data/datasets', fd, { headers: { 'Content-Type': 'multipart/form-data' } })).data;
};
export const listDatasets = async (): Promise<Dataset[]> => (await apiClient.get('/api/data/datasets')).data;
export const getDataset = async (id: string): Promise<Dataset> => (await apiClient.get(`/api/data/datasets/${id}`)).data;
export const deleteDataset = async (id: string): Promise<void> => { await apiClient.delete(`/api/data/datasets/${id}`); };
export const askData = async (datasetId: string, question: string, analysisType = 'general'): Promise<DataAnalysis> =>
  (await apiClient.post(`/api/data/datasets/${datasetId}/ask`, { question, analysis_type: analysisType })).data;
export const autoAnalyze = async (datasetId: string, depth = 'standard'): Promise<DataAnalysis> =>
  (await apiClient.post(`/api/data/datasets/${datasetId}/auto-analyze`, { depth })).data;
export const listAnalyses = async (datasetId: string): Promise<DataAnalysis[]> =>
  (await apiClient.get(`/api/data/datasets/${datasetId}/analyses`)).data;
