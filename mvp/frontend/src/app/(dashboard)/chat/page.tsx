/**
 * Chat Page - AI Conversation Interface
 * Two-panel layout: conversation list on the left, active chat on the right.
 * Supports creating conversations from transcription context via query parameter.
 * Uses SSE streaming for real-time AI responses.
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { MessageSquare, X } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';

import { Card } from '@/components/ui/card';
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

export default function ChatPage(): JSX.Element {
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

      // Reset streaming state
      setStreamingText('');
      setStreamProvider(undefined);
      setStreamTokenCount(undefined);
      setStreamError(null);
      accumulatedTextRef.current = '';

      // Optimistically add the user message
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

            // Clear pending messages and refetch the conversation to get
            // the persisted messages from the server
            setPendingMessages([]);
            void queryClient.invalidateQueries({
              queryKey: queryKeys.conversations.detail(activeConversationId),
            });
            void queryClient.invalidateQueries({
              queryKey: queryKeys.conversations.lists(),
            });

            // Reset streaming text after a brief delay for the refetch
            setTimeout(() => {
              setStreamingText('');
              setStreamProvider(undefined);
              setStreamTokenCount(undefined);
            }, 500);
          },
          onError: (error: string) => {
            setStreamError(error);
            // Still refetch to get any messages that were persisted
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
    <div className="flex gap-4" style={{ height: 'calc(100vh - 120px)' }}>
      {/* Left Panel: Conversation List */}
      <Card
        className="flex flex-col overflow-hidden shrink-0"
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
      </Card>

      {/* Right Panel: Active Chat */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        {activeConversationId ? (
          <>
            {/* Chat Header */}
            <div className="px-4 py-3 border-b border-[var(--border)] flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-[var(--accent)]" />
              <h6 className="text-base font-semibold text-[var(--text-high)]">
                {activeConversation?.title || 'New Conversation'}
              </h6>
              {activeConversation?.transcription_id && (
                <span className="ml-auto text-xs text-[var(--text-mid)] bg-[var(--bg-elevated)] px-2 py-0.5 rounded">
                  Linked to transcription
                </span>
              )}
            </div>

            {/* Stream Error */}
            {streamError && (
              <Alert variant="destructive" className="mx-4 mt-2">
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
          <div className="flex-1 flex flex-col justify-center items-center gap-4 text-[var(--text-mid)]">
            <MessageSquare className="w-16 h-16 opacity-15" />
            <h6 className="text-base font-semibold text-[var(--text-mid)]">
              Select a conversation or create a new one
            </h6>
            <p className="text-sm text-[var(--text-mid)]">
              Chat with AI about your transcriptions and more.
            </p>
          </div>
        )}
      </Card>

    </div>
  );
}
