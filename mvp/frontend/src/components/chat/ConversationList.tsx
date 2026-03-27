'use client';

import { useState } from 'react';
import { Plus, Trash2, MessageSquare } from 'lucide-react';
import { Button } from '@/lib/design-hub/components/Button';
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
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onCreate: () => void;
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
      <div className="p-4 pb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-[var(--accent)]/20 to-[#a855f7]/20 border border-[var(--accent)]/30 flex items-center justify-center shrink-0">
            <MessageSquare className="h-3.5 w-3.5 text-[var(--accent)]" />
          </div>
          <h2 className="text-sm font-semibold text-[var(--text-high)]">Conversations</h2>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={onCreate}
                className="h-7 w-7 rounded-lg flex items-center justify-center bg-[var(--accent)]/10 text-[var(--accent)] hover:bg-[var(--accent)]/20 transition-colors shrink-0"
                aria-label="New conversation"
              >
                <Plus className="h-4 w-4" />
              </button>
            </TooltipTrigger>
            <TooltipContent>New conversation</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      <Separator />

      {/* Conversation List */}
      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="p-3 space-y-1.5">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full rounded-lg" />
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="p-8 flex flex-col items-center gap-3 text-[var(--text-low)]">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-[var(--accent)]/10 to-[#a855f7]/10 border border-[var(--accent)]/20 flex items-center justify-center">
              <MessageSquare className="h-6 w-6 text-[var(--accent)]/50" />
            </div>
            <p className="text-xs text-[var(--text-low)] text-center leading-relaxed">
              Start a conversation
            </p>
          </div>
        ) : (
          <ul className="py-1.5 px-1.5 space-y-0.5">
            {conversations.map((conversation) => {
              const isActive = conversation.id === activeId;

              return (
                <li
                  key={conversation.id}
                  className="group relative"
                >
                  <button
                    onClick={() => onSelect(conversation.id)}
                    className={`w-full text-left py-2.5 px-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-[var(--accent)]/8 border-l-2 border-l-[var(--accent)] pl-[10px]'
                        : 'border-l-2 border-l-transparent hover:bg-[var(--bg-elevated)]'
                    }`}
                  >
                    <p
                      className={`text-sm truncate max-w-[170px] font-medium text-[var(--text-high)] ${
                        isActive ? 'text-[var(--accent)]' : ''
                      }`}
                    >
                      {conversation.title || 'New Conversation'}
                    </p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className="text-[10px] text-[var(--text-low)]">
                        {formatRelativeDate(conversation.updated_at)}
                      </span>
                      {conversation.message_count > 0 && (
                        <span className="text-[10px] text-[var(--text-low)]">
                          · {conversation.message_count}
                        </span>
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
                          className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded-md hover:bg-[var(--error)]/10 text-[var(--text-low)] hover:text-[var(--error)]"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
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
