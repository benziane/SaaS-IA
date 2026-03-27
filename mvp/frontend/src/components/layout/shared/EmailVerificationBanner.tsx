'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Mail, X, Loader2, CheckCircle2 } from 'lucide-react';
import apiClient from '@/lib/apiClient';
import { useCurrentUser } from '@/features/auth/hooks';

export function EmailVerificationBanner() {
  const { data: user } = useCurrentUser();
  const [dismissed, setDismissed] = useState(false);
  const [sent, setSent] = useState(false);

  const resendMutation = useMutation({
    mutationFn: () =>
      apiClient.post('/api/auth/resend-verify', { email: user?.email }),
    onSuccess: () => setSent(true),
  });

  if (!user || user.email_verified || dismissed) return null;

  return (
    <div
      role="alert"
      className="flex items-center justify-between gap-3 px-5 py-3 border-b border-amber-500/30 bg-amber-500/8 text-sm"
    >
      <div className="flex items-center gap-2 min-w-0">
        <Mail className="h-4 w-4 text-amber-500 shrink-0" />
        {sent ? (
          <span className="flex items-center gap-1.5 text-[var(--text-mid)]">
            <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
            Verification email sent to{' '}
            <strong className="text-[var(--text-high)]">{user.email}</strong>
          </span>
        ) : (
          <span className="text-[var(--text-mid)]">
            Please verify your email address.{' '}
            <button
              onClick={() => resendMutation.mutate()}
              disabled={resendMutation.isPending}
              className="font-semibold text-[var(--accent)] hover:underline disabled:opacity-50 inline-flex items-center gap-1"
            >
              {resendMutation.isPending && (
                <Loader2 className="h-3 w-3 animate-spin" />
              )}
              Resend verification email
            </button>
          </span>
        )}
      </div>
      <button
        onClick={() => setDismissed(true)}
        aria-label="Dismiss"
        className="shrink-0 p-0.5 rounded hover:bg-[var(--bg-elevated)] text-[var(--text-low)] hover:text-[var(--text-mid)] transition-colors"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
