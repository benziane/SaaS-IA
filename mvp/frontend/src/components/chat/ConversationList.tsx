/**
 * ConversationList - Sidebar listing all user conversations
 * Displays title, date, and message count for each conversation.
 * Supports active highlighting, deletion with confirmation, and empty state.
 */

'use client';

import { useState } from 'react';
import { Plus, Trash2, MessageSquare } from 'lucide-react';
import { Button } from '@/lib/design-hub/components/Button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/lib/design-hub/components/Dialog';
import { Separator } from '@/lib/design-hub/components/Separator';
import { Skeleton } from '@/lib/design-hub/components/Skeleton';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';

import type { Conversation } from '@/features/conversation/types';

/* ========================================================================
   TYPES
   ======================================================================== */

export interface ConversationListProps {
  /** Array of conversations to display */
  conversations: Conversation[];
  /** Currently selected conversation ID */
  activeId: string | null;
  /** Called when a conversation is selected */
  onSelect: (id: string) => void;
  /** Called when the user confirms deletion of a conversation */
  onDelete: (id: string) => void;
  /** Called to create a new conversation */
  onCreate: () => void;
  /** Whether the list is loading */
  isLoading: boolean;
}

/* ========================================================================
   HELPERS
   ======================================================================== */

function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

/* ========================================================================
   COMPONENT
   ======================================================================== */

export function ConversationList({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onCreate,
  isLoading,
}: ConversationListProps): JSX.Element {
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const handleConfirmDelete = (): void => {
    if (deleteTarget) {
      onDelete(deleteTarget);
      setDeleteTarget(null);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[var(--bg-surface)]">
      {/* Header */}
      <div className="p-4 pb-2">
        <h2 className="text-lg font-semibold mb-2 text-[var(--text-high)]">Conversations</h2>
        <Button
          onClick={onCreate}
          size="sm"
          className="w-full gap-2"
        >
          <Plus className="h-4 w-4" />
          New Conversation
        </Button>
      </div>

      <Separator />

      {/* Conversation List */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="p-4 space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="p-6 flex flex-col items-center gap-2 text-[var(--text-low)]">
            <MessageSquare className="h-12 w-12 opacity-30" />
            <p className="text-sm text-[var(--text-low)] text-center">
              No conversations yet. Start a new one to chat with AI.
            </p>
          </div>
        ) : (
          <ul className="py-1">
            {conversations.map((conversation) => {
              const isActive = conversation.id === activeId;

              return (
                <li
                  key={conversation.id}
                  className="group relative"
                >
                  <button
                    onClick={() => onSelect(conversation.id)}
                    className={`w-full text-left py-3 px-4 transition-colors ${
                      isActive
                        ? 'bg-[var(--bg-elevated)] border-l-[3px] border-l-[var(--accent)]'
                        : 'border-l-[3px] border-l-transparent hover:bg-[var(--bg-elevated)]/50'
                    }`}
                  >
                    <p
                      className={`text-sm truncate max-w-[180px] ${
                        isActive ? 'font-semibold' : 'font-normal'
                      } text-[var(--text-high)]`}
                    >
                      {conversation.title || 'New Conversation'}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-[var(--text-low)]">
                        {formatRelativeDate(conversation.updated_at)}
                      </span>
                      {conversation.message_count > 0 && (
                        <Badge variant="outline" className="h-[18px] text-[0.65rem]">
                          {conversation.message_count}
                        </Badge>
                      )}
                    </div>
                  </button>

                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteTarget(conversation.id);
                          }}
                          aria-label="Delete conversation"
                          className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-md hover:bg-[var(--bg-elevated)] text-[var(--text-low)] hover:text-red-400"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent>Delete conversation</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <DialogContent className="max-w-xs">
          <DialogHeader>
            <DialogTitle>Delete Conversation</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this conversation? All messages will
              be permanently removed. This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDeleteTarget(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default ConversationList;
