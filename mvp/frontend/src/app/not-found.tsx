/**
 * Not Found Page (404)
 * Displayed when a route does not match any known page.
 * Uses plain HTML/CSS for maximum reliability.
 */

import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Page Not Found',
};

export default function NotFound() {
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.code}>404</div>

        <h1 style={styles.title}>Page not found</h1>

        <p style={styles.message}>
          The page you are looking for does not exist or has been moved.
          Please check the URL or return to the home page.
        </p>

        <div style={styles.actions}>
          <a
            href="/"
            style={styles.primaryLink}
          >
            Return to home
          </a>
          <a
            href="/dashboard"
            style={styles.secondaryLink}
          >
            Go to dashboard
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
  code: {
    fontSize: '72px',
    fontWeight: 700,
    color: '#7367f0',
    lineHeight: 1,
    marginBottom: '12px',
    letterSpacing: '-2px',
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
    margin: '0 0 32px 0',
  },
  actions: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center',
    flexWrap: 'wrap' as const,
  },
  primaryLink: {
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
    textDecoration: 'none',
  },
  secondaryLink: {
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
    textDecoration: 'none',
  },
};
