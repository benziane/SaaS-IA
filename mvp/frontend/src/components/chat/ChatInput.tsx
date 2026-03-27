'use client';

import { useCallback, useState } from 'react';
import { Send, Square } from 'lucide-react';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';

/* ========================================================================
   CONSTANTS
   ======================================================================== */

const MAX_CHARACTERS = 4000;

/* ========================================================================
   TYPES
   ======================================================================== */

export interface ChatInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  isStreaming: boolean;
  disabled?: boolean;
  placeholder?: string;
}

/* ========================================================================
   COMPONENT
   ======================================================================== */

export function ChatInput({
  onSend,
  onStop,
  isStreaming,
  disabled = false,
  placeholder = 'Type your message...',
}: ChatInputProps): JSX.Element {
  const [value, setValue] = useState('');

  const trimmedValue = value.trim();
  const canSend = trimmedValue.length > 0 && !isStreaming && !disabled;
  const characterCount = value.length;

  const handleSend = useCallback(() => {
    if (!canSend) return;
    onSend(trimmedValue);
    setValue('');
  }, [canSend, onSend, trimmedValue]);

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div className="border-t border-[var(--border)] bg-[var(--bg-surface)] px-4 py-3">
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <Textarea
            value={value}
            onChange={(e) => setValue(e.target.value.slice(0, MAX_CHARACTERS))}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled || isStreaming}
            className="bg-[var(--bg-elevated)] border border-[var(--border)] rounded-xl px-4 py-3 text-sm resize-none focus:border-[var(--accent)]/50 focus:ring-1 focus:ring-[var(--accent)]/20 min-h-[44px] max-h-[160px]"
            rows={1}
          />
          <span className="absolute right-3 -bottom-5 text-[10px] text-[var(--text-low)]">
            {characterCount}/{MAX_CHARACTERS}
          </span>
        </div>

        <TooltipProvider>
          {isStreaming ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={onStop}
                  className="mb-0.5 h-9 w-9 rounded-xl flex items-center justify-center bg-[var(--error)]/10 text-[var(--error)] border border-[var(--error)]/30 hover:bg-[var(--error)]/20 transition-colors shrink-0"
                >
                  <Square className="h-4 w-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent>Stop generating</TooltipContent>
            </Tooltip>
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <span>
                  <button
                    type="button"
                    onClick={handleSend}
                    disabled={!canSend}
                    className="mb-0.5 h-9 w-9 rounded-xl flex items-center justify-center bg-gradient-to-br from-[var(--accent)] to-[var(--accent)]/80 text-white hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </span>
              </TooltipTrigger>
              <TooltipContent>
                {canSend ? 'Send message (Enter)' : 'Type a message to send'}
              </TooltipContent>
            </Tooltip>
          )}
        </TooltipProvider>
      </div>
    </div>
  );
}

export default ChatInput;
