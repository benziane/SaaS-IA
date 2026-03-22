'use client';

/**
 * Dashboard Error Boundary
 * Catches errors within the dashboard route group.
 * Renders inside the dashboard layout so navigation remains usable.
 * Uses plain HTML/CSS to avoid dependency failures in the error boundary itself.
 */

import { useEffect } from 'react';

interface DashboardErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function DashboardError({ error, reset }: DashboardErrorProps) {
  useEffect(() => {
    console.error('[DashboardError] Error in dashboard route:', error);
  }, [error]);

  const isDev = process.env.NODE_ENV === 'development';

  return (
    <div style={styles.wrapper}>
      <div style={styles.card}>
        <div style={styles.iconWrapper}>
          <svg
            width="40"
            height="40"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#ea5455"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>

        <h2 style={styles.title}>An error occurred</h2>

        <p style={styles.message}>
          Something went wrong while loading this page. You can try again or
          navigate to another section using the sidebar.
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
            href="/dashboard"
            style={styles.secondaryButton}
            onMouseOver={(e) => {
              (e.target as HTMLAnchorElement).style.backgroundColor = '#f5f5f5';
            }}
            onMouseOut={(e) => {
              (e.target as HTMLAnchorElement).style.backgroundColor = 'transparent';
            }}
          >
            Go to dashboard
          </a>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '60vh',
    padding: '24px',
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
  card: {
    maxWidth: '480px',
    width: '100%',
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    padding: '40px 32px',
    textAlign: 'center' as const,
    boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
  },
  iconWrapper: {
    marginBottom: '20px',
  },
  title: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#2f2b3d',
    margin: '0 0 12px 0',
    lineHeight: 1.3,
  },
  message: {
    fontSize: '14px',
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
