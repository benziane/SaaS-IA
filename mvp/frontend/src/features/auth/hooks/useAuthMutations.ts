/**
 * Auth Mutations - Grade S++
 * React Query mutations for authentication
 */

import { useMutation, useQueryClient, type UseMutationResult } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

import { extractErrorMessage } from '@/lib/apiClient';
import { queryKeys } from '@/lib/queryClient';
import { useAuthStore } from '@/lib/store';

import { authApi } from '../api';
import type { LoginRequest, LoginResponse, RegisterRequest, User } from '../types';

/* ========================================================================
   USE REGISTER
   ======================================================================== */

/**
 * Register mutation
 */
export function useRegister(): UseMutationResult<User, Error, RegisterRequest> {
  const router = useRouter();
  
  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: (user) => {
      toast.success('Account created successfully', {
        description: `Welcome, ${user.email}!`,
      });
      
      // Redirect to login
      router.push('/login');
    },
    onError: (error: Error) => {
      toast.error('Failed to create account', {
        description: extractErrorMessage(error),
      });
    },
  });
}

/* ========================================================================
   USE LOGIN
   ======================================================================== */

/**
 * Login mutation
 */
export function useLogin(): UseMutationResult<LoginResponse, Error, LoginRequest> {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { login: loginStore } = useAuthStore();
  
  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: async (response, variables) => {
      // Store token FIRST (localStorage + Cookie for middleware)
      localStorage.setItem('auth_token', response.access_token);
      document.cookie = `auth_token=${response.access_token}; path=/; max-age=1800; SameSite=Lax`;
      
      // Get user data (now with token in headers)
      const user = await authApi.getCurrentUser();
      
      // Update store
      loginStore(user, response.access_token);
      
      // Invalidate auth queries
      await queryClient.invalidateQueries({ queryKey: queryKeys.auth.all });
      
      toast.success('Login successful', {
        description: `Welcome back, ${user.email}!`,
      });
      
      // Redirect to dashboard
      router.push('/dashboard');
    },
    onError: (error: Error) => {
      toast.error('Failed to login', {
        description: extractErrorMessage(error),
      });
    },
  });
}

/* ========================================================================
   USE LOGOUT
   ======================================================================== */

/**
 * Logout mutation
 */
export function useLogout(): UseMutationResult<void, Error, void> {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { logout: logoutStore } = useAuthStore();
  
  return useMutation({
    mutationFn: async () => {
      // No API call needed for logout (JWT is stateless)
      return Promise.resolve();
    },
    onSuccess: () => {
      // Clear store
      logoutStore();
      
      // Clear cookie
      document.cookie = 'auth_token=; path=/; max-age=0';
      
      // Clear all queries
      queryClient.clear();
      
      toast.success('Logged out successfully');
      
      // Redirect to login
      router.push('/login');
    },
    onError: (error: Error) => {
      toast.error('Failed to logout', {
        description: extractErrorMessage(error),
      });
    },
  });
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default {
  useRegister,
  useLogin,
  useLogout,
};

