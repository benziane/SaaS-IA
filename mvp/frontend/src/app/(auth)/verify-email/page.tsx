'use client';

import { useMutation } from '@tanstack/react-query';
import { Loader2, Mail, MailCheck, MailX } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import type { ReactElement } from 'react';

import apiClient from '@/lib/apiClient';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';

/* ========================================================================
   TYPES
   ======================================================================== */

type VerifyState = 'loading' | 'success' | 'error' | 'no-token';

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function VerifyEmailPage(): ReactElement {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [state, setState] = useState<VerifyState>(token ? 'loading' : 'no-token');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [resendEmail, setResendEmail] = useState('');
  const [resent, setResent] = useState(false);

  const resendMutation = useMutation({
    mutationFn: () => apiClient.post('/api/auth/resend-verify', { email: resendEmail }),
  });

  useEffect(() => {
    if (!token) return;

    let cancelled = false;

    const verify = async (): Promise<void> => {
      try {
        await apiClient.post('/api/auth/verify-email', { token });
        if (!cancelled) setState('success');
      } catch (err: unknown) {
        if (!cancelled) {
          const message =
            err instanceof Error
              ? err.message
              : 'The verification link is invalid or has expired.';
          setErrorMessage(message);
          setState('error');
        }
      }
    };

    void verify();

    return () => {
      cancelled = true;
    };
  }, [token]);

  /* ========================================================================
     RENDER
     ======================================================================== */

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden"
      style={{ background: 'var(--bg-app)' }}
    >
      {/* Skip to main content - Accessibility */}
      <a href="#main-content" className="skip-to-main">Skip to main content</a>
      {/* Subtle grid pattern */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{ backgroundImage: 'repeating-linear-gradient(0deg, var(--border) 0px, var(--border) 1px, transparent 1px, transparent 48px), repeating-linear-gradient(90deg, var(--border) 0px, var(--border) 1px, transparent 1px, transparent 48px)' }} />

      {/* Auth card */}
      <div
        id="main-content"
        role="main"
        aria-labelledby="verify-email-title"
        className="glass relative z-10 w-full max-w-[440px] rounded-2xl p-8 shadow-[var(--shadow-xl)] animate-enter"
      >
        {/* ================================================================
            LOADING STATE
            ================================================================ */}
        {state === 'loading' && (
          <div className="flex flex-col items-center text-center">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4 animate-pulse-glow bg-[var(--bg-elevated)] border border-[var(--border)]"
            >
              <Loader2 className="h-7 w-7 text-white animate-spin" />
            </div>
            <h1
              id="verify-email-title"
              className="text-xl font-bold text-[var(--text-high)] tracking-tight mb-2"
            >
              Verifying your email…
            </h1>
            <p className="text-sm text-[var(--text-mid)]">
              Please wait while we confirm your address.
            </p>
            <div className="mt-6 w-full space-y-2">
              <div
                className="h-2 rounded-full animate-pulse"
                style={{ background: 'var(--bg-elevated)' }}
              />
              <div
                className="h-2 rounded-full animate-pulse w-3/4 mx-auto"
                style={{ background: 'var(--bg-elevated)' }}
              />
            </div>
          </div>
        )}

        {/* ================================================================
            SUCCESS STATE
            ================================================================ */}
        {state === 'success' && (
          <div className="flex flex-col items-center text-center">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)' }}
            >
              <MailCheck className="h-6 w-6 text-[var(--accent)]" />
            </div>
            <h1
              id="verify-email-title"
              className="text-xl font-bold text-[var(--text-high)] tracking-tight mb-2"
            >
              Email verified!
            </h1>
            <p className="text-sm text-[var(--text-mid)] mb-8">
              Your account is now active. You can sign in and start using SaaS-IA.
            </p>
            <Link href="/login" className="w-full">
              <Button className="w-full" size="lg" aria-label="Go to Login">
                Go to Login
              </Button>
            </Link>
          </div>
        )}

        {/* ================================================================
            ERROR STATE
            ================================================================ */}
        {state === 'error' && (
          <div className="flex flex-col items-center text-center">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)' }}
            >
              <MailX className="h-6 w-6 text-[var(--accent)]" />
            </div>
            <h1
              id="verify-email-title"
              className="text-xl font-bold text-[var(--text-high)] tracking-tight mb-2"
            >
              Verification failed
            </h1>
            <p className="text-sm text-[var(--text-mid)] mb-2">
              {errorMessage || 'The verification link is invalid or has expired.'}
            </p>
            <p className="text-xs text-[var(--text-low)] mb-8">
              Request a new link by signing in, or contact support if the issue persists.
            </p>
            <Link href="/login" className="w-full">
              <Button className="w-full" size="lg" variant="outline" aria-label="Back to sign in">
                Back to Sign In
              </Button>
            </Link>
            {!resent ? (
              <div className="mt-4 space-y-2">
                <p className="text-xs text-[var(--text-low)]">Enter your email to resend the verification link:</p>
                <div className="flex gap-2">
                  <Input
                    type="email"
                    placeholder="your@email.com"
                    value={resendEmail}
                    onChange={(e) => setResendEmail(e.target.value)}
                    className="text-sm"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!resendEmail.trim() || resendMutation.isPending}
                    onClick={() => resendMutation.mutate(undefined, { onSuccess: () => setResent(true) })}
                  >
                    {resendMutation.isPending ? <Loader2 className="h-3 w-3 animate-spin" /> : 'Resend'}
                  </Button>
                </div>
              </div>
            ) : (
              <p className="mt-3 text-sm text-green-500">Verification email resent!</p>
            )}
          </div>
        )}

        {/* ================================================================
            NO-TOKEN STATE
            ================================================================ */}
        {state === 'no-token' && (
          <div className="flex flex-col items-center text-center">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4 animate-pulse-glow bg-[var(--bg-elevated)] border border-[var(--border)]"
            >
              <Mail className="h-6 w-6 text-[var(--accent)]" />
            </div>
            <h1
              id="verify-email-title"
              className="text-xl font-bold text-[var(--text-high)] tracking-tight mb-2"
            >
              Invalid link
            </h1>
            <p className="text-sm text-[var(--text-mid)] mb-2">
              This verification link is missing a token.
            </p>
            <p className="text-xs text-[var(--text-low)] mb-8">
              Please use the exact link from your confirmation email. If you need a new
              one, sign in to request another.
            </p>
            <Link href="/login" className="w-full">
              <Button className="w-full" size="lg" variant="outline" aria-label="Back to sign in">
                Back to Sign In
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
