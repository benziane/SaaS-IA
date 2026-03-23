import type { AxiosResponse } from 'axios';
import apiClient from '@/lib/apiClient';
import type { CostAlert, CostDashboard } from './types';

export async function getCostDashboard(days: number = 30): Promise<CostDashboard> {
  const response: AxiosResponse<CostDashboard> = await apiClient.get(`/api/costs/dashboard?days=${days}`);
  return response.data;
}

export async function getCostAlerts(): Promise<CostAlert[]> {
  const response: AxiosResponse<CostAlert[]> = await apiClient.get('/api/costs/alerts');
  return response.data;
}

export function getExportUrl(days: number): string {
  return `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004'}/api/costs/export?days=${days}`;
}

export const costApi = { getCostDashboard, getCostAlerts, getExportUrl } as const;
export default costApi;
