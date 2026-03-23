'use client';

import { useQuery } from '@tanstack/react-query';
import { getCostAlerts, getCostDashboard } from '../api';
import type { CostAlert, CostDashboard } from '../types';

export function useCostDashboard(days: number = 30) {
  return useQuery<CostDashboard>({
    queryKey: ['costs', 'dashboard', days],
    queryFn: () => getCostDashboard(days),
    staleTime: 60 * 1000,
  });
}

export function useCostAlerts() {
  return useQuery<CostAlert[]>({
    queryKey: ['cost-alerts'],
    queryFn: getCostAlerts,
    staleTime: 120 * 1000,
  });
}
