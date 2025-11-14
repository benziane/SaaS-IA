/**
 * Register Page - Grade S++
 * User registration page
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
        aria-labelledby="register-title"
      >
        <CardContent sx={{ p: 4 }}>
          {/* Header */}
          <Box sx={{ mb: 4, textAlign: 'center' }}>
            <Typography
              id="register-title"
              variant="h4"
              component="h1"
              gutterBottom
              sx={{ fontWeight: 600 }}
            >
              Create Account 🚀
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Start your AI journey today
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
                  }}
                />
              )}
            />
            
            {/* Password Field */}
            <Controller
              name="password"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.password} sx={{ mb: 3 }}>
                  <InputLabel htmlFor="password">Password</InputLabel>
                  <OutlinedInput
                    {...field}
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    endAdornment={
                      <InputAdornment position="end">
                        <IconButton
                          aria-label={showPassword ? 'Hide password' : 'Show password'}
                          onClick={() => setShowPassword(!showPassword)}
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
                    }}
                  />
                  {errors.password && (
                    <FormHelperText>{errors.password.message}</FormHelperText>
                  )}
                </FormControl>
              )}
            />
            
            {/* Confirm Password Field */}
            <Controller
              name="confirmPassword"
              control={control}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.confirmPassword} sx={{ mb: 2 }}>
                  <InputLabel htmlFor="confirmPassword">Confirm Password</InputLabel>
                  <OutlinedInput
                    {...field}
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    autoComplete="new-password"
                    endAdornment={
                      <InputAdornment position="end">
                        <IconButton
                          aria-label={
                            showConfirmPassword ? 'Hide password' : 'Show password'
                          }
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          edge="end"
                        >
                          {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    }
                    label="Confirm Password"
                    inputProps={{
                      'aria-required': 'true',
                      'aria-invalid': !!errors.confirmPassword,
                    }}
                  />
                  {errors.confirmPassword && (
                    <FormHelperText>{errors.confirmPassword.message}</FormHelperText>
                  )}
                </FormControl>
              )}
            />
            
            {/* Terms & Conditions */}
            <FormControlLabel
              control={
                <Checkbox
                  checked={acceptTerms}
                  onChange={(e) => setAcceptTerms(e.target.checked)}
                  inputProps={{
                    'aria-label': 'Accept terms and conditions',
                    'aria-required': 'true',
                  }}
                />
              }
              label={
                <Typography variant="body2">
                  I agree to the{' '}
                  <MuiLink href="/terms" underline="hover">
                    Terms & Conditions
                  </MuiLink>
                </Typography>
              }
              sx={{ mb: 3 }}
            />
            
            {/* Submit Button */}
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={!acceptTerms || isSubmitting || registerMutation.isPending}
              sx={{ mb: 3 }}
              aria-label="Create your account"
            >
              {isSubmitting || registerMutation.isPending ? 'Creating account...' : 'Sign Up'}
            </Button>
            
            {/* Login Link */}
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Already have an account?{' '}
                <MuiLink
                  component={Link}
                  href="/login"
                  underline="hover"
                  sx={{ fontWeight: 600 }}
                >
                  Sign in instead
                </MuiLink>
              </Typography>
            </Box>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}

