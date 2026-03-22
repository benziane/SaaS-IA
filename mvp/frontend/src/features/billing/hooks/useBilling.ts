/**
 * Billing hooks
 * React Query hooks for billing data
 */

'use client';

import { useMutation, useQuery } from '@tanstack/react-query';

import { createCheckout, createPortal, getPlans, getQuota } from '../api';
import type { CheckoutResponse, Plan, PortalResponse, UserQuota } from '../types';

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

export function useCheckout() {
  return useMutation<CheckoutResponse, Error, string>({
    mutationFn: createCheckout,
    onSuccess: (data) => {
      window.location.href = data.checkout_url;
    },
  });
}

export function usePortal() {
  return useMutation<PortalResponse, Error, void>({
    mutationFn: createPortal,
    onSuccess: (data) => {
      window.location.href = data.portal_url;
    },
  });
}
