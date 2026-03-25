/**
 * Integration Hub API
 */

import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type {
  ConnectorCreateRequest,
  ConnectorTestResult,
  IntegrationConnector,
  IntegrationTrigger,
  ProviderInfo,
  TriggerCreateRequest,
  WebhookEvent,
} from './types';

const ENDPOINTS = {
  PROVIDERS: '/api/integrations/providers',
  CONNECTORS: '/api/integrations/connectors',
  CONNECTOR: (id: string) => `/api/integrations/connectors/${id}`,
  CONNECTOR_TEST: (id: string) => `/api/integrations/connectors/${id}/test`,
  CONNECTOR_EVENTS: (id: string) => `/api/integrations/connectors/${id}/events`,
  TRIGGERS: '/api/integrations/triggers',
  TRIGGER: (id: string) => `/api/integrations/triggers/${id}`,
} as const;

export async function listProviders(): Promise<ProviderInfo[]> {
  const response: AxiosResponse<ProviderInfo[]> = await apiClient.get(ENDPOINTS.PROVIDERS);
  return response.data;
}

export async function listConnectors(): Promise<IntegrationConnector[]> {
  const response: AxiosResponse<IntegrationConnector[]> = await apiClient.get(ENDPOINTS.CONNECTORS);
  return response.data;
}

export async function createConnector(data: ConnectorCreateRequest): Promise<IntegrationConnector> {
  const response: AxiosResponse<IntegrationConnector> = await apiClient.post(ENDPOINTS.CONNECTORS, data);
  return response.data;
}

export async function getConnector(id: string): Promise<IntegrationConnector> {
  const response: AxiosResponse<IntegrationConnector> = await apiClient.get(ENDPOINTS.CONNECTOR(id));
  return response.data;
}

export async function deleteConnector(id: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.CONNECTOR(id));
}

export async function testConnector(id: string): Promise<ConnectorTestResult> {
  const response: AxiosResponse<ConnectorTestResult> = await apiClient.post(ENDPOINTS.CONNECTOR_TEST(id));
  return response.data;
}

export async function listEvents(connectorId: string, limit?: number): Promise<WebhookEvent[]> {
  const params = limit ? { limit } : {};
  const response: AxiosResponse<WebhookEvent[]> = await apiClient.get(ENDPOINTS.CONNECTOR_EVENTS(connectorId), { params });
  return response.data;
}

export async function listTriggers(connectorId?: string): Promise<IntegrationTrigger[]> {
  const params = connectorId ? { connector_id: connectorId } : {};
  const response: AxiosResponse<IntegrationTrigger[]> = await apiClient.get(ENDPOINTS.TRIGGERS, { params });
  return response.data;
}

export async function createTrigger(data: TriggerCreateRequest): Promise<IntegrationTrigger> {
  const response: AxiosResponse<IntegrationTrigger> = await apiClient.post(ENDPOINTS.TRIGGERS, data);
  return response.data;
}

export async function deleteTrigger(id: string): Promise<void> {
  await apiClient.delete(ENDPOINTS.TRIGGER(id));
}
