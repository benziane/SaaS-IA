/**
 * ChatPanel - Message display area for a conversation
 * Renders a scrollable list of messages with role-based styling.
 * User messages are right-aligned with primary color, assistant messages
 * are left-aligned with a grey background, and system messages appear
 * as subtle info banners. Auto-scrolls to the bottom on new messages.
 */

'use client';

import { useCallback, useEffect, useRef } from 'react';
import { Bot, User } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/lib/design-hub/components/Avatar';
import { Spinner } from '@/components/ui/spinner';

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
      <div className="px-4 py-1">
        <Alert variant="info">
          <AlertDescription className="text-xs">
            {message.content}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-4 py-1.5 gap-2 items-start`}
    >
      {/* Assistant avatar */}
      {!isUser && (
        <Avatar className="h-8 w-8 mt-1">
          <AvatarFallback className="bg-gray-600 text-white">
            <Bot className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}

      {/* Message content */}
      <div className="max-w-[70%] min-w-[60px]">
        {/* Provider label for assistant messages */}
        {!isUser && message.provider && (
          <Badge variant="outline" className="h-[18px] text-[0.65rem] mb-1 border-gray-400">
            {message.provider}
          </Badge>
        )}

        <div
          className={`px-4 py-2.5 ${
            isUser
              ? 'rounded-[16px_16px_4px_16px] bg-[var(--accent)] text-[var(--bg-app,#fff)]'
              : 'rounded-[16px_16px_16px_4px] bg-[var(--bg-elevated)] text-[var(--text-high)]'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">
            {message.content}
          </p>
        </div>

        {/* Timestamp */}
        <span
          className={`block mt-0.5 text-[0.65rem] text-[var(--text-low)] ${isUser ? 'text-right' : 'text-left'}`}
        >
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>

      {/* User avatar */}
      {isUser && (
        <Avatar className="h-8 w-8 mt-1">
          <AvatarFallback className="bg-[var(--accent)] text-white">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
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
      <div className="flex justify-center items-center h-full">
        <Spinner size={32} />
      </div>
    );
  }

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 overflow-auto flex flex-col py-4"
    >
      {messages.length === 0 && !isStreaming && (
        <div className="flex-1 flex flex-col justify-center items-center gap-2 text-[var(--text-low)]">
          <Bot className="h-12 w-12 opacity-30" />
          <p className="text-sm text-[var(--text-low)]">
            Send a message to start the conversation.
          </p>
        </div>
      )}

      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {/* Streaming response indicator */}
      {isStreaming && (
        <div className="flex justify-start px-4 py-1.5 gap-2 items-start">
          <Avatar className="h-8 w-8 mt-1">
            <AvatarFallback className="bg-gray-600 text-white">
              <Bot className="h-4 w-4" />
            </AvatarFallback>
          </Avatar>

          <div className="max-w-[70%] min-w-[200px]">
            {streamingProvider && (
              <Badge variant="outline" className="h-[18px] text-[0.65rem] mb-1 border-gray-400">
                {streamingProvider}
              </Badge>
            )}
            <div className="px-4 py-2.5 rounded-[16px_16px_16px_4px] bg-[var(--bg-elevated)] text-[var(--text-high)]">
              <StreamingText
                text={streamingText}
                isStreaming={isStreaming}
                provider={streamingProvider}
                tokenCount={streamingTokenCount}
              />
            </div>
          </div>
        </div>
      )}

      {/* Scroll anchor */}
      <div ref={bottomRef} />
    </div>
  );
}

export default ChatPanel;
