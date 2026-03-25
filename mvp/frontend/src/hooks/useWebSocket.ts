/**
 * useWebSocket - Production-grade WebSocket hook with auto-reconnect
 *
 * Features:
 * - JWT auth via URL path token
 * - Exponential backoff reconnection
 * - Message queue for offline messages
 * - Typed message handlers
 * - Connection status tracking
 * - Ping/pong keepalive
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import type { WSConnectionStatus, WSMessage, WSMessageType } from '@/features/notifications/types';

/* ========================================================================
   CONSTANTS
   ======================================================================== */

const WS_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004')
  .replace('http://', 'ws://')
  .replace('https://', 'wss://');

const RECONNECT_BASE_DELAY = 1000; // 1 second
const RECONNECT_MAX_DELAY = 30000; // 30 seconds
const RECONNECT_MAX_ATTEMPTS = 20;
const PING_INTERVAL = 25000; // 25 seconds

/* ========================================================================
   TYPES
   ======================================================================== */

type MessageHandler = (message: WSMessage) => void;

export interface UseWebSocketOptions {
  /** Auto-connect on mount (default: true) */
  autoConnect?: boolean;
  /** Called when connection status changes */
  onStatusChange?: (status: WSConnectionStatus) => void;
}

export interface UseWebSocketReturn {
  /** Current connection status */
  status: WSConnectionStatus;
  /** Send a typed message */
  sendMessage: (type: string, data: Record<string, unknown>, roomId?: string) => void;
  /** Register a handler for a specific message type */
  onMessage: (type: WSMessageType | string, callback: MessageHandler) => () => void;
  /** Manually connect */
  connect: () => void;
  /** Manually disconnect (stops auto-reconnect) */
  disconnect: () => void;
  /** Last received message (any type) */
  lastMessage: WSMessage | null;
}

/* ========================================================================
   HOOK
   ======================================================================== */

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { autoConnect = true, onStatusChange } = options;

  const [status, setStatus] = useState<WSConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef<Map<string, Set<MessageHandler>>>(new Map());
  const messageQueueRef = useRef<string[]>([]);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const intentionalCloseRef = useRef(false);
  const statusRef = useRef<WSConnectionStatus>('disconnected');

  // Update status and notify
  const updateStatus = useCallback(
    (newStatus: WSConnectionStatus) => {
      statusRef.current = newStatus;
      setStatus(newStatus);
      onStatusChange?.(newStatus);
    },
    [onStatusChange],
  );

  // Get auth token
  const getToken = useCallback((): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
  }, []);

  // Flush queued messages
  const flushQueue = useCallback(() => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    while (messageQueueRef.current.length > 0) {
      const msg = messageQueueRef.current.shift();
      if (msg) {
        ws.send(msg);
      }
    }
  }, []);

  // Start ping keepalive
  const startPing = useCallback(() => {
    if (pingTimerRef.current) {
      clearInterval(pingTimerRef.current);
    }
    pingTimerRef.current = setInterval(() => {
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping', data: {} }));
      }
    }, PING_INTERVAL);
  }, []);

  // Stop ping
  const stopPing = useCallback(() => {
    if (pingTimerRef.current) {
      clearInterval(pingTimerRef.current);
      pingTimerRef.current = null;
    }
  }, []);

  // Dispatch message to registered handlers
  const dispatchMessage = useCallback((message: WSMessage) => {
    setLastMessage(message);

    // Notify type-specific handlers
    const typeHandlers = handlersRef.current.get(message.type);
    if (typeHandlers) {
      typeHandlers.forEach((handler) => {
        try {
          handler(message);
        } catch (e) {
          console.error('[WS] Handler error:', e);
        }
      });
    }

    // Notify wildcard handlers
    const wildcardHandlers = handlersRef.current.get('*');
    if (wildcardHandlers) {
      wildcardHandlers.forEach((handler) => {
        try {
          handler(message);
        } catch (e) {
          console.error('[WS] Wildcard handler error:', e);
        }
      });
    }
  }, []);

  // Schedule reconnection with exponential backoff
  const scheduleReconnect = useCallback(() => {
    if (intentionalCloseRef.current) return;
    if (reconnectAttemptRef.current >= RECONNECT_MAX_ATTEMPTS) {
      console.warn('[WS] Max reconnect attempts reached');
      updateStatus('disconnected');
      return;
    }

    const delay = Math.min(
      RECONNECT_BASE_DELAY * Math.pow(2, reconnectAttemptRef.current),
      RECONNECT_MAX_DELAY,
    );

    updateStatus('reconnecting');
    reconnectAttemptRef.current += 1;

    reconnectTimerRef.current = setTimeout(() => {
      connectWs();
    }, delay);
  }, []); // connectWs is hoisted

  // Connect to WebSocket
  const connectWs = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.onclose = null; // Prevent reconnect on intentional close
      wsRef.current.close();
      wsRef.current = null;
    }

    const token = getToken();
    if (!token) {
      updateStatus('disconnected');
      return;
    }

    intentionalCloseRef.current = false;
    updateStatus('connecting');

    const url = `${WS_BASE_URL}/ws/${token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectAttemptRef.current = 0;
      updateStatus('connected');
      flushQueue();
      startPing();
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        dispatchMessage(message);
      } catch {
        // Non-JSON message; ignore
      }
    };

    ws.onclose = (event: CloseEvent) => {
      stopPing();
      wsRef.current = null;

      if (event.code === 4001) {
        // Auth failure - do not reconnect
        updateStatus('disconnected');
        return;
      }

      if (!intentionalCloseRef.current) {
        scheduleReconnect();
      } else {
        updateStatus('disconnected');
      }
    };

    ws.onerror = () => {
      // onclose will fire after onerror; reconnect happens there
    };
  }, [getToken, updateStatus, flushQueue, startPing, stopPing, dispatchMessage, scheduleReconnect]);

  // Disconnect
  const disconnect = useCallback(() => {
    intentionalCloseRef.current = true;

    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    stopPing();

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    reconnectAttemptRef.current = 0;
    updateStatus('disconnected');
  }, [stopPing, updateStatus]);

  // Send message
  const sendMessage = useCallback(
    (type: string, data: Record<string, unknown>, roomId: string = 'global') => {
      const msg = JSON.stringify({ type, data, room_id: roomId });

      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(msg);
      } else {
        // Queue for later delivery
        messageQueueRef.current.push(msg);
      }
    },
    [],
  );

  // Register message handler (returns unsubscribe function)
  const onMessage = useCallback(
    (type: WSMessageType | string, callback: MessageHandler): (() => void) => {
      if (!handlersRef.current.has(type)) {
        handlersRef.current.set(type, new Set());
      }
      handlersRef.current.get(type)!.add(callback);

      return () => {
        const handlers = handlersRef.current.get(type);
        if (handlers) {
          handlers.delete(callback);
          if (handlers.size === 0) {
            handlersRef.current.delete(type);
          }
        }
      };
    },
    [],
  );

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      const token = getToken();
      if (token) {
        connectWs();
      }
    }

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect]);

  return {
    status,
    sendMessage,
    onMessage,
    connect: connectWs,
    disconnect,
    lastMessage,
  };
}

export default useWebSocket;
