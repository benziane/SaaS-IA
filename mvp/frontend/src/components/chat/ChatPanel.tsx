'use client';

import { useCallback, useEffect, useRef } from 'react';
import { Bot, User } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Avatar, AvatarFallback } from '@/lib/design-hub/components/Avatar';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';

import { StreamingText } from '@/components/ui/StreamingText';
import type { Message } from '@/features/conversation/types';

/* ========================================================================
   TYPES
   ======================================================================== */

export interface ChatPanelProps {
  messages: Message[];
  streamingText: string;
  isStreaming: boolean;
  streamingProvider?: string;
  streamingTokenCount?: number;
  isLoading: boolean;
  onSend?: (content: string) => void;
}

/* ========================================================================
   SUB-COMPONENTS
   ======================================================================== */

function StreamingDots() {
  return (
    <span className="inline-flex items-center gap-[3px] h-4">
      <span
        className="w-1.5 h-1.5 rounded-full bg-[var(--text-low)] animate-pulse"
        style={{ animationDelay: '0ms', animationDuration: '1s' }}
      />
      <span
        className="w-1.5 h-1.5 rounded-full bg-[var(--text-low)] animate-pulse"
        style={{ animationDelay: '200ms', animationDuration: '1s' }}
      />
      <span
        className="w-1.5 h-1.5 rounded-full bg-[var(--text-low)] animate-pulse"
        style={{ animationDelay: '400ms', animationDuration: '1s' }}
      />
    </span>
  );
}

function BotAvatar() {
  return (
    <Avatar className="h-8 w-8 mt-1 shrink-0">
      <AvatarFallback className="bg-[var(--bg-elevated)] border border-[var(--accent)]/30">
        <Bot className="h-4 w-4 text-[var(--accent)]" />
      </AvatarFallback>
    </Avatar>
  );
}

function UserAvatar() {
  return (
    <Avatar className="h-8 w-8 mt-1 shrink-0">
      <AvatarFallback className="bg-[var(--bg-elevated)] border border-[var(--border)]">
        <User className="h-4 w-4 text-[var(--accent)]" />
      </AvatarFallback>
    </Avatar>
  );
}

interface MessageBubbleProps {
  message: Message;
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

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
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-4 py-1.5 gap-2.5 items-start`}
    >
      {!isUser && <BotAvatar />}

      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} min-w-[60px]`}>
        {!isUser && message.provider && (
          <span className="text-[10px] text-[var(--text-low)] mb-1 px-1">
            {message.provider}
          </span>
        )}

        <div
          className={
            isUser
              ? 'bg-gradient-to-br from-[var(--accent)] to-[var(--accent)]/70 text-white rounded-2xl rounded-br-sm px-4 py-2.5 max-w-[75%]'
              : 'bg-[var(--bg-elevated)] border border-[var(--border)] text-[var(--text-high)] rounded-2xl rounded-bl-sm px-4 py-2.5 max-w-[80%]'
          }
        >
          <p className="text-sm whitespace-pre-wrap break-words leading-relaxed">
            {message.content}
          </p>
        </div>

        <span className="block mt-0.5 text-[10px] text-[var(--text-low)]">
          {new Date(message.created_at).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </span>
      </div>

      {isUser && <UserAvatar />}
    </div>
  );
}

/* ========================================================================
   LOADING SKELETON
   ======================================================================== */

function ChatSkeleton() {
  return (
    <div className="flex flex-col gap-4 px-4 py-6">
      <div className="flex items-start gap-2.5">
        <Skeleton className="h-8 w-8 rounded-full shrink-0" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-4 w-[55%]" />
          <Skeleton className="h-4 w-[40%]" />
        </div>
      </div>
      <div className="flex items-start gap-2.5 justify-end">
        <div className="space-y-2 flex-1 flex flex-col items-end">
          <Skeleton className="h-4 w-[45%]" />
          <Skeleton className="h-4 w-[30%]" />
        </div>
        <Skeleton className="h-8 w-8 rounded-full shrink-0" />
      </div>
      <div className="flex items-start gap-2.5">
        <Skeleton className="h-8 w-8 rounded-full shrink-0" />
        <div className="space-y-2 flex-1">
          <Skeleton className="h-4 w-[65%]" />
          <Skeleton className="h-4 w-[50%]" />
          <Skeleton className="h-4 w-[35%]" />
        </div>
      </div>
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
  onSend,
}: ChatPanelProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages.length, streamingText, scrollToBottom]);

  if (isLoading) {
    return (
      <div className="flex-1 overflow-hidden">
        <ChatSkeleton />
      </div>
    );
  }

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 overflow-auto flex flex-col py-4"
    >
      {messages.length === 0 && !isStreaming && (
        <div className="flex-1 flex flex-col justify-center items-center gap-3 text-[var(--text-low)]">
          <div className="h-14 w-14 rounded-2xl bg-[var(--bg-elevated)] border border-[var(--accent)]/30 flex items-center justify-center">
            <Bot className="h-7 w-7 text-[var(--accent)]" />
          </div>
          <p className="text-sm text-[var(--text-mid)]">
            Send a message to start the conversation.
          </p>
          {onSend && (
            <div className="flex flex-wrap gap-2 justify-center mt-4">
              {['Summarize a document', 'Explain this code', 'Answer questions from a transcript'].map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => onSend(prompt)}
                  className="px-3 py-1.5 text-xs rounded-full border border-[var(--border)] text-[var(--text-mid)] hover:bg-[var(--bg-elevated)] hover:text-[var(--text-high)] transition-colors cursor-pointer"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {/* Streaming response */}
      {isStreaming && (
        <div className="flex justify-start px-4 py-1.5 gap-2.5 items-start">
          <BotAvatar />

          <div className="flex flex-col items-start min-w-[60px]">
            {streamingProvider && (
              <span className="text-[10px] text-[var(--text-low)] mb-1 px-1">
                {streamingProvider}
              </span>
            )}
            <div className="bg-[var(--bg-elevated)] border border-[var(--border)] text-[var(--text-high)] rounded-2xl rounded-bl-sm px-4 py-2.5 max-w-[80%]">
              {streamingText ? (
                <StreamingText
                  text={streamingText}
                  isStreaming={isStreaming}
                  provider={streamingProvider}
                  tokenCount={streamingTokenCount}
                />
              ) : (
                <StreamingDots />
              )}
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}

export default ChatPanel;
