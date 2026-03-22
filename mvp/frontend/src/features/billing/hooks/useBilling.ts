/**
 * Billing hooks
 * React Query hooks for billing data
 */

'use client';

import { useQuery } from '@tanstack/react-query';

import { getPlans, getQuota } from '../api';
import type { Plan, UserQuota } from '../types';

export function usePlans() {
  return useQuery<Plan[]>({
    queryKey: ['billing', 'plans'],
    queryFn: getPlans,
    staleTime: 5 * 60 * 1000,
  });
}

export function useQuota() {
  return useQuery<UserQuota>({
    queryKey: ['billing', 'quota'],
    queryFn: getQuota,
    refetchInterval: 30 * 1000,
  });
}
