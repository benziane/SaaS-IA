/**
 * ChatInput - Message input component for conversation chat
 * Supports Enter to send, Shift+Enter for newline, and character count display.
 * Disables input while the AI is streaming a response.
 */

'use client';

import { useCallback, useState } from 'react';
import {
  Box,
  IconButton,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { Send, StopCircle } from '@mui/icons-material';

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
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: 1,
        p: 2,
        borderTop: '1px solid',
        borderColor: 'divider',
        bgcolor: 'background.paper',
      }}
    >
      <Box sx={{ flex: 1, position: 'relative' }}>
        <TextField
          fullWidth
          multiline
          maxRows={6}
          value={value}
          onChange={(e) => setValue(e.target.value.slice(0, MAX_CHARACTERS))}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isStreaming}
          size="small"
          variant="outlined"
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
            },
          }}
        />
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            position: 'absolute',
            right: 8,
            bottom: -18,
            fontSize: '0.7rem',
          }}
        >
          {characterCount}/{MAX_CHARACTERS}
        </Typography>
      </Box>

      {isStreaming ? (
        <Tooltip title="Stop generating">
          <IconButton
            color="warning"
            onClick={onStop}
            size="medium"
            sx={{ mb: '2px' }}
          >
            <StopCircle />
          </IconButton>
        </Tooltip>
      ) : (
        <Tooltip title={canSend ? 'Send message (Enter)' : 'Type a message to send'}>
          <span>
            <IconButton
              color="primary"
              onClick={handleSend}
              disabled={!canSend}
              size="medium"
              sx={{ mb: '2px' }}
            >
              <Send />
            </IconButton>
          </span>
        </Tooltip>
      )}
    </Box>
  );
}

export default ChatInput;
