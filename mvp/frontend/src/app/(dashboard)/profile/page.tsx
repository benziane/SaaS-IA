/**
 * Profile Page
 * User profile settings: view info, edit name, change password
 */

'use client';

import { useState } from 'react';

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  IconButton,
  InputAdornment,
  TextField,
  Typography,
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { useQueryClient } from '@tanstack/react-query';

import { useCurrentUser } from '@/features/auth/hooks';
import { authApi } from '@/features/auth/api';
import { extractErrorMessage } from '@/lib/apiClient';
import { queryKeys } from '@/lib/queryClient';

/* ========================================================================
   SCHEMAS
   ======================================================================== */

const profileSchema = z.object({
  full_name: z
    .string()
    .min(1, 'Full name is required')
    .max(255, 'Full name must be 255 characters or fewer'),
});

type ProfileFormData = z.infer<typeof profileSchema>;

const passwordSchema = z
  .object({
    current_password: z
      .string()
      .min(1, 'Current password is required'),
    new_password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Must contain at least one number'),
    confirm_password: z
      .string()
      .min(1, 'Please confirm your new password'),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  });

type PasswordFormData = z.infer<typeof passwordSchema>;

/* ========================================================================
   PAGE COMPONENT
   ======================================================================== */

export default function ProfilePage(): JSX.Element {
  const { data: user, isLoading: userLoading } = useCurrentUser();
  const queryClient = useQueryClient();

  const [profileSubmitting, setProfileSubmitting] = useState(false);
  const [passwordSubmitting, setPasswordSubmitting] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  /* ------------------------------------------------------------------
     Profile Form
     ------------------------------------------------------------------ */

  const profileForm = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
    values: {
      full_name: user?.full_name ?? '',
    },
  });

  const handleProfileSubmit = async (data: ProfileFormData) => {
    setProfileSubmitting(true);
    try {
      await authApi.updateProfile({ full_name: data.full_name });
      await queryClient.invalidateQueries({ queryKey: queryKeys.auth.me() });

      // Update localStorage cache if present
      if (typeof window !== 'undefined') {
        const storedUser = localStorage.getItem('auth_user');
        if (storedUser) {
          try {
            const parsed = JSON.parse(storedUser);
            parsed.full_name = data.full_name;
            localStorage.setItem('auth_user', JSON.stringify(parsed));
          } catch {
            // Ignore parse errors
          }
        }
      }

      toast.success('Profile updated', {
        description: 'Your profile has been updated successfully.',
      });
    } catch (error) {
      toast.error('Failed to update profile', {
        description: extractErrorMessage(error),
      });
    } finally {
      setProfileSubmitting(false);
    }
  };

  /* ------------------------------------------------------------------
     Password Form
     ------------------------------------------------------------------ */

  const passwordForm = useForm<PasswordFormData>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
  });

  const handlePasswordSubmit = async (data: PasswordFormData) => {
    setPasswordSubmitting(true);
    try {
      await authApi.changePassword({
        current_password: data.current_password,
        new_password: data.new_password,
      });
      passwordForm.reset();
      toast.success('Password changed', {
        description: 'Your password has been changed successfully.',
      });
    } catch (error) {
      toast.error('Failed to change password', {
        description: extractErrorMessage(error),
      });
    } finally {
      setPasswordSubmitting(false);
    }
  };

  /* ------------------------------------------------------------------
     Loading State
     ------------------------------------------------------------------ */

  if (userLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  /* ------------------------------------------------------------------
     Render
     ------------------------------------------------------------------ */

  const memberSince = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : 'N/A';

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600 }}>
          Profile Settings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your account information and security settings.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* ============================================================
            User Info Card
            ============================================================ */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardHeader title="Account Information" />
            <Divider />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    Email
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {user?.email ?? 'N/A'}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    Full Name
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {user?.full_name || 'Not set'}
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    Role
                  </Typography>
                  <Chip
                    label={user?.role === 'admin' ? 'Administrator' : 'User'}
                    color={user?.role === 'admin' ? 'primary' : 'default'}
                    size="small"
                    variant="outlined"
                  />
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    Status
                  </Typography>
                  <Chip
                    label={user?.is_active ? 'Active' : 'Inactive'}
                    color={user?.is_active ? 'success' : 'error'}
                    size="small"
                  />
                </Box>

                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    Member Since
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {memberSince}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* ============================================================
            Edit Profile + Change Password
            ============================================================ */}
        <Grid item xs={12} md={8}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Edit Profile Card */}
            <Card>
              <CardHeader title="Edit Profile" />
              <Divider />
              <CardContent>
                <Box
                  component="form"
                  onSubmit={profileForm.handleSubmit(handleProfileSubmit)}
                  noValidate
                >
                  <Controller
                    name="full_name"
                    control={profileForm.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        label="Full Name"
                        fullWidth
                        error={!!fieldState.error}
                        helperText={fieldState.error?.message}
                        disabled={profileSubmitting}
                        sx={{ mb: 3 }}
                      />
                    )}
                  />

                  <Alert severity="info" variant="outlined" sx={{ mb: 3 }}>
                    Your email address cannot be changed. Contact support if you need to update it.
                  </Alert>

                  <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={profileSubmitting || !profileForm.formState.isDirty}
                      startIcon={profileSubmitting ? <CircularProgress size={16} /> : undefined}
                    >
                      {profileSubmitting ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </Box>
                </Box>
              </CardContent>
            </Card>

            {/* Change Password Card */}
            <Card>
              <CardHeader title="Change Password" />
              <Divider />
              <CardContent>
                <Box
                  component="form"
                  onSubmit={passwordForm.handleSubmit(handlePasswordSubmit)}
                  noValidate
                >
                  <Controller
                    name="current_password"
                    control={passwordForm.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        label="Current Password"
                        type={showCurrentPassword ? 'text' : 'password'}
                        fullWidth
                        error={!!fieldState.error}
                        helperText={fieldState.error?.message}
                        disabled={passwordSubmitting}
                        sx={{ mb: 3 }}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowCurrentPassword((prev) => !prev)}
                                edge="end"
                                size="small"
                                aria-label={showCurrentPassword ? 'Hide password' : 'Show password'}
                              >
                                {showCurrentPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                              </IconButton>
                            </InputAdornment>
                          ),
                        }}
                      />
                    )}
                  />

                  <Controller
                    name="new_password"
                    control={passwordForm.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        label="New Password"
                        type={showNewPassword ? 'text' : 'password'}
                        fullWidth
                        error={!!fieldState.error}
                        helperText={fieldState.error?.message || 'Minimum 8 characters with uppercase, lowercase, and a number'}
                        disabled={passwordSubmitting}
                        sx={{ mb: 3 }}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowNewPassword((prev) => !prev)}
                                edge="end"
                                size="small"
                                aria-label={showNewPassword ? 'Hide password' : 'Show password'}
                              >
                                {showNewPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                              </IconButton>
                            </InputAdornment>
                          ),
                        }}
                      />
                    )}
                  />

                  <Controller
                    name="confirm_password"
                    control={passwordForm.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        {...field}
                        label="Confirm New Password"
                        type={showConfirmPassword ? 'text' : 'password'}
                        fullWidth
                        error={!!fieldState.error}
                        helperText={fieldState.error?.message}
                        disabled={passwordSubmitting}
                        sx={{ mb: 3 }}
                        InputProps={{
                          endAdornment: (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => setShowConfirmPassword((prev) => !prev)}
                                edge="end"
                                size="small"
                                aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                              >
                                {showConfirmPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                              </IconButton>
                            </InputAdornment>
                          ),
                        }}
                      />
                    )}
                  />

                  <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      type="submit"
                      variant="contained"
                      color="warning"
                      disabled={passwordSubmitting}
                      startIcon={passwordSubmitting ? <CircularProgress size={16} /> : undefined}
                    >
                      {passwordSubmitting ? 'Changing...' : 'Change Password'}
                    </Button>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
