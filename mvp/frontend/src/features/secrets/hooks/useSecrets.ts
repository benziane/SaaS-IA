/**
 * Secrets hooks
 * React Query hooks for secret rotation data
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  completeRotation,
  getAlerts,
  getHealth,
  getSecrets,
  markCompromised,
  registerSecret,
  startRotation,
} from '../api';
import type {
  SecretAlert,
  SecretHealth,
  SecretRegisterRequest,
  SecretRegistration,
} from '../types';

const SECRETS_KEYS = {
  all: ['secrets'] as const,
  list: ['secrets', 'list'] as const,
  alerts: ['secrets', 'alerts'] as const,
  health: ['secrets', 'health'] as const,
};

export function useSecrets() {
  return useQuery<SecretRegistration[]>({
    queryKey: SECRETS_KEYS.list,
    queryFn: getSecrets,
    staleTime: 30 * 1000,
  });
}

export function useSecretAlerts() {
  return useQuery<SecretAlert[]>({
    queryKey: SECRETS_KEYS.alerts,
    queryFn: getAlerts,
    staleTime: 60 * 1000,
  });
}

export function useSecretHealth() {
  return useQuery<SecretHealth>({
    queryKey: SECRETS_KEYS.health,
    queryFn: getHealth,
    staleTime: 60 * 1000,
  });
}

export function useRegisterSecret() {
  const queryClient = useQueryClient();
  return useMutation<{ message: string }, Error, SecretRegisterRequest>({
    mutationFn: registerSecret,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SECRETS_KEYS.all });
    },
  });
}

export function useStartRotation() {
  const queryClient = useQueryClient();
  return useMutation<{ message: string }, Error, { name: string; hint?: string }>({
    mutationFn: ({ name, hint }) => startRotation(name, hint ? { hint } : undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SECRETS_KEYS.all });
    },
  });
}

export function useCompleteRotation() {
  const queryClient = useQueryClient();
  return useMutation<{ message: string }, Error, string>({
    mutationFn: completeRotation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SECRETS_KEYS.all });
    },
  });
}

export function useMarkCompromised() {
  const queryClient = useQueryClient();
  return useMutation<{ message: string }, Error, string>({
    mutationFn: markCompromised,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: SECRETS_KEYS.all });
    },
  });
}
