/**
 * StreamingText - Displays text that streams in token by token
 * Shows a blinking cursor animation while streaming is active.
 * Renders provider and token count information once streaming completes.
 */

'use client';

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
    <div>
      {/* Inject keyframes for blinking cursor */}
      {isStreaming && (
        <style>{cursorKeyframes}</style>
      )}

      <div className="p-4 border border-[var(--border)] rounded-[var(--radius-md,6px)] bg-[var(--bg-elevated)] max-h-[400px] overflow-auto relative">
        <div className="text-sm whitespace-pre-wrap break-words leading-[1.7] min-h-[24px]">
          {text || (isStreaming ? '' : 'No content')}
          {isStreaming && (
            <span
              className="inline-block w-[2px] h-[1em] bg-[var(--accent)] align-text-bottom ml-[1px]"
              style={{ animation: 'blink-cursor 0.8s step-end infinite' }}
            />
          )}
        </div>
      </div>

      {showMeta && (
        <span className="mt-2 block text-xs text-[var(--text-low)]">
          Provider: {provider}
          {tokenCount !== undefined && ` | Tokens: ${tokenCount.toLocaleString()}`}
        </span>
      )}
    </div>
  );
}

export default StreamingText;
