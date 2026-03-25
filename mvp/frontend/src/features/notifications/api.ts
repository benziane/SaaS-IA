/**
 * Notifications API
 * REST API calls for the notification system
 */

import type { AxiosResponse } from 'axios';

import apiClient from '@/lib/apiClient';

import type {
  NotificationListResponse,
  UnreadCountResponse,
  MarkReadResponse,
  MarkAllReadResponse,
} from './types';

/* ========================================================================
   API ENDPOINTS
   ======================================================================== */

const NOTIFICATION_ENDPOINTS = {
  LIST: '/api/notifications',
  MARK_READ: (id: string) => `/api/notifications/${id}/read`,
  MARK_ALL_READ: '/api/notifications/read-all',
  UNREAD_COUNT: '/api/notifications/unread-count',
} as const;

/* ========================================================================
   API FUNCTIONS
   ======================================================================== */

/**
 * List notifications with optional filtering
 */
export async function listNotifications(
  unreadOnly: boolean = false,
  limit: number = 50,
  offset: number = 0,
): Promise<NotificationListResponse> {
  const params = new URLSearchParams();
  if (unreadOnly) params.append('unread_only', 'true');
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  const queryString = params.toString();
  const url = queryString
    ? `${NOTIFICATION_ENDPOINTS.LIST}?${queryString}`
    : NOTIFICATION_ENDPOINTS.LIST;

  const response: AxiosResponse<NotificationListResponse> = await apiClient.get(url);
  return response.data;
}

/**
 * Mark a single notification as read
 */
export async function markNotificationRead(id: string): Promise<MarkReadResponse> {
  const response: AxiosResponse<MarkReadResponse> = await apiClient.put(
    NOTIFICATION_ENDPOINTS.MARK_READ(id),
  );
  return response.data;
}

/**
 * Mark all notifications as read
 */
export async function markAllNotificationsRead(): Promise<MarkAllReadResponse> {
  const response: AxiosResponse<MarkAllReadResponse> = await apiClient.put(
    NOTIFICATION_ENDPOINTS.MARK_ALL_READ,
  );
  return response.data;
}

/**
 * Get unread notification count
 */
export async function getUnreadCount(): Promise<UnreadCountResponse> {
  const response: AxiosResponse<UnreadCountResponse> = await apiClient.get(
    NOTIFICATION_ENDPOINTS.UNREAD_COUNT,
  );
  return response.data;
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export const notificationsApi = {
  listNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  getUnreadCount,
} as const;

export default notificationsApi;
