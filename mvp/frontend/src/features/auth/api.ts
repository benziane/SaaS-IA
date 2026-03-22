/**
 * Auth API - Grade S++
 * Authentication API calls
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type { LoginRequest, LoginResponse, RegisterRequest, UpdateProfileRequest, ChangePasswordRequest, User } from './types';

/* ========================================================================
   API ENDPOINTS
   ======================================================================== */

const AUTH_ENDPOINTS = {
  REGISTER: '/api/auth/register',
  LOGIN: '/api/auth/login',
  REFRESH: '/api/auth/refresh',
  ME: '/api/auth/me',
  PROFILE: '/api/auth/profile',
  PASSWORD: '/api/auth/password',
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
 * Refresh the access token using a valid refresh token.
 * Returns a new token pair (access + rotated refresh).
 */
export async function refreshToken(refreshTokenValue: string): Promise<LoginResponse> {
  const response: AxiosResponse<LoginResponse> = await apiClient.post(
    AUTH_ENDPOINTS.REFRESH,
    { refresh_token: refreshTokenValue },
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

/**
 * Update user profile (full_name)
 */
export async function updateProfile(data: UpdateProfileRequest): Promise<User> {
  const response: AxiosResponse<User> = await apiClient.put(AUTH_ENDPOINTS.PROFILE, data);
  return response.data;
}

/**
 * Change user password
 */
export async function changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
  const response: AxiosResponse<{ message: string }> = await apiClient.put(AUTH_ENDPOINTS.PASSWORD, data);
  return response.data;
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export const authApi = {
  register,
  login,
  refreshToken,
  getCurrentUser,
  updateProfile,
  changePassword,
} as const;

export default authApi;

