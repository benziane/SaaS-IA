/**
 * Billing API
 * API calls for billing and quota features
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type { CheckoutResponse, Plan, PortalResponse, UserQuota } from './types';

const BILLING_ENDPOINTS = {
  PLANS: '/api/billing/plans',
  QUOTA: '/api/billing/quota',
} as const;

export async function getPlans(): Promise<Plan[]> {
  const response: AxiosResponse<Plan[]> = await apiClient.get(
    BILLING_ENDPOINTS.PLANS
  );
  return response.data;
}

export async function getQuota(): Promise<UserQuota> {
  const response: AxiosResponse<UserQuota> = await apiClient.get(
    BILLING_ENDPOINTS.QUOTA
  );
  return response.data;
}

export async function createCheckout(planName: string): Promise<CheckoutResponse> {
  const response: AxiosResponse<CheckoutResponse> = await apiClient.post(
    '/api/billing/checkout',
    { plan_name: planName }
  );
  return response.data;
}

export async function createPortal(): Promise<PortalResponse> {
  const response: AxiosResponse<PortalResponse> = await apiClient.post(
    '/api/billing/portal'
  );
  return response.data;
}

export const billingApi = {
  getPlans,
  getQuota,
  createCheckout,
  createPortal,
} as const;

export default billingApi;
