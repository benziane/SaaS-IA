'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, EyeOff, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import type { ReactElement } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';

import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { useRegister } from '@/features/auth/hooks';
import { registerSchema } from '@/features/auth/schemas';

/* ========================================================================
   EXTENDED SCHEMA — adds full_name on top of the base registerSchema
   ======================================================================== */

const registerPageSchema = registerSchema.and(
  z.object({
    fullName: z
      .string()
      .min(1, 'Full name is required')
      .min(2, 'Name must be at least 2 characters')
      .max(100, 'Name is too long')
      .trim(),
  })
);

type RegisterPageSchema = z.infer<typeof registerPageSchema>;

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function RegisterPage(): ReactElement {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const registerMutation = useRegister();

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterPageSchema>({
    resolver: zodResolver(registerPageSchema),
    defaultValues: {
      fullName: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
    mode: 'onBlur',
  });

  const onSubmit = async (data: RegisterPageSchema): Promise<void> => {
    await registerMutation.mutateAsync({
      email: data.email,
      password: data.password,
    });
  };

  const quickRegister = async (): Promise<void> => {
    try {
      await registerMutation.mutateAsync({
        email: `dev+${Date.now()}@saas-ia.com`,
        password: 'DevPass123',
      });
    } catch { /* handled by hook */ }
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
        aria-labelledby="register-title"
        className="glass relative z-10 w-full max-w-[440px] rounded-2xl p-8 shadow-[var(--shadow-xl)] animate-enter"
      >
        {/* Logo & branding */}
        <div className="flex flex-col items-center mb-8">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4 animate-pulse-glow"
            className="bg-[var(--bg-elevated)] border border-[var(--border)]"
          >
            <Sparkles className="h-6 w-6 text-[var(--accent)]" />
          </div>
          <h1
            id="register-title"
            className="text-xl font-bold text-[var(--text-high)] tracking-tight mb-1"
          >
            Create your account
          </h1>
          <p className="text-sm text-[var(--text-mid)]">Start your AI journey today</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">

          {/* Full Name */}
          <Controller name="fullName" control={control} render={({ field }) => (
            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">
                Full name
              </label>
              <Input
                {...field}
                id="fullName"
                type="text"
                autoComplete="name"
                placeholder="Jane Smith"
                className={errors.fullName ? 'border-red-500/60' : ''}
                aria-required="true"
                aria-invalid={!!errors.fullName}
                aria-describedby={errors.fullName ? 'fullName-error' : undefined}
              />
              {errors.fullName && (
                <p id="fullName-error" className="mt-1.5 text-xs text-[var(--error)]">
                  {errors.fullName.message}
                </p>
              )}
            </div>
          )} />

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

          {/* Password */}
          <Controller name="password" control={control} render={({ field }) => (
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">
                Password
              </label>
              <div className="relative">
                <Input
                  {...field}
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  placeholder="••••••••"
                  className={`pr-10 ${errors.password ? 'border-red-500/60' : ''}`}
                  aria-required="true"
                  aria-invalid={!!errors.password}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-low)] hover:text-[var(--text-high)] transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  onClick={() => setShowPassword(!showPassword)}
                  onMouseDown={(e) => e.preventDefault()}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && (
                <p id="password-error" className="mt-1.5 text-xs text-[var(--error)]">
                  {errors.password.message}
                </p>
              )}
            </div>
          )} />

          {/* Confirm Password */}
          <Controller name="confirmPassword" control={control} render={({ field }) => (
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">
                Confirm password
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
                  aria-describedby={errors.confirmPassword ? 'confirmPassword-error' : undefined}
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-low)] hover:text-[var(--text-high)] transition-colors"
                  aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  onMouseDown={(e) => e.preventDefault()}
                >
                  {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p id="confirmPassword-error" className="mt-1.5 text-xs text-[var(--error)]">
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
            disabled={isSubmitting || registerMutation.isPending}
            aria-label="Create your account"
          >
            {isSubmitting || registerMutation.isPending ? 'Creating account…' : 'Create Account'}
          </Button>
        </form>

        {/* Login link */}
        <p className="text-center text-sm text-[var(--text-mid)] mt-6">
          Already have an account?{' '}
          <Link href="/login" className="font-semibold text-[var(--accent)] hover:underline">
            Sign in instead
          </Link>
        </p>

        {/* Quick Register (DEV only) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-6 pt-5 border-t border-[var(--border)]">
            <p className="text-xs font-semibold text-[var(--warning)] mb-3 text-center uppercase tracking-wider">
              Dev Quick Register
            </p>
            <Button
              className="w-full"
              variant="outline"
              size="md"
              onClick={quickRegister}
              disabled={isSubmitting || registerMutation.isPending}
            >
              {registerMutation.isPending ? 'Registering…' : 'Create dev account'}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
