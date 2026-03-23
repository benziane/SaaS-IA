import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type { AgentRun, SentimentResponse } from './types';

export async function runAgent(instruction: string): Promise<AgentRun> {
  const response: AxiosResponse<AgentRun> = await apiClient.post('/api/agents/run', { instruction });
  return response.data;
}

export async function listAgentRuns(): Promise<AgentRun[]> {
  const response: AxiosResponse<AgentRun[]> = await apiClient.get('/api/agents/runs');
  return response.data;
}

export async function getAgentRun(id: string): Promise<AgentRun> {
  const response: AxiosResponse<AgentRun> = await apiClient.get(`/api/agents/runs/${id}`);
  return response.data;
}

export async function analyzeSentiment(text: string): Promise<SentimentResponse> {
  const response: AxiosResponse<SentimentResponse> = await apiClient.post('/api/sentiment/analyze', { text });
  return response.data;
}

export async function analyzeTranscriptionSentiment(transcriptionId: string): Promise<SentimentResponse> {
  const response: AxiosResponse<SentimentResponse> = await apiClient.post('/api/sentiment/transcription', { transcription_id: transcriptionId });
  return response.data;
}
