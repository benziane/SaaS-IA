/**
 * TanStack Query Client Configuration - Grade S++
 * @see https://tanstack.com/query/latest/docs/react/guides/query-client
 */

import { QueryClient } from '@tanstack/react-query';

import { shouldRetry } from './apiClient';

/* ========================================================================
   STALE TIME CONFIGURATION
   ======================================================================== */

export const QUERY_STALE_TIME = {
  CRITICAL: 30 * 1000, // 30 seconds - Data that changes frequently
  STANDARD: 5 * 60 * 1000, // 5 minutes - Normal data
  STABLE: 30 * 60 * 1000, // 30 minutes - Data that rarely changes
  STATIC: Infinity, // Never stale - Static data
} as const;

export const QUERY_CACHE_TIME = {
  SHORT: 5 * 60 * 1000, // 5 minutes
  MEDIUM: 30 * 60 * 1000, // 30 minutes
  LONG: 60 * 60 * 1000, // 1 hour
  VERY_LONG: 24 * 60 * 60 * 1000, // 24 hours
} as const;

/* ========================================================================
   QUERY CLIENT
   ======================================================================== */

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      /* Stale Time - Grade S++ */
      staleTime: QUERY_STALE_TIME.STANDARD,
      
      /* Cache Time - Grade S++ */
      gcTime: QUERY_CACHE_TIME.MEDIUM, // Previously 'cacheTime' in v4
      
      /* Retry Configuration - Grade S++ */
      retry: (failureCount, error) => shouldRetry(error, failureCount),
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      
      /* Refetch Configuration */
      refetchOnWindowFocus: true,
      refetchOnReconnect: true,
      refetchOnMount: true,
      
      /* Network Mode */
      networkMode: 'online',
      
      /* Error Handling */
      throwOnError: false,
    },
    mutations: {
      /* Retry Configuration - Grade S++ */
      retry: false, // Don't retry mutations by default
      
      /* Network Mode */
      networkMode: 'online',
      
      /* Error Handling */
      throwOnError: false,
    },
  },
});

/* ========================================================================
   QUERY KEY FACTORY
   ======================================================================== */

/**
 * Query Keys Factory Pattern - Grade S++
 * Centralized query keys management
 */
export const queryKeys = {
  /* Auth */
  auth: {
    all: ['auth'] as const,
    me: () => [...queryKeys.auth.all, 'me'] as const,
  },
  
  /* Transcriptions */
  transcriptions: {
    all: ['transcriptions'] as const,
    lists: () => [...queryKeys.transcriptions.all, 'list'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.transcriptions.lists(), filters] as const,
    details: () => [...queryKeys.transcriptions.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.transcriptions.details(), id] as const,
  },

  /* Conversations */
  conversations: {
    all: ['conversations'] as const,
    lists: () => [...queryKeys.conversations.all, 'list'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.conversations.lists(), filters] as const,
    details: () => [...queryKeys.conversations.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.conversations.details(), id] as const,
  },
} as const;

/* ========================================================================
   UTILITY FUNCTIONS
   ======================================================================== */

/**
 * Invalidate all queries
 */
export async function invalidateAll(): Promise<void> {
  await queryClient.invalidateQueries();
}

/**
 * Clear all caches
 */
export function clearAllCaches(): void {
  queryClient.clear();
}

/**
 * Prefetch query
 */
export async function prefetchQuery<T>(
  queryKey: readonly unknown[],
  queryFn: () => Promise<T>,
  staleTime?: number
): Promise<void> {
  await queryClient.prefetchQuery({
    queryKey,
    queryFn,
    staleTime,
  });
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default queryClient;

