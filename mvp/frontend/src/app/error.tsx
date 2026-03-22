'use client';

/**
 * Global Error Boundary
 * Catches unhandled errors across all routes.
 * Uses plain HTML/CSS to avoid dependency failures in the error boundary itself.
 */

import { useEffect } from 'react';

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
  useEffect(() => {
    console.error('[GlobalError] Unhandled application error:', error);
  }, [error]);

  const isDev = process.env.NODE_ENV === 'development';

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.iconWrapper}>
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#ea5455"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>

        <h1 style={styles.title}>Something went wrong</h1>

        <p style={styles.message}>
          An unexpected error occurred. Our team has been notified. Please try
          again or return to the home page.
        </p>

        {isDev && (
          <details style={styles.details}>
            <summary style={styles.summary}>Error details (development only)</summary>
            <pre style={styles.pre}>
              {error.message}
              {error.stack ? `\n\n${error.stack}` : ''}
              {error.digest ? `\n\nDigest: ${error.digest}` : ''}
            </pre>
          </details>
        )}

        <div style={styles.actions}>
          <button
            type="button"
            onClick={reset}
            style={styles.primaryButton}
            onMouseOver={(e) => {
              (e.target as HTMLButtonElement).style.opacity = '0.9';
            }}
            onMouseOut={(e) => {
              (e.target as HTMLButtonElement).style.opacity = '1';
            }}
          >
            Try again
          </button>
          <a
            href="/"
            style={styles.secondaryButton}
            onMouseOver={(e) => {
              (e.target as HTMLAnchorElement).style.backgroundColor = '#f5f5f5';
            }}
            onMouseOut={(e) => {
              (e.target as HTMLAnchorElement).style.backgroundColor = 'transparent';
            }}
          >
            Return to home
          </a>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    padding: '24px',
    backgroundColor: '#f8f7fa',
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
  card: {
    maxWidth: '480px',
    width: '100%',
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    padding: '48px 32px',
    textAlign: 'center' as const,
    boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
  },
  iconWrapper: {
    marginBottom: '24px',
  },
  title: {
    fontSize: '22px',
    fontWeight: 600,
    color: '#2f2b3d',
    margin: '0 0 12px 0',
    lineHeight: 1.3,
  },
  message: {
    fontSize: '15px',
    color: '#6e6b7b',
    lineHeight: 1.6,
    margin: '0 0 24px 0',
  },
  details: {
    textAlign: 'left' as const,
    marginBottom: '24px',
    border: '1px solid #ebe9f1',
    borderRadius: '6px',
    padding: '12px',
  },
  summary: {
    fontSize: '13px',
    color: '#a8aaae',
    cursor: 'pointer',
    userSelect: 'none' as const,
  },
  pre: {
    fontSize: '12px',
    color: '#ea5455',
    whiteSpace: 'pre-wrap' as const,
    wordBreak: 'break-word' as const,
    marginTop: '12px',
    padding: '12px',
    backgroundColor: '#fff5f5',
    borderRadius: '4px',
    maxHeight: '200px',
    overflow: 'auto',
  },
  actions: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center',
    flexWrap: 'wrap' as const,
  },
  primaryButton: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '10px 24px',
    fontSize: '15px',
    fontWeight: 500,
    color: '#ffffff',
    backgroundColor: '#7367f0',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'opacity 0.2s ease',
    textDecoration: 'none',
  },
  secondaryButton: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '10px 24px',
    fontSize: '15px',
    fontWeight: 500,
    color: '#6e6b7b',
    backgroundColor: 'transparent',
    border: '1px solid #ebe9f1',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
    textDecoration: 'none',
  },
};
