/**
 * Auth API - Grade S++
 * Authentication API calls
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type { LoginRequest, LoginResponse, RegisterRequest, User } from './types';

/* ========================================================================
   API ENDPOINTS
   ======================================================================== */

const AUTH_ENDPOINTS = {
  REGISTER: '/api/auth/register',
  LOGIN: '/api/auth/login',
  ME: '/api/auth/me',
} as const;

/* ========================================================================
   API FUNCTIONS
   ======================================================================== */

/**
 * Register a new user
 */
export async function register(data: RegisterRequest): Promise<User> {
  const response: AxiosResponse<User> = await apiClient.post(AUTH_ENDPOINTS.REGISTER, data);
  return response.data;
}

/**
 * Login user
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  // FastAPI OAuth2 expects form data
  const formData = new URLSearchParams();
  formData.append('username', data.email);
  formData.append('password', data.password);
  
  const response: AxiosResponse<LoginResponse> = await apiClient.post(
    AUTH_ENDPOINTS.LOGIN,
    formData,
    {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    }
  );
  
  return response.data;
}

/**
 * Get current user
 */
export async function getCurrentUser(): Promise<User> {
  const response: AxiosResponse<User> = await apiClient.get(AUTH_ENDPOINTS.ME);
  return response.data;
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export const authApi = {
  register,
  login,
  getCurrentUser,
} as const;

export default authApi;

