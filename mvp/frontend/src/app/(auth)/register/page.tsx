/**
 * Register Page - Grade S++
 * User registration page
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
import { useRegister } from '@/features/auth/hooks';
import { registerSchema, type RegisterSchema } from '@/features/auth/schemas';

/* ========================================================================
   COMPONENT
   ======================================================================== */

export default function RegisterPage(): JSX.Element {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [acceptTerms, setAcceptTerms] = useState(false);

  const registerMutation = useRegister();

  /* Form */
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterSchema>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
    },
    mode: 'onBlur',
  });

  /* Handlers */
  const onSubmit = async (data: RegisterSchema): Promise<void> => {
    if (!acceptTerms) {
      return;
    }

    await registerMutation.mutateAsync({
      email: data.email,
      password: data.password,
    });
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
        aria-labelledby="register-title"
      >
        <CardContent className="p-8">
          {/* Header */}
          <div className="mb-8 text-center">
            <h1
              id="register-title"
              className="text-2xl font-semibold text-[var(--text-high)] mb-2"
            >
              Create Account 🚀
            </h1>
            <p className="text-sm text-[var(--text-mid)]">
              Start your AI journey today
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
                  />
                  {errors.email && (
                    <p className="mt-1 text-xs text-red-400">
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
                <div className="mb-6">
                  <label htmlFor="password" className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <Input
                      {...field}
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="new-password"
                      className={errors.password ? 'border-red-500 focus:ring-red-500 pr-10' : 'pr-10'}
                      aria-required="true"
                      aria-invalid={!!errors.password}
                    />
                    <button
                      type="button"
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-[var(--text-low)] hover:text-[var(--text-high)] transition-colors"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {errors.password && (
                    <p className="mt-1 text-xs text-red-400">
                      {errors.password.message}
                    </p>
                  )}
                </div>
              )}
            />

            {/* Confirm Password Field */}
            <Controller
              name="confirmPassword"
              control={control}
              render={({ field }) => (
                <div className="mb-4">
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-[var(--text-mid)] mb-1.5">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <Input
                      {...field}
                      id="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      autoComplete="new-password"
                      className={errors.confirmPassword ? 'border-red-500 focus:ring-red-500 pr-10' : 'pr-10'}
                      aria-required="true"
                      aria-invalid={!!errors.confirmPassword}
                    />
                    <button
                      type="button"
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-[var(--text-low)] hover:text-[var(--text-high)] transition-colors"
                      aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {errors.confirmPassword && (
                    <p className="mt-1 text-xs text-red-400">
                      {errors.confirmPassword.message}
                    </p>
                  )}
                </div>
              )}
            />

            {/* Terms & Conditions */}
            <label className="flex items-start gap-2 cursor-pointer mb-6">
              <input
                type="checkbox"
                checked={acceptTerms}
                onChange={(e) => setAcceptTerms(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-[var(--border)] bg-[var(--bg-elevated)] text-[var(--accent)] focus:ring-[var(--accent)]"
                aria-label="Accept terms and conditions"
                aria-required="true"
              />
              <span className="text-sm text-[var(--text-mid)]">
                I agree to the{' '}
                <a href="/terms" className="text-[var(--accent)] hover:underline">
                  Terms & Conditions
                </a>
              </span>
            </label>

            {/* Submit Button */}
            <Button
              type="submit"
              className="w-full mb-6"
              size="lg"
              disabled={!acceptTerms || isSubmitting || registerMutation.isPending}
              aria-label="Create your account"
            >
              {isSubmitting || registerMutation.isPending ? 'Creating account...' : 'Sign Up'}
            </Button>

            {/* Login Link */}
            <div className="text-center">
              <p className="text-sm text-[var(--text-mid)]">
                Already have an account?{' '}
                <Link
                  href="/login"
                  className="font-semibold text-[var(--accent)] hover:underline"
                >
                  Sign in instead
                </Link>
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
