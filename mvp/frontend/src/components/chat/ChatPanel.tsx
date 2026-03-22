/**
 * ChatPanel - Message display area for a conversation
 * Renders a scrollable list of messages with role-based styling.
 * User messages are right-aligned with primary color, assistant messages
 * are left-aligned with a grey background, and system messages appear
 * as subtle info banners. Auto-scrolls to the bottom on new messages.
 */

'use client';

import { useCallback, useEffect, useRef } from 'react';
import {
  Alert,
  Avatar,
  Box,
  Chip,
  CircularProgress,
  Typography,
} from '@mui/material';
import { Person, SmartToy } from '@mui/icons-material';

import { StreamingText } from '@/components/ui/StreamingText';
import type { Message } from '@/features/conversation/types';

/* ========================================================================
   TYPES
   ======================================================================== */

export interface ChatPanelProps {
  /** Existing messages for the conversation */
  messages: Message[];
  /** Text accumulated so far for the current streaming response */
  streamingText: string;
  /** Whether the AI is currently generating a response */
  isStreaming: boolean;
  /** Provider name for the current streaming response */
  streamingProvider?: string;
  /** Token count for the completed streaming response */
  streamingTokenCount?: number;
  /** Whether the conversation data is loading */
  isLoading: boolean;
}

/* ========================================================================
   SUB-COMPONENTS
   ======================================================================== */

interface MessageBubbleProps {
  message: Message;
}

function MessageBubble({ message }: MessageBubbleProps): JSX.Element {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  // System messages render as info banners
  if (isSystem) {
    return (
      <Box sx={{ px: 2, py: 0.5 }}>
        <Alert
          severity="info"
          variant="outlined"
          sx={{
            py: 0,
            '& .MuiAlert-message': {
              fontSize: '0.8rem',
            },
          }}
        >
          {message.content}
        </Alert>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        px: 2,
        py: 0.75,
        gap: 1,
        alignItems: 'flex-start',
      }}
    >
      {/* Assistant avatar */}
      {!isUser && (
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: 'grey.600',
            mt: 0.5,
          }}
        >
          <SmartToy sx={{ fontSize: 18 }} />
        </Avatar>
      )}

      {/* Message content */}
      <Box
        sx={{
          maxWidth: '70%',
          minWidth: 60,
        }}
      >
        {/* Provider label for assistant messages */}
        {!isUser && message.provider && (
          <Chip
            label={message.provider}
            size="small"
            variant="outlined"
            sx={{
              height: 18,
              fontSize: '0.65rem',
              mb: 0.5,
              borderColor: 'grey.400',
            }}
          />
        )}

        <Box
          sx={{
            px: 2,
            py: 1.25,
            borderRadius: isUser
              ? '16px 16px 4px 16px'
              : '16px 16px 16px 4px',
            bgcolor: isUser ? 'primary.main' : 'grey.100',
            color: isUser ? 'primary.contrastText' : 'text.primary',
            ...(isUser
              ? {}
              : {
                  // Adapt grey bg for dark mode
                  '.MuiCssBaseline-root[data-mui-color-scheme="dark"] &': {
                    bgcolor: 'grey.800',
                  },
                }),
          }}
        >
          <Typography
            variant="body2"
            sx={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              lineHeight: 1.6,
            }}
          >
            {message.content}
          </Typography>
        </Box>

        {/* Timestamp */}
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            display: 'block',
            mt: 0.25,
            textAlign: isUser ? 'right' : 'left',
            fontSize: '0.65rem',
          }}
        >
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </Typography>
      </Box>

      {/* User avatar */}
      {isUser && (
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: 'primary.main',
            mt: 0.5,
          }}
        >
          <Person sx={{ fontSize: 18 }} />
        </Avatar>
      )}
    </Box>
  );
}

/* ========================================================================
   COMPONENT
   ======================================================================== */

export function ChatPanel({
  messages,
  streamingText,
  isStreaming,
  streamingProvider,
  streamingTokenCount,
  isLoading,
}: ChatPanelProps): JSX.Element {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change or streaming text updates
  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages.length, streamingText, scrollToBottom]);

  if (isLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100%',
        }}
      >
        <CircularProgress size={32} />
      </Box>
    );
  }

  return (
    <Box
      ref={scrollContainerRef}
      sx={{
        flex: 1,
        overflow: 'auto',
        display: 'flex',
        flexDirection: 'column',
        py: 2,
      }}
    >
      {messages.length === 0 && !isStreaming && (
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 1,
            color: 'text.secondary',
          }}
        >
          <SmartToy sx={{ fontSize: 48, opacity: 0.3 }} />
          <Typography variant="body2" color="text.secondary">
            Send a message to start the conversation.
          </Typography>
        </Box>
      )}

      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {/* Streaming response indicator */}
      {isStreaming && (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'flex-start',
            px: 2,
            py: 0.75,
            gap: 1,
            alignItems: 'flex-start',
          }}
        >
          <Avatar
            sx={{
              width: 32,
              height: 32,
              bgcolor: 'grey.600',
              mt: 0.5,
            }}
          >
            <SmartToy sx={{ fontSize: 18 }} />
          </Avatar>

          <Box sx={{ maxWidth: '70%', minWidth: 200 }}>
            {streamingProvider && (
              <Chip
                label={streamingProvider}
                size="small"
                variant="outlined"
                sx={{
                  height: 18,
                  fontSize: '0.65rem',
                  mb: 0.5,
                  borderColor: 'grey.400',
                }}
              />
            )}
            <Box
              sx={{
                px: 2,
                py: 1.25,
                borderRadius: '16px 16px 16px 4px',
                bgcolor: 'grey.100',
                color: 'text.primary',
              }}
            >
              <StreamingText
                text={streamingText}
                isStreaming={isStreaming}
                provider={streamingProvider}
                tokenCount={streamingTokenCount}
              />
            </Box>
          </Box>
        </Box>
      )}

      {/* Scroll anchor */}
      <div ref={bottomRef} />
    </Box>
  );
}

export default ChatPanel;
