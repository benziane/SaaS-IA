'use client';

import { useEffect, useState } from 'react';

export default function OfflinePage() {
  const [lastSync, setLastSync] = useState<string>('');
  const [isRetrying, setIsRetrying] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('saas-ia-last-sync');
    if (stored) {
      setLastSync(new Date(stored).toLocaleString());
    }
  }, []);

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      const response = await fetch('/dashboard', { method: 'HEAD', cache: 'no-store' });
      if (response.ok) {
        window.location.href = '/dashboard';
        return;
      }
    } catch {
      // Still offline
    }
    setIsRetrying(false);
  };

  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Offline - SaaS-IA</title>
      </head>
      <body>
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%)',
            color: '#e0e0e0',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            padding: '24px',
            textAlign: 'center',
          }}
        >
          {/* Offline icon */}
          <div
            style={{
              width: 120,
              height: 120,
              borderRadius: '50%',
              background: 'rgba(37, 99, 235, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 32,
              border: '2px solid rgba(37, 99, 235, 0.3)',
            }}
          >
            <svg
              width="56"
              height="56"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#2563eb"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="1" y1="1" x2="23" y2="23" />
              <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
              <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
              <path d="M10.71 5.05A16 16 0 0 1 22.56 9" />
              <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
              <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
              <line x1="12" y1="20" x2="12.01" y2="20" />
            </svg>
          </div>

          <h1
            style={{
              fontSize: 28,
              fontWeight: 700,
              marginBottom: 12,
              background: 'linear-gradient(90deg, #2563eb, #7c3aed)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            You&apos;re Offline
          </h1>

          <p
            style={{
              fontSize: 16,
              color: '#a0a0a0',
              maxWidth: 400,
              lineHeight: 1.6,
              marginBottom: 32,
            }}
          >
            SaaS-IA needs an internet connection to work properly.
            Please check your network connection and try again.
          </p>

          <button
            onClick={handleRetry}
            disabled={isRetrying}
            style={{
              padding: '14px 40px',
              fontSize: 16,
              fontWeight: 600,
              color: '#ffffff',
              background: isRetrying
                ? 'rgba(37, 99, 235, 0.4)'
                : 'linear-gradient(135deg, #2563eb, #7c3aed)',
              border: 'none',
              borderRadius: 12,
              cursor: isRetrying ? 'wait' : 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: isRetrying ? 'none' : '0 4px 16px rgba(37, 99, 235, 0.3)',
            }}
          >
            {isRetrying ? 'Checking connection...' : 'Retry Connection'}
          </button>

          {lastSync && (
            <p
              style={{
                marginTop: 24,
                fontSize: 13,
                color: '#666',
              }}
            >
              Last synced: {lastSync}
            </p>
          )}

          <div
            style={{
              position: 'absolute',
              bottom: 24,
              fontSize: 12,
              color: '#444',
            }}
          >
            SaaS-IA v3.9.0
          </div>
        </div>
      </body>
    </html>
  );
}
