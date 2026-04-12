/**
 * Dashboard Loading State
 * Displayed while dashboard pages are loading.
 * Uses plain HTML/CSS for maximum reliability and fast rendering.
 */

export default function DashboardLoading() {
  return (
    <div style={styles.wrapper}>
      <div style={styles.spinnerContainer}>
        <div style={styles.spinner} />
        <style>{`
          @keyframes dashboard-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
      <p style={styles.text}>Loading...</p>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  wrapper: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '50vh',
    padding: '24px',
    gap: '16px',
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
  spinnerContainer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '3px solid var(--border)',
    borderTopColor: 'var(--accent)',
    borderRadius: '50%',
    animation: 'dashboard-spin 0.8s linear infinite',
  },
  text: {
    fontSize: '14px',
    color: 'var(--text-mid)',
    margin: 0,
  },
};
