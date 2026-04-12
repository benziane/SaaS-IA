'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { CheckCircle2, Mail } from 'lucide-react';
import Link from 'next/link';
import { useState, type ReactElement } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';

import apiClient from '@/lib/apiClient';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';

/* ========================================================================
   SCHEMA
   ======================================================================== */

const forgotPasswordSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Invalid email address')
    .toLowerCase()
    .trim(),
});

type ForgotPasswordSchema = z.infer<typeof forgotPasswordSchema>;

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function ForgotPasswordPage(): ReactElement {
  const [sent, setSent] = useState(false);

  const {
    control,
    handleSubmit,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordSchema>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: '' },
    mode: 'onBlur',
  });

  const forgotMutation = useMutation({
    mutationFn: (data: ForgotPasswordSchema) =>
      apiClient.post('/api/auth/forgot-password', { email: data.email }),
    onSuccess: () => {
      setSent(true);
    },
  });

  const onSubmit = async (data: ForgotPasswordSchema): Promise<void> => {
    await forgotMutation.mutateAsync(data);
  };

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
        aria-labelledby="forgot-password-title"
        className="glass relative z-10 w-full max-w-[440px] rounded-2xl p-8 shadow-[var(--shadow-xl)] animate-enter"
      >
        {sent ? (
          /* ================================================================
             SUCCESS STATE
             ================================================================ */
          <div className="flex flex-col items-center text-center">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)' }}
            >
              <CheckCircle2 className="h-6 w-6 text-[var(--accent)]" />
            </div>
            <h1 className="text-xl font-bold text-[var(--text-high)] tracking-tight mb-2">
              Check your inbox
            </h1>
            <p className="text-sm text-[var(--text-mid)] mb-2">
              We sent a password reset link to
            </p>
            <p className="text-sm font-semibold text-[var(--text-high)] mb-6">
              {getValues('email')}
            </p>
            <p className="text-xs text-[var(--text-low)] mb-8">
              Didn&apos;t receive the email? Check your spam folder or{' '}
              <button
                type="button"
                className="text-[var(--accent)] hover:underline"
                onClick={() => setSent(false)}
              >
                try again
              </button>
              .
            </p>
            <Link
              href="/login"
              className="text-sm font-semibold text-[var(--accent)] hover:underline"
            >
              Back to sign in
            </Link>
          </div>
        ) : (
          /* ================================================================
             FORM STATE
             ================================================================ */
          <>
            {/* Logo & branding */}
            <div className="flex flex-col items-center mb-8">
              <div
                className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4 bg-[var(--bg-elevated)] border border-[var(--border)]"
              >
                <Mail className="h-6 w-6 text-[var(--accent)]" />
              </div>
              <h1
                id="forgot-password-title"
                className="text-xl font-bold text-[var(--text-high)] tracking-tight mb-1"
              >
                Reset Password
              </h1>
              <p className="text-sm text-[var(--text-mid)] text-center">
                We&apos;ll send you a link to reset your password
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">

              {/* Email */}
              <Controller name="email" control={control} render={({ field }) => (
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">
                    Email address
                  </label>
                  <Input
                    {...field}
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="you@company.com"
                    className={errors.email ? 'border-red-500/60' : ''}
                    aria-required="true"
                    aria-invalid={!!errors.email}
                    aria-describedby={errors.email ? 'email-error' : undefined}
                  />
                  {errors.email && (
                    <p id="email-error" className="mt-1.5 text-xs text-[var(--error)]">
                      {errors.email.message}
                    </p>
                  )}
                </div>
              )} />

              {/* Submit */}
              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={isSubmitting || forgotMutation.isPending}
                aria-label="Send reset link"
              >
                {isSubmitting || forgotMutation.isPending ? 'Sending…' : 'Send Reset Link'}
              </Button>

              {forgotMutation.isError && (
                <p className="text-center text-xs text-[var(--error)]">
                  Something went wrong. Please try again.
                </p>
              )}
            </form>

            {/* Back to login */}
            <p className="text-center text-sm text-[var(--text-mid)] mt-6">
              Remembered your password?{' '}
              <Link href="/login" className="font-semibold text-[var(--accent)] hover:underline">
                Sign in
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
