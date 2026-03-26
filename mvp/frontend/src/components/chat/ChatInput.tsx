/**
 * ChatInput - Message input component for conversation chat
 * Supports Enter to send, Shift+Enter for newline, and character count display.
 * Disables input while the AI is streaming a response.
 */

'use client';

import { useCallback, useState } from 'react';
import { Send, CircleStop } from 'lucide-react';
import { Textarea } from '@/lib/design-hub/components/Textarea';
import { Button } from '@/lib/design-hub/components/Button';
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '@/lib/design-hub/components/Tooltip';

/* ========================================================================
   CONSTANTS
   ======================================================================== */

const MAX_CHARACTERS = 4000;

/* ========================================================================
   TYPES
   ======================================================================== */

export interface ChatInputProps {
  /** Called when the user submits a message */
  onSend: (message: string) => void;
  /** Called to abort the current stream */
  onStop?: () => void;
  /** Whether an AI response is currently streaming */
  isStreaming: boolean;
  /** Whether the input should be fully disabled (e.g. no conversation selected) */
  disabled?: boolean;
  /** Placeholder text */
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
    <div className="flex items-end gap-2 p-4 border-t border-[var(--border)] bg-[var(--bg-surface)]">
      <div className="flex-1 relative">
        <Textarea
          value={value}
          onChange={(e) => setValue(e.target.value.slice(0, MAX_CHARACTERS))}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isStreaming}
          className="min-h-[40px] max-h-[160px] rounded-lg resize-none"
          rows={1}
        />
        <span className="absolute right-2 -bottom-5 text-[0.7rem] text-[var(--text-low)]">
          {characterCount}/{MAX_CHARACTERS}
        </span>
      </div>

      <TooltipProvider>
        {isStreaming ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                onClick={onStop}
                className="mb-0.5 text-amber-500 hover:text-amber-600"
              >
                <CircleStop className="h-5 w-5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Stop generating</TooltipContent>
          </Tooltip>
        ) : (
          <Tooltip>
            <TooltipTrigger asChild>
              <span>
                <Button
                  variant="default"
                  size="icon"
                  onClick={handleSend}
                  disabled={!canSend}
                  className="mb-0.5"
                >
                  <Send className="h-5 w-5" />
                </Button>
              </span>
            </TooltipTrigger>
            <TooltipContent>
              {canSend ? 'Send message (Enter)' : 'Type a message to send'}
            </TooltipContent>
          </Tooltip>
        )}
      </TooltipProvider>
    </div>
  );
}

export default ChatInput;
