/**
 * Login Page - Grade S++
 * User authentication page
 */

'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, EyeOff } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { useLogin } from '@/features/auth/hooks';
import { loginSchema, type LoginSchema } from '@/features/auth/schemas';

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function LoginPage(): JSX.Element {
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const loginMutation = useLogin();

  /* Form */
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginSchema>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
    mode: 'onBlur',
  });

  /* Handlers */
  const onSubmit = async (data: LoginSchema): Promise<void> => {
    await loginMutation.mutateAsync(data);
  };

  const handleClickShowPassword = (): void => {
    setShowPassword(!showPassword);
  };

  const handleMouseDownPassword = (event: React.MouseEvent<HTMLButtonElement>): void => {
    event.preventDefault();
  };

  /* Quick Login for Development */
  const quickLogin = async (email: string, password: string): Promise<void> => {
    try {
      await loginMutation.mutateAsync({ email, password });
    } catch {
      // Error is already handled by useLogin hook (toast)
    }
  };

  /* ========================================================================
     RENDER
     ======================================================================== */

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-app)] p-4">
      {/* Skip to main content - Accessibility S++ */}
      <a href="#main-content" className="skip-to-main">
        Skip to main content
      </a>

      <Card
        id="main-content"
        className="max-w-[450px] w-full"
        role="main"
        aria-labelledby="login-title"
      >
        <CardContent className="p-8">
          {/* Header */}
          <div className="mb-8 text-center">
            <h1
              id="login-title"
              className="text-2xl font-semibold text-[var(--text-high)] mb-2"
            >
              Welcome to SaaS-IA 👋
            </h1>
            <p className="text-sm text-[var(--text-mid)]">
              Please sign in to your account
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            {/* Email Field */}
            <Controller
              name="email"
              control={control}
              render={({ field }) => (
                <div className="mb-6">
                  <label htmlFor="email" className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">
                    Email
                  </label>
                  <Input
                    {...field}
                    id="email"
                    type="email"
                    autoComplete="email"
                    className={errors.email ? 'border-red-500 focus:ring-red-500' : ''}
                    aria-label="Email address"
                    aria-required="true"
                    aria-invalid={!!errors.email}
                    aria-describedby={errors.email ? 'email-error' : undefined}
                  />
                  {errors.email && (
                    <p id="email-error" className="mt-1 text-xs text-red-400">
                      {errors.email.message}
                    </p>
                  )}
                </div>
              )}
            />

            {/* Password Field */}
            <Controller
              name="password"
              control={control}
              render={({ field }) => (
                <div className="mb-4">
                  <label htmlFor="password" className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <Input
                      {...field}
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="current-password"
                      className={errors.password ? 'border-red-500 focus:ring-red-500 pr-10' : 'pr-10'}
                      aria-required="true"
                      aria-invalid={!!errors.password}
                      aria-describedby={errors.password ? 'password-error' : undefined}
                    />
                    <button
                      type="button"
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-[var(--text-low)] hover:text-[var(--text-high)] transition-colors"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      onClick={handleClickShowPassword}
                      onMouseDown={handleMouseDownPassword}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {errors.password && (
                    <p id="password-error" className="mt-1 text-xs text-red-400">
                      {errors.password.message}
                    </p>
                  )}
                </div>
              )}
            />

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between mb-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="h-4 w-4 rounded border-[var(--border)] bg-[var(--bg-elevated)] text-[var(--accent)] focus:ring-[var(--accent)]"
                  aria-label="Remember me"
                />
                <span className="text-sm text-[var(--text-mid)]">Remember me</span>
              </label>
              <Link
                href="/forgot-password"
                className="text-sm text-[var(--accent)] hover:underline"
              >
                Forgot Password?
              </Link>
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full mb-6"
              size="lg"
              disabled={isSubmitting || loginMutation.isPending}
              aria-label="Sign in to your account"
            >
              {isSubmitting || loginMutation.isPending ? 'Signing in...' : 'Sign In'}
            </Button>

            {/* Register Link */}
            <div className="text-center">
              <p className="text-sm text-[var(--text-mid)]">
                Don&apos;t have an account?{' '}
                <Link
                  href="/register"
                  className="font-semibold text-[var(--accent)] hover:underline"
                >
                  Create an account
                </Link>
              </p>
            </div>
          </form>

          {/* Quick Login (DEV only) - Grade S++ */}
          {process.env.NODE_ENV === 'development' && (
            <div className="mt-8 pt-6 border-t border-[var(--border)]">
              <p className="mb-4 font-semibold text-sm text-amber-400 flex items-center gap-2">
                🚀 Quick Login (DEV)
              </p>

              <Button
                className="w-full"
                variant="outline"
                size="md"
                onClick={() => quickLogin('admin@saas-ia.com', 'admin123')}
                disabled={isSubmitting || loginMutation.isPending}
                aria-label="Quick login as admin"
              >
                {loginMutation.isPending ? 'Logging in...' : '👑 Admin'}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
