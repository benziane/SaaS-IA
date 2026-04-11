'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, EyeOff, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import type { ReactElement } from 'react';
import { Controller, useForm } from 'react-hook-form';

import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { useLogin } from '@/features/auth/hooks';
import { loginSchema, type LoginSchema } from '@/features/auth/schemas';

export default function LoginPage(): ReactElement {
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const loginMutation = useLogin();

  const { control, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginSchema>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
    mode: 'onBlur',
  });

  const onSubmit = async (data: LoginSchema): Promise<void> => {
    await loginMutation.mutateAsync(data);
  };

  const quickLogin = async (email: string, password: string): Promise<void> => {
    try { await loginMutation.mutateAsync({ email, password }); } catch { /* handled by hook */ }
  };

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
        aria-labelledby="login-title"
        className="glass relative z-10 w-full max-w-[420px] rounded-2xl p-8 shadow-[var(--shadow-xl)] animate-enter"
      >
        {/* Logo & branding */}
        <div className="flex flex-col items-center mb-8">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 bg-[var(--bg-elevated)] border border-[var(--border)]"
          >
            <Sparkles className="h-6 w-6 text-[var(--accent)]" />
          </div>
          <h1 id="login-title" className="text-xl font-bold text-[var(--text-high)] tracking-tight mb-1">
            Welcome back
          </h1>
          <p className="text-sm text-[var(--text-mid)]">Sign in to your SaaS-IA account</p>
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
                <p id="email-error" className="mt-1.5 text-xs text-[var(--error)]">{errors.email.message}</p>
              )}
            </div>
          )} />

          {/* Password */}
          <Controller name="password" control={control} render={({ field }) => (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="text-sm font-medium text-[var(--text-mid)]">
                  Password
                </label>
                <Link href="/forgot-password"
                  className="text-xs text-[var(--accent)] hover:underline transition-colors">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Input
                  {...field}
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
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
                <p id="password-error" className="mt-1.5 text-xs text-[var(--error)]">{errors.password.message}</p>
              )}
            </div>
          )} />

          {/* Remember me */}
          <label className="flex items-center gap-2.5 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 rounded border-[var(--border)] bg-[var(--bg-elevated)] accent-[var(--accent)]"
              aria-label="Remember me"
            />
            <span className="text-sm text-[var(--text-mid)]">Remember me for 30 days</span>
          </label>

          {/* Submit */}
          <Button
            type="submit"
            className="w-full"
            size="lg"
            disabled={isSubmitting || loginMutation.isPending}
            aria-label="Sign in"
          >
            {isSubmitting || loginMutation.isPending ? 'Signing in…' : 'Sign In'}
          </Button>
        </form>

        {/* Register link */}
        <p className="text-center text-sm text-[var(--text-mid)] mt-6">
          No account?{' '}
          <Link href="/register" className="font-semibold text-[var(--accent)] hover:underline">
            Create one for free
          </Link>
        </p>

        {/* Quick Login (DEV only) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-6 pt-5 border-t border-[var(--border)]">
            <p className="text-xs font-semibold text-[var(--warning)] mb-3 text-center uppercase tracking-wider">
              Dev Quick Login
            </p>
            <Button
              className="w-full"
              variant="outline"
              size="md"
              onClick={() => quickLogin('admin@saas-ia.com', 'admin123')}
              disabled={isSubmitting || loginMutation.isPending}
            >
              {loginMutation.isPending ? 'Logging in…' : 'Admin — admin@saas-ia.com'}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
