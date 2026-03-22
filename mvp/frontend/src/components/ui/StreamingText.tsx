/**
 * StreamingText - Displays text that streams in token by token
 * Shows a blinking cursor animation while streaming is active.
 * Renders provider and token count information once streaming completes.
 */

'use client';

import { Box, Typography } from '@mui/material';

/* ========================================================================
   TYPES
   ======================================================================== */

export interface StreamingTextProps {
  /** The accumulated text to display so far */
  text: string;
  /** Whether the stream is currently active */
  isStreaming: boolean;
  /** AI provider name, shown after streaming completes */
  provider?: string;
  /** Total tokens streamed, shown after streaming completes */
  tokenCount?: number;
}

/* ========================================================================
   STYLES
   ======================================================================== */

const cursorKeyframes = `
@keyframes blink-cursor {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
`;

/* ========================================================================
   COMPONENT
   ======================================================================== */

export function StreamingText({
  text,
  isStreaming,
  provider,
  tokenCount,
}: StreamingTextProps): JSX.Element {
  const showMeta = !isStreaming && provider;

  return (
    <Box>
      {/* Inject keyframes for blinking cursor */}
      {isStreaming && (
        <style>{cursorKeyframes}</style>
      )}

      <Box
        sx={{
          p: 2,
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1,
          bgcolor: 'action.hover',
          maxHeight: 400,
          overflow: 'auto',
          position: 'relative',
        }}
      >
        <Typography
          variant="body2"
          component="div"
          sx={{
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            lineHeight: 1.7,
            minHeight: 24,
          }}
        >
          {text || (isStreaming ? '' : 'No content')}
          {isStreaming && (
            <Box
              component="span"
              sx={{
                display: 'inline-block',
                width: '2px',
                height: '1em',
                bgcolor: 'primary.main',
                verticalAlign: 'text-bottom',
                ml: '1px',
                animation: 'blink-cursor 0.8s step-end infinite',
              }}
            />
          )}
        </Typography>
      </Box>

      {showMeta && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ mt: 1, display: 'block' }}
        >
          Provider: {provider}
          {tokenCount !== undefined && ` | Tokens: ${tokenCount.toLocaleString()}`}
        </Typography>
      )}
    </Box>
  );
}

export default StreamingText;
