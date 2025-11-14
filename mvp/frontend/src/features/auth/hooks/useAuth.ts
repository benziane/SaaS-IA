/**
 * Auth Hooks - Grade S++
 * React Query hooks for authentication
 */

import { useQuery, type UseQueryResult } from '@tanstack/react-query';

import { QUERY_STALE_TIME, queryKeys } from '@/lib/queryClient';
import { useAuthStore } from '@/lib/store';

import { authApi } from '../api';
import type { User } from '../types';

/* ========================================================================
   USE CURRENT USER
   ======================================================================== */

/**
 * Get current user
 */
export function useCurrentUser(): UseQueryResult<User, Error> {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  
  return useQuery({
    queryKey: queryKeys.auth.me(),
    queryFn: () => authApi.getCurrentUser(),
    enabled: isAuthenticated,
    staleTime: QUERY_STALE_TIME.STANDARD,
    retry: false, // Don't retry on 401
  });
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default {
  useCurrentUser,
};

