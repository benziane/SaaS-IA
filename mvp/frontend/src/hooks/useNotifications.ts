/**
 * useNotifications - React Query hooks for the notification system
 *
 * Provides:
 * - useNotifications() - paginated notification list
 * - useUnreadCount() - badge count with WebSocket real-time updates
 * - useMarkRead() - mark single notification read
 * - useMarkAllRead() - mark all notifications read
 */

'use client';

import { useCallback, useEffect } from 'react';
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';

import { QUERY_STALE_TIME } from '@/lib/queryClient';
import { notificationsApi } from '@/features/notifications/api';
import type {
  MarkAllReadResponse,
  MarkReadResponse,
  NotificationListResponse,
  WSMessage,
} from '@/features/notifications/types';

/* ========================================================================
   QUERY KEYS
   ======================================================================== */

export const notificationKeys = {
  all: ['notifications'] as const,
  lists: () => [...notificationKeys.all, 'list'] as const,
  list: (filters?: Record<string, unknown>) =>
    [...notificationKeys.lists(), filters] as const,
  unreadCount: () => [...notificationKeys.all, 'unread-count'] as const,
};

/* ========================================================================
   useNotifications
   ======================================================================== */

/**
 * List notifications with optional unread-only filter
 */
export function useNotifications(
  unreadOnly: boolean = false,
  limit: number = 50,
  offset: number = 0,
): UseQueryResult<NotificationListResponse, Error> {
  return useQuery({
    queryKey: notificationKeys.list({ unreadOnly, limit, offset }),
    queryFn: () => notificationsApi.listNotifications(unreadOnly, limit, offset),
    staleTime: QUERY_STALE_TIME.CRITICAL,
  });
}

/* ========================================================================
   useUnreadCount
   ======================================================================== */

/**
 * Get unread notification count for badge display.
 * Polls every 60 seconds as a fallback; primary updates come via WebSocket.
 */
export function useUnreadCount(): UseQueryResult<number, Error> {
  return useQuery({
    queryKey: notificationKeys.unreadCount(),
    queryFn: async () => {
      const result = await notificationsApi.getUnreadCount();
      return result.unread_count;
    },
    staleTime: QUERY_STALE_TIME.CRITICAL,
    refetchInterval: 60000,
  });
}

/* ========================================================================
   useMarkRead
   ======================================================================== */

/**
 * Mark a single notification as read
 */
export function useMarkRead(): UseMutationResult<MarkReadResponse, Error, string> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (notificationId: string) =>
      notificationsApi.markNotificationRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

/* ========================================================================
   useMarkAllRead
   ======================================================================== */

/**
 * Mark all notifications as read
 */
export function useMarkAllRead(): UseMutationResult<MarkAllReadResponse, Error, void> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => notificationsApi.markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

/* ========================================================================
   useNotificationWebSocket
   ======================================================================== */

/**
 * Hook that listens to WebSocket notification messages and
 * invalidates React Query caches for real-time badge updates.
 *
 * Usage:
 *   const { onMessage } = useWebSocket();
 *   useNotificationWebSocket(onMessage);
 */
export function useNotificationWebSocket(
  onMessage: (type: string, callback: (msg: WSMessage) => void) => () => void,
): void {
  const queryClient = useQueryClient();

  const handleNotification = useCallback(
    (_msg: WSMessage) => {
      // Invalidate both the list and unread count
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
    [queryClient],
  );

  useEffect(() => {
    const unsubscribe = onMessage('notification', handleNotification);
    return unsubscribe;
  }, [onMessage, handleNotification]);
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default {
  useNotifications,
  useUnreadCount,
  useMarkRead,
  useMarkAllRead,
  useNotificationWebSocket,
};
