/**
 * useSSE - Reusable Server-Sent Events streaming hook
 * Uses the Fetch API with ReadableStream for SSE-style POST requests.
 * Parses "data: {...}\n\n" formatted chunks from the server.
 */

'use client';

import { useCallback, useRef, useState } from 'react';

/* ========================================================================
   TYPES
   ======================================================================== */

export interface SSETokenEvent {
  type: 'token';
  content: string;
}

export interface SSEDoneEvent {
  type: 'done';
  provider: string;
  tokens_streamed: number;
}

export interface SSEErrorEvent {
  type: 'error';
  message: string;
}

type SSEEvent = SSETokenEvent | SSEDoneEvent | SSEErrorEvent;

export interface UseSSEOptions {
  onToken: (token: string) => void;
  onDone: (info: { provider: string; tokens_streamed: number }) => void;
  onError: (error: string) => void;
}

export interface UseSSEReturn {
  startStream: (url: string, body: Record<string, unknown>, options: UseSSEOptions) => void;
  stopStream: () => void;
  isStreaming: boolean;
}

/* ========================================================================
   CONSTANTS
   ======================================================================== */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004';

/* ========================================================================
   HOOK
   ======================================================================== */

export function useSSE(): UseSSEReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const startStream = useCallback(
    (url: string, body: Record<string, unknown>, options: UseSSEOptions) => {
      // Abort any existing stream before starting a new one
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const controller = new AbortController();
      abortControllerRef.current = controller;
      setIsStreaming(true);

      // Retrieve auth token from localStorage (consistent with apiClient pattern)
      let authToken: string | null = null;
      if (typeof window !== 'undefined') {
        authToken = localStorage.getItem('auth_token');
      }

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      };

      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;

      fetch(fullUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
        signal: controller.signal,
      })
        .then(async (response) => {
          if (!response.ok) {
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            try {
              const errorBody = await response.json();
              if (errorBody.detail) {
                errorMessage =
                  typeof errorBody.detail === 'string'
                    ? errorBody.detail
                    : JSON.stringify(errorBody.detail);
              }
            } catch {
              // Response body was not JSON; use the default message
            }
            options.onError(errorMessage);
            setIsStreaming(false);
            return;
          }

          const reader = response.body?.getReader();
          if (!reader) {
            options.onError('Response body is not readable');
            setIsStreaming(false);
            return;
          }

          const decoder = new TextDecoder();
          let buffer = '';

          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });

              // Process complete SSE messages (delimited by double newline)
              const messages = buffer.split('\n\n');
              // Keep the last incomplete chunk in the buffer
              buffer = messages.pop() ?? '';

              for (const message of messages) {
                const trimmed = message.trim();
                if (!trimmed) continue;

                // Extract lines that start with "data: "
                for (const line of trimmed.split('\n')) {
                  if (!line.startsWith('data: ')) continue;

                  const jsonStr = line.slice(6); // Remove "data: " prefix
                  if (jsonStr === '[DONE]') {
                    // OpenAI-style stream termination
                    continue;
                  }

                  try {
                    const event: SSEEvent = JSON.parse(jsonStr);
                    switch (event.type) {
                      case 'token':
                        options.onToken(event.content);
                        break;
                      case 'done':
                        options.onDone({
                          provider: event.provider,
                          tokens_streamed: event.tokens_streamed,
                        });
                        break;
                      case 'error':
                        options.onError(event.message);
                        break;
                    }
                  } catch {
                    // Non-JSON data line; skip silently
                  }
                }
              }
            }
          } catch (readError: unknown) {
            if (readError instanceof DOMException && readError.name === 'AbortError') {
              // Stream was intentionally aborted; not an error
            } else {
              const message =
                readError instanceof Error ? readError.message : 'Stream read failed';
              options.onError(message);
            }
          } finally {
            reader.releaseLock();
            setIsStreaming(false);
            abortControllerRef.current = null;
          }
        })
        .catch((fetchError: unknown) => {
          if (fetchError instanceof DOMException && fetchError.name === 'AbortError') {
            // Intentional abort; do not report as error
          } else {
            const message =
              fetchError instanceof Error ? fetchError.message : 'Failed to connect to stream';
            options.onError(message);
          }
          setIsStreaming(false);
          abortControllerRef.current = null;
        });
    },
    []
  );

  return { startStream, stopStream, isStreaming };
}

export default useSSE;
