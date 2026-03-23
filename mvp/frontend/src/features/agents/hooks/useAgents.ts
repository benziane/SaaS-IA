'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { analyzeSentiment, getAgentRun, listAgentRuns, runAgent } from '../api';
import type { AgentRun, SentimentResponse } from '../types';

export function useAgentRuns() {
  return useQuery<AgentRun[]>({ queryKey: ['agents'], queryFn: listAgentRuns });
}

export function useAgentRun(id: string) {
  return useQuery<AgentRun>({ queryKey: ['agents', id], queryFn: () => getAgentRun(id), enabled: !!id, refetchInterval: 2000 });
}

export function useRunAgent() {
  const qc = useQueryClient();
  return useMutation<AgentRun, Error, string>({
    mutationFn: runAgent,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['agents'] }); },
  });
}

export function useAnalyzeSentiment() {
  return useMutation<SentimentResponse, Error, string>({ mutationFn: analyzeSentiment });
}
