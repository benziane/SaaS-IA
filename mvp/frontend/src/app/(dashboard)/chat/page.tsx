/**
 * Chat Page - AI Conversation Interface
 * Two-panel layout: conversation list on the left, active chat on the right.
 * Supports creating conversations from transcription context via query parameter.
 * Uses SSE streaming for real-time AI responses.
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Alert,
  Box,
  Card,
  Typography,
} from '@mui/material';
import { Forum } from '@mui/icons-material';
import { useQueryClient } from '@tanstack/react-query';

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
    <Box sx={{ height: 'calc(100vh - 120px)', display: 'flex', gap: 2 }}>
      {/* Left Panel: Conversation List */}
      <Card
        sx={{
          width: SIDEBAR_WIDTH,
          minWidth: SIDEBAR_WIDTH,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
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
      <Card
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {activeConversationId ? (
          <>
            {/* Chat Header */}
            <Box
              sx={{
                px: 2,
                py: 1.5,
                borderBottom: '1px solid',
                borderColor: 'divider',
                display: 'flex',
                alignItems: 'center',
                gap: 1,
              }}
            >
              <Forum fontSize="small" color="primary" />
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                {activeConversation?.title || 'New Conversation'}
              </Typography>
              {activeConversation?.transcription_id && (
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{
                    ml: 'auto',
                    bgcolor: 'action.hover',
                    px: 1,
                    py: 0.25,
                    borderRadius: 1,
                  }}
                >
                  Linked to transcription
                </Typography>
              )}
            </Box>

            {/* Stream Error */}
            {streamError && (
              <Alert severity="error" sx={{ mx: 2, mt: 1 }} onClose={() => setStreamError(null)}>
                {streamError}
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
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              gap: 2,
              color: 'text.secondary',
            }}
          >
            <Forum sx={{ fontSize: 64, opacity: 0.15 }} />
            <Typography variant="h6" color="text.secondary">
              Select a conversation or create a new one
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Chat with AI about your transcriptions and more.
            </Typography>
          </Box>
        )}
      </Card>

    </Box>
  );
}
