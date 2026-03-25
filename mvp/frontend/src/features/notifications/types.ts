/**
 * Notification Types
 * Type definitions for the notification system
 */

/* ========================================================================
   NOTIFICATION
   ======================================================================== */

export type NotificationType =
  | 'info'
  | 'success'
  | 'warning'
  | 'error'
  | 'ai_complete'
  | 'mention'
  | 'system';

export interface Notification {
  id: string;
  title: string;
  body: string;
  type: NotificationType;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

/* ========================================================================
   RESPONSES
   ======================================================================== */

export interface NotificationListResponse {
  items: Notification[];
  count: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface MarkReadResponse {
  message: string;
}

export interface MarkAllReadResponse {
  message: string;
  count: number;
}

/* ========================================================================
   WEBSOCKET MESSAGES
   ======================================================================== */

export type WSMessageType =
  | 'chat'
  | 'notification'
  | 'presence'
  | 'typing'
  | 'system'
  | 'pong';

export interface WSMessage {
  type: WSMessageType;
  data: Record<string, unknown>;
  room_id: string;
  user_id: string;
  timestamp: string;
}

export type WSConnectionStatus =
  | 'connecting'
  | 'connected'
  | 'disconnected'
  | 'reconnecting';

export interface WSPresenceUser {
  user_id: string;
  name: string;
  status: 'online' | 'away' | 'busy' | 'offline';
  color: string;
  last_seen?: string;
}
