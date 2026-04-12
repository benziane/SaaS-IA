/**
 * Dashboard Not Found Page (404)
 * Displayed when a route within the dashboard does not match any known page.
 * Renders inside the dashboard layout so navigation remains usable.
 * Uses plain HTML/CSS for maximum reliability.
 */

export default function DashboardNotFound() {
  return (
    <div style={styles.wrapper}>
      <div style={styles.card}>
        <div style={styles.code}>404</div>

        <h2 style={styles.title}>Page not found</h2>

        <p style={styles.message}>
          The page you are looking for does not exist or has been moved.
          Please check the URL or navigate to another section using the sidebar.
        </p>

        <div style={styles.actions}>
          <a href="/dashboard" style={styles.primaryLink}>
            Back to Dashboard
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
    minHeight: '50vh',
    padding: '24px',
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
  card: {
    maxWidth: '480px',
    width: '100%',
    backgroundColor: 'var(--bg-surface)',
    borderRadius: '8px',
    padding: '48px 32px',
    textAlign: 'center' as const,
    boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
  },
  code: {
    fontSize: '64px',
    fontWeight: 700,
    color: 'var(--accent)',
    lineHeight: 1,
    marginBottom: '12px',
    letterSpacing: '-2px',
  },
  title: {
    fontSize: '20px',
    fontWeight: 600,
    color: 'var(--text-high)',
    margin: '0 0 12px 0',
    lineHeight: 1.3,
  },
  message: {
    fontSize: '14px',
    color: 'var(--text-mid)',
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
};
