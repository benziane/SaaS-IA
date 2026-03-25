/**
 * Integration Hub hooks
 */

'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createConnector,
  createTrigger,
  deleteConnector,
  deleteTrigger,
  listConnectors,
  listEvents,
  listProviders,
  listTriggers,
  testConnector,
} from '../api';
import type {
  ConnectorCreateRequest,
  ConnectorTestResult,
  IntegrationConnector,
  IntegrationTrigger,
  ProviderInfo,
  TriggerCreateRequest,
  WebhookEvent,
} from '../types';

export function useProviders() {
  return useQuery<ProviderInfo[]>({
    queryKey: ['integration-providers'],
    queryFn: listProviders,
    staleTime: 5 * 60 * 1000, // providers rarely change
  });
}

export function useConnectors() {
  return useQuery<IntegrationConnector[]>({
    queryKey: ['integration-connectors'],
    queryFn: listConnectors,
  });
}

export function useCreateConnector() {
  const queryClient = useQueryClient();
  return useMutation<IntegrationConnector, Error, ConnectorCreateRequest>({
    mutationFn: createConnector,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration-connectors'] });
    },
  });
}

export function useDeleteConnector() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteConnector,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration-connectors'] });
    },
  });
}

export function useTestConnector() {
  return useMutation<ConnectorTestResult, Error, string>({
    mutationFn: testConnector,
  });
}

export function useEvents(connectorId: string | null) {
  return useQuery<WebhookEvent[]>({
    queryKey: ['integration-events', connectorId],
    queryFn: () => listEvents(connectorId!),
    enabled: !!connectorId,
  });
}

export function useTriggers(connectorId?: string | null) {
  return useQuery<IntegrationTrigger[]>({
    queryKey: ['integration-triggers', connectorId],
    queryFn: () => listTriggers(connectorId || undefined),
  });
}

export function useCreateTrigger() {
  const queryClient = useQueryClient();
  return useMutation<IntegrationTrigger, Error, TriggerCreateRequest>({
    mutationFn: createTrigger,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration-triggers'] });
    },
  });
}

export function useDeleteTrigger() {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: deleteTrigger,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration-triggers'] });
    },
  });
}
