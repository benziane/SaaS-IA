/**
 * Login Page - Grade S++
 * User authentication page
 */

'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import {
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControl,
  FormControlLabel,
  FormHelperText,
  IconButton,
  InputAdornment,
  InputLabel,
  Link as MuiLink,
  OutlinedInput,
  TextField,
  Typography,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import Link from 'next/link';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';

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
    } catch (error) {
      // Error is already handled by useLogin hook (toast)
      // Just prevent the error from propagating
      console.error('Quick Login failed:', error);
    }
  };
  
  /* ========================================================================
     RENDER
     ======================================================================== */
  
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'background.default',
        padding: 2,
      }}
    >
      {/* Skip to main content - Accessibility S++ */}
      <a href="#main-content" className="skip-to-main">
        Skip to main content
      </a>
      
      <Card
        id="main-content"
        sx={{
          maxWidth: 450,
          width: '100%',
        }}
        role="main"
        aria-labelledby="login-title"
      >
        <CardContent sx={{ p: 4 }}>
          {/* Header */}
          <Box sx={{ mb: 4, textAlign: 'center' }}>
            <Typography
              id="login-title"
              variant="h4"
              component="h1"
              gutterBottom
              sx={{ fontWeight: 600 }}
            >
              Welcome to SaaS-IA 👋
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Please sign in to your account
            </Typography>
          </Box>
          
          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} noValidate>
            {/* Email Field */}
            <Controller
              name="email"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Email"
                  type="email"
                  autoComplete="email"
                  error={!!errors.email}
                  helperText={errors.email?.message}
                  sx={{ mb: 3 }}
                  inputProps={{
                    'aria-label': 'Email address',
                    'aria-required': 'true',
                    'aria-invalid': !!errors.email,
                    'aria-describedby': errors.email ? 'email-error' : undefined,
                  }}
                />
              )}
            />
            
            {/* Password Field */}
            <Controller
              name="password"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.password} sx={{ mb: 2 }}>
                  <InputLabel htmlFor="password">Password</InputLabel>
                  <OutlinedInput
                    {...field}
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    endAdornment={
                      <InputAdornment position="end">
                        <IconButton
                          aria-label={showPassword ? 'Hide password' : 'Show password'}
                          onClick={handleClickShowPassword}
                          onMouseDown={handleMouseDownPassword}
                          edge="end"
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    }
                    label="Password"
                    inputProps={{
                      'aria-required': 'true',
                      'aria-invalid': !!errors.password,
                      'aria-describedby': errors.password ? 'password-error' : undefined,
                    }}
                  />
                  {errors.password && (
                    <FormHelperText id="password-error">{errors.password.message}</FormHelperText>
                  )}
                </FormControl>
              )}
            />
            
            {/* Remember Me & Forgot Password */}
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                mb: 3,
              }}
            >
              <FormControlLabel
                control={
                  <Checkbox
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    inputProps={{
                      'aria-label': 'Remember me',
                    }}
                  />
                }
                label="Remember me"
              />
              <MuiLink
                component={Link}
                href="/forgot-password"
                underline="hover"
                sx={{ fontSize: '0.875rem' }}
              >
                Forgot Password?
              </MuiLink>
            </Box>
            
            {/* Submit Button */}
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={isSubmitting || loginMutation.isPending}
              sx={{ mb: 3 }}
              aria-label="Sign in to your account"
            >
              {isSubmitting || loginMutation.isPending ? 'Signing in...' : 'Sign In'}
            </Button>
            
            {/* Register Link */}
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Don&apos;t have an account?{' '}
                <MuiLink
                  component={Link}
                  href="/register"
                  underline="hover"
                  sx={{ fontWeight: 600 }}
                >
                  Create an account
                </MuiLink>
              </Typography>
            </Box>
          </form>
          
          {/* Quick Login (DEV only) - Grade S++ */}
          {process.env.NODE_ENV === 'development' && (
            <Box
              sx={{
                mt: 4,
                pt: 3,
                borderTop: 1,
                borderColor: 'divider',
              }}
            >
              <Typography
                variant="body2"
                sx={{
                  mb: 2,
                  fontWeight: 600,
                  color: 'warning.main',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                🚀 Quick Login (DEV)
              </Typography>
              
              <Button
                fullWidth
                variant="outlined"
                color="error"
                size="medium"
                onClick={() => quickLogin('admin@saas-ia.com', 'admin123')}
                disabled={isSubmitting || loginMutation.isPending}
                sx={{
                  borderWidth: 2,
                  '&:hover': {
                    borderWidth: 2,
                  },
                }}
                aria-label="Quick login as admin"
              >
                {loginMutation.isPending ? 'Logging in...' : '👑 Admin'}
              </Button>
              
              {/* Help message */}
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

