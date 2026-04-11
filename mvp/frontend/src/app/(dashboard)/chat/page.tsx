/**
 * Chat Page - AI Conversation Interface
 * Two-panel layout: conversation list on the left, active chat on the right.
 * Supports creating conversations from transcription context via query parameter.
 * Uses SSE streaming for real-time AI responses.
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { MessageSquare, X, Sparkles } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';

import { Alert, AlertDescription } from '@/components/ui/alert';

import { useConversations, useConversation } from '@/features/conversation/hooks';
import {
  useCreateConversation,
  useDeleteConversation,
} from '@/features/conversation/hooks';
import { queryKeys } from '@/lib/queryClient';
import { useSSE } from '@/hooks/useSSE';

import { ChatPanel } from '@/components/chat/ChatPanel';
import { ChatInput } from '@/components/chat/ChatInput';
import { ConversationList } from '@/components/chat/ConversationList';

import type { Message } from '@/features/conversation/types';

/* ========================================================================
   CONSTANTS
   ======================================================================== */

const SIDEBAR_WIDTH = 300;
const CHAT_STREAM_URL = '/api/conversation';

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function ChatPage() {
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  // Conversation list
  const {
    data: conversationsData,
    isLoading: isLoadingList,
  } = useConversations();

  // Active conversation
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const {
    data: activeConversation,
    isLoading: isLoadingConversation,
  } = useConversation(activeConversationId ?? '');

  // Mutations
  const createConversation = useCreateConversation();
  const deleteConversation = useDeleteConversation();

  // SSE streaming
  const { startStream, stopStream, isStreaming } = useSSE();
  const [streamingText, setStreamingText] = useState('');
  const [streamProvider, setStreamProvider] = useState<string | undefined>(undefined);
  const [streamTokenCount, setStreamTokenCount] = useState<number | undefined>(undefined);
  const [streamError, setStreamError] = useState<string | null>(null);
  const accumulatedTextRef = useRef('');

  // Optimistic messages added while streaming (before refetch)
  const [pendingMessages, setPendingMessages] = useState<Message[]>([]);

  // Derived data
  const conversations = conversationsData?.items ?? [];
  const existingMessages = activeConversation?.messages ?? [];
  const displayMessages = [...existingMessages, ...pendingMessages];

  // Handle transcription_id query parameter: auto-create conversation
  const transcriptionIdParam = searchParams.get('transcription_id');
  const handledTranscriptionRef = useRef<string | null>(null);

  useEffect(() => {
    if (
      transcriptionIdParam &&
      transcriptionIdParam !== handledTranscriptionRef.current &&
      !createConversation.isPending
    ) {
      handledTranscriptionRef.current = transcriptionIdParam;
      createConversation.mutate(transcriptionIdParam, {
        onSuccess: (newConversation) => {
          setActiveConversationId(newConversation.id);
        },
      });
    }
  }, [transcriptionIdParam, createConversation]);

  // Auto-select first conversation if none active
  useEffect(() => {
    if (
      !activeConversationId &&
      conversations.length > 0 &&
      !transcriptionIdParam
    ) {
      const first = conversations[0];
      if (first) {
        setActiveConversationId(first.id);
      }
    }
  }, [activeConversationId, conversations, transcriptionIdParam]);

  // Create new conversation handler
  const handleCreateConversation = useCallback(() => {
    createConversation.mutate(undefined, {
      onSuccess: (newConversation) => {
        setActiveConversationId(newConversation.id);
      },
    });
  }, [createConversation]);

  // Delete conversation handler
  const handleDeleteConversation = useCallback(
    (id: string) => {
      deleteConversation.mutate(id, {
        onSuccess: () => {
          if (activeConversationId === id) {
            setActiveConversationId(null);
          }
        },
      });
    },
    [deleteConversation, activeConversationId]
  );

  // Send message handler - uses SSE streaming
  const handleSendMessage = useCallback(
    (content: string) => {
      if (!activeConversationId) return;

      setStreamingText('');
      setStreamProvider(undefined);
      setStreamTokenCount(undefined);
      setStreamError(null);
      accumulatedTextRef.current = '';

      const optimisticUserMessage: Message = {
        id: `pending-${Date.now()}`,
        role: 'user',
        content,
        provider: null,
        created_at: new Date().toISOString(),
      };
      setPendingMessages((prev) => [...prev, optimisticUserMessage]);

      startStream(
        `${CHAT_STREAM_URL}/${activeConversationId}/chat`,
        { message: content },
        {
          onToken: (token: string) => {
            accumulatedTextRef.current += token;
            setStreamingText(accumulatedTextRef.current);
          },
          onDone: (info) => {
            setStreamProvider(info.provider);
            setStreamTokenCount(info.tokens_streamed);
            setPendingMessages([]);
            void queryClient.invalidateQueries({
              queryKey: queryKeys.conversations.detail(activeConversationId),
            });
            void queryClient.invalidateQueries({
              queryKey: queryKeys.conversations.lists(),
            });
            setTimeout(() => {
              setStreamingText('');
              setStreamProvider(undefined);
              setStreamTokenCount(undefined);
            }, 500);
          },
          onError: (error: string) => {
            setStreamError(error);
            setPendingMessages([]);
            void queryClient.invalidateQueries({
              queryKey: queryKeys.conversations.detail(activeConversationId),
            });
          },
        }
      );
    },
    [activeConversationId, startStream, queryClient]
  );

  return (
    <div className="flex gap-4 p-5 animate-enter" style={{ height: 'calc(100vh - 120px)' }}>

      {/* Left Panel: Conversation List */}
      <div
        className="surface-card flex flex-col overflow-hidden shrink-0"
        style={{ width: SIDEBAR_WIDTH, minWidth: SIDEBAR_WIDTH }}
      >
        <ConversationList
          conversations={conversations}
          activeId={activeConversationId}
          onSelect={setActiveConversationId}
          onDelete={handleDeleteConversation}
          onCreate={handleCreateConversation}
          isLoading={isLoadingList}
        />
      </div>

      {/* Right Panel: Active Chat */}
      <div className="surface-card flex-1 flex flex-col overflow-hidden">
        {activeConversationId ? (
          <>
            {/* Chat Header */}
            <div className="px-5 py-3.5 border-b border-[var(--border)] flex items-center gap-3 shrink-0">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[#a855f7] shrink-0">
                <MessageSquare className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-[var(--text-high)] truncate">
                  {activeConversation?.title || 'New Conversation'}
                </p>
                {activeConversation?.transcription_id && (
                  <span className="text-xs text-[var(--accent)]">
                    Linked to transcription
                  </span>
                )}
              </div>
              {isStreaming && (
                <span className="flex items-center gap-1.5 text-xs text-[var(--accent)]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse" />
                  Streaming
                </span>
              )}
            </div>

            {/* Stream Error */}
            {streamError && (
              <Alert variant="destructive" className="mx-4 mt-3">
                <div className="flex items-center justify-between">
                  <AlertDescription>{streamError}</AlertDescription>
                  <button
                    type="button"
                    title="Dismiss error"
                    onClick={() => setStreamError(null)}
                    className="text-red-400 hover:text-red-300 shrink-0 ml-2"
                  >
                    <X className="w-4 h-4" />
                    <span className="sr-only">Dismiss error</span>
                  </button>
                </div>
              </Alert>
            )}

            {/* Message Area */}
            <ChatPanel
              messages={displayMessages}
              streamingText={streamingText}
              isStreaming={isStreaming}
              streamingProvider={streamProvider}
              streamingTokenCount={streamTokenCount}
              isLoading={isLoadingConversation}
            />

            {/* Input Area */}
            <ChatInput
              onSend={handleSendMessage}
              onStop={stopStream}
              isStreaming={isStreaming}
            />
          </>
        ) : (
          /* No conversation selected */
          <div className="flex-1 flex flex-col justify-center items-center gap-4 p-8">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)]/20 to-[#a855f7]/20 border border-[var(--accent)]/20">
              <Sparkles className="w-8 h-8 text-[var(--accent)]" />
            </div>
            <div className="text-center">
              <p className="text-base font-semibold text-[var(--text-high)] mb-1">
                Start a conversation
              </p>
              <p className="text-sm text-[var(--text-mid)]">
                Select a conversation from the list or create a new one.
              </p>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
