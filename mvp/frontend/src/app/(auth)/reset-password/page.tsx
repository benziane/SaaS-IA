'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { CheckCircle2, Eye, EyeOff, KeyRound } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';

import apiClient, { extractErrorMessage } from '@/lib/apiClient';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';

/* ========================================================================
   SCHEMA
   ======================================================================== */

const resetPasswordSchema = z
  .object({
    newPassword: z
      .string()
      .min(1, 'Password is required')
      .min(8, 'Password must be at least 8 characters'),
    confirmPassword: z
      .string()
      .min(1, 'Please confirm your password'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

type ResetPasswordSchema = z.infer<typeof resetPasswordSchema>;

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function ResetPasswordPage(): JSX.Element {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [success, setSuccess] = useState(false);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordSchema>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { newPassword: '', confirmPassword: '' },
    mode: 'onBlur',
  });

  const resetMutation = useMutation({
    mutationFn: (data: ResetPasswordSchema) =>
      apiClient.post('/api/auth/reset-password', {
        token,
        password: data.newPassword,
      }),
    onSuccess: () => {
      setSuccess(true);
    },
  });

  const onSubmit = async (data: ResetPasswordSchema): Promise<void> => {
    await resetMutation.mutateAsync(data);
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

      {/* Background radial glows */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-10"
          style={{ background: 'radial-gradient(circle, var(--accent) 0%, transparent 70%)' }}
        />
        <div
          className="absolute top-0 right-0 w-96 h-96 rounded-full opacity-5"
          style={{ background: 'radial-gradient(circle, #a855f7 0%, transparent 70%)' }}
        />
        <div
          className="absolute bottom-0 left-0 w-80 h-80 rounded-full opacity-5"
          style={{ background: 'radial-gradient(circle, #05c3db 0%, transparent 70%)' }}
        />
      </div>

      {/* Auth card */}
      <div
        id="main-content"
        role="main"
        aria-labelledby="reset-password-title"
        className="glass relative z-10 w-full max-w-[420px] rounded-2xl p-8 shadow-[var(--shadow-xl)] animate-enter"
      >
        {/* ================================================================
            INVALID TOKEN STATE
            ================================================================ */}
        {!token ? (
          <div className="flex flex-col items-center text-center">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)' }}
            >
              <KeyRound className="h-7 w-7 text-white" />
            </div>
            <h1 className="text-xl font-bold text-[var(--text-high)] tracking-tight mb-2">
              Invalid Reset Link
            </h1>
            <p className="text-sm text-[var(--text-mid)] mb-8">
              This password reset link is invalid or has expired. Please request a new one.
            </p>
            <Link
              href="/forgot-password"
              className="text-sm font-semibold text-[var(--accent)] hover:underline"
            >
              Request a new link
            </Link>
          </div>
        ) : success ? (
          /* ================================================================
             SUCCESS STATE
             ================================================================ */
          <div className="flex flex-col items-center text-center">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4"
              style={{ background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)' }}
            >
              <CheckCircle2 className="h-7 w-7 text-white" />
            </div>
            <h1 className="text-xl font-bold text-[var(--text-high)] tracking-tight mb-2">
              Password updated!
            </h1>
            <p className="text-sm text-[var(--text-mid)] mb-8">
              Password updated! You can now log in.
            </p>
            <Link
              href="/login"
              className="text-sm font-semibold text-[var(--accent)] hover:underline"
            >
              Go to sign in
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
                className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4 animate-pulse-glow"
                style={{ background: 'linear-gradient(135deg, var(--accent) 0%, #a855f7 100%)' }}
              >
                <KeyRound className="h-7 w-7 text-white" />
              </div>
              <h1
                id="reset-password-title"
                className="text-xl font-bold text-[var(--text-high)] tracking-tight mb-1"
              >
                Reset Password
              </h1>
              <p className="text-sm text-[var(--text-mid)]">
                Enter your new password below
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">

              {/* New Password */}
              <Controller name="newPassword" control={control} render={({ field }) => (
                <div>
                  <label htmlFor="newPassword" className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">
                    New Password
                  </label>
                  <div className="relative">
                    <Input
                      {...field}
                      id="newPassword"
                      type={showNewPassword ? 'text' : 'password'}
                      autoComplete="new-password"
                      placeholder="••••••••"
                      className={`pr-10 ${errors.newPassword ? 'border-red-500/60' : ''}`}
                      aria-required="true"
                      aria-invalid={!!errors.newPassword}
                      aria-describedby={errors.newPassword ? 'new-password-error' : undefined}
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-low)] hover:text-[var(--text-high)] transition-colors"
                      aria-label={showNewPassword ? 'Hide password' : 'Show password'}
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      onMouseDown={(e) => e.preventDefault()}
                    >
                      {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {errors.newPassword && (
                    <p id="new-password-error" className="mt-1.5 text-xs text-[var(--error)]">
                      {errors.newPassword.message}
                    </p>
                  )}
                </div>
              )} />

              {/* Confirm Password */}
              <Controller name="confirmPassword" control={control} render={({ field }) => (
                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <Input
                      {...field}
                      id="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      autoComplete="new-password"
                      placeholder="••••••••"
                      className={`pr-10 ${errors.confirmPassword ? 'border-red-500/60' : ''}`}
                      aria-required="true"
                      aria-invalid={!!errors.confirmPassword}
                      aria-describedby={errors.confirmPassword ? 'confirm-password-error' : undefined}
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-low)] hover:text-[var(--text-high)] transition-colors"
                      aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      onMouseDown={(e) => e.preventDefault()}
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {errors.confirmPassword && (
                    <p id="confirm-password-error" className="mt-1.5 text-xs text-[var(--error)]">
                      {errors.confirmPassword.message}
                    </p>
                  )}
                </div>
              )} />

              {/* Submit */}
              <Button
                type="submit"
                className="w-full"
                size="lg"
                disabled={isSubmitting || resetMutation.isPending}
                aria-label="Update password"
              >
                {isSubmitting || resetMutation.isPending ? 'Updating…' : 'Update Password'}
              </Button>

              {resetMutation.isError && (
                <p className="text-center text-xs text-[var(--error)]">
                  {extractErrorMessage(resetMutation.error)}
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
