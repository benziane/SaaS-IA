/**
 * API Client - Grade S++
 * Axios instance with interceptors, error handling, and retry logic
 */

import axios, { type AxiosError, type AxiosRequestConfig, type AxiosResponse } from 'axios';

/* ========================================================================
   CONFIGURATION
   ======================================================================== */

// In dev, use Next.js rewrite proxy (same origin = no CORS issues)
// In production, set NEXT_PUBLIC_API_URL to the backend URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
const API_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;

/* ========================================================================
   AXIOS INSTANCE
   ======================================================================== */

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

/* ========================================================================
   REQUEST INTERCEPTOR
   ======================================================================== */

apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    
    // Add request timestamp for monitoring
    if (config.headers) {
      config.headers['X-Request-Time'] = new Date().toISOString();
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/* ========================================================================
   RESPONSE INTERCEPTOR - with JWT refresh token support
   ======================================================================== */

/**
 * Flag to prevent infinite refresh loops.
 * When a refresh is already in progress, subsequent 401s will wait
 * for the same refresh promise instead of triggering new ones.
 */
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

/**
 * Attempt to refresh the access token using the stored refresh token.
 * Returns the new access token on success, or null on failure.
 */
async function attemptTokenRefresh(): Promise<string | null> {
  const storedRefreshToken = localStorage.getItem('auth_refresh_token');

  if (!storedRefreshToken) {
    return null;
  }

  try {
    // Use a raw axios call to avoid triggering our own interceptors
    const response = await axios.post(
      `${API_BASE_URL}/api/auth/refresh`,
      { refresh_token: storedRefreshToken },
      { headers: { 'Content-Type': 'application/json' } },
    );

    const { access_token, refresh_token } = response.data;

    // Persist the new token pair
    localStorage.setItem('auth_token', access_token);
    localStorage.setItem('auth_refresh_token', refresh_token);

    // Update the cookie used by middleware
    document.cookie = `auth_token=${access_token}; path=/; max-age=1800; SameSite=Lax`;

    return access_token;
  } catch {
    return null;
  }
}

/**
 * Clear all auth data and redirect to login.
 */
function clearAuthAndRedirect(): void {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_refresh_token');
  localStorage.removeItem('auth_user');
  document.cookie = 'auth_token=; path=/; max-age=0';
  window.location.href = '/login';
}

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & {
      _retry?: number;
      _isRefreshAttempt?: boolean;
    };

    // Handle 401 Unauthorized - attempt token refresh before giving up
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      // If this request was itself a refresh attempt, avoid infinite loop
      if (originalRequest._isRefreshAttempt) {
        clearAuthAndRedirect();
        return Promise.reject(error);
      }

      // If a refresh is already in progress, wait for it
      if (isRefreshing && refreshPromise) {
        const newToken = await refreshPromise;

        if (newToken && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return apiClient(originalRequest);
        }

        clearAuthAndRedirect();
        return Promise.reject(error);
      }

      // Start a new refresh cycle
      isRefreshing = true;
      refreshPromise = attemptTokenRefresh().finally(() => {
        isRefreshing = false;
        refreshPromise = null;
      });

      const newToken = await refreshPromise;

      if (newToken) {
        // Retry the original request with the fresh token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return apiClient(originalRequest);
      }

      // Refresh failed - clear auth and redirect
      clearAuthAndRedirect();
      return Promise.reject(error);
    }

    // Retry logic for 5xx errors and network errors
    if (
      originalRequest &&
      !originalRequest._retry &&
      (error.response?.status ? error.response.status >= 500 : true)
    ) {
      originalRequest._retry = (originalRequest._retry || 0) + 1;

      if (originalRequest._retry <= MAX_RETRIES) {
        // Exponential backoff: 1s, 2s, 4s
        const delay = Math.pow(2, originalRequest._retry - 1) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));

        return apiClient(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);

/* ========================================================================
   ERROR HANDLING UTILITIES
   ======================================================================== */

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown;
}

/**
 * Extract error message from Axios error
 */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string | Array<{ msg: string; loc: string[] }> }>;
    
    // FastAPI validation error (array of errors)
    if (Array.isArray(axiosError.response?.data?.detail)) {
      return axiosError.response.data.detail
        .map((err) => `${err.loc.slice(1).join('.')}: ${err.msg}`)
        .join(', ');
    }
    
    // FastAPI simple error (string)
    if (typeof axiosError.response?.data?.detail === 'string') {
      return axiosError.response.data.detail;
    }
    
    // HTTP status text
    if (axiosError.response?.statusText) {
      return axiosError.response.statusText;
    }
    
    // Network error
    if (axiosError.message) {
      return axiosError.message;
    }
  }
  
  // Unknown error
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
}

/**
 * Convert Axios error to ApiError
 */
export function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    return {
      message: extractErrorMessage(error),
      status: error.response?.status,
      code: error.code,
      details: error.response?.data,
    };
  }
  
  return {
    message: extractErrorMessage(error),
  };
}

/**
 * Check if error should be retried
 */
export function shouldRetry(error: unknown, failureCount: number): boolean {
  // Max retries reached
  if (failureCount >= MAX_RETRIES) {
    return false;
  }
  
  // Axios error
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    
    // Retry on 5xx server errors
    if (status && status >= 500) {
      return true;
    }
    
    // Retry on specific 4xx errors
    if (status === 408 || status === 429) {
      return true;
    }
    
    // Retry on network errors
    if (!status) {
      return true;
    }
    
    // Don't retry on other 4xx errors
    return false;
  }
  
  // Retry on unknown errors
  return true;
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default apiClient;

