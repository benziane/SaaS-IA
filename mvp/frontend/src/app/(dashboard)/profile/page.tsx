/**
 * Profile Page
 * User profile settings: view info, edit name, change password
 */

'use client';

import { useState } from 'react';
import { Eye, EyeOff, Loader2 } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/lib/design-hub/components/Alert';
import { Button } from '@/lib/design-hub/components/Button';
import { Input } from '@/lib/design-hub/components/Input';
import { Separator } from '@/lib/design-hub/components/Separator';

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
      <div className="flex justify-center items-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-[var(--accent)]" />
      </div>
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
    <div>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--text-high)] mb-1">
          Profile Settings
        </h1>
        <p className="text-[var(--text-mid)]">
          Manage your account information and security settings.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* ============================================================
            User Info Card
            ============================================================ */}
        <div className="md:col-span-4">
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Account Information</CardTitle>
            </CardHeader>
            <Separator />
            <CardContent className="pt-6">
              <div className="flex flex-col gap-5">
                <div>
                  <span className="text-xs text-[var(--text-low)] block mb-1">
                    Email
                  </span>
                  <p className="text-sm font-medium text-[var(--text-high)]">
                    {user?.email ?? 'N/A'}
                  </p>
                </div>

                <div>
                  <span className="text-xs text-[var(--text-low)] block mb-1">
                    Full Name
                  </span>
                  <p className="text-sm font-medium text-[var(--text-high)]">
                    {user?.full_name || 'Not set'}
                  </p>
                </div>

                <div>
                  <span className="text-xs text-[var(--text-low)] block mb-1">
                    Role
                  </span>
                  <Badge variant={user?.role === 'admin' ? 'default' : 'outline'}>
                    {user?.role === 'admin' ? 'Administrator' : 'User'}
                  </Badge>
                </div>

                <div>
                  <span className="text-xs text-[var(--text-low)] block mb-1">
                    Status
                  </span>
                  <Badge variant={user?.is_active ? 'success' : 'destructive'}>
                    {user?.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>

                <div>
                  <span className="text-xs text-[var(--text-low)] block mb-1">
                    Member Since
                  </span>
                  <p className="text-sm font-medium text-[var(--text-high)]">
                    {memberSince}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ============================================================
            Edit Profile + Change Password
            ============================================================ */}
        <div className="md:col-span-8">
          <div className="flex flex-col gap-6">
            {/* Edit Profile Card */}
            <Card>
              <CardHeader>
                <CardTitle>Edit Profile</CardTitle>
              </CardHeader>
              <Separator />
              <CardContent className="pt-6">
                <form
                  onSubmit={profileForm.handleSubmit(handleProfileSubmit)}
                  noValidate
                >
                  <Controller
                    name="full_name"
                    control={profileForm.control}
                    render={({ field, fieldState }) => (
                      <div className="mb-6">
                        <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Full Name</label>
                        <Input
                          {...field}
                          className={fieldState.error ? 'border-red-500' : ''}
                          disabled={profileSubmitting}
                        />
                        {fieldState.error && (
                          <p className="text-xs text-red-400 mt-1">{fieldState.error.message}</p>
                        )}
                      </div>
                    )}
                  />

                  <Alert variant="info" className="mb-6">
                    <AlertDescription>
                      Your email address cannot be changed. Contact support if you need to update it.
                    </AlertDescription>
                  </Alert>

                  <div className="flex justify-end">
                    <Button
                      type="submit"
                      disabled={profileSubmitting || !profileForm.formState.isDirty}
                    >
                      {profileSubmitting && <Loader2 className="h-4 w-4 animate-spin mr-1" />}
                      {profileSubmitting ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            {/* Change Password Card */}
            <Card>
              <CardHeader>
                <CardTitle>Change Password</CardTitle>
              </CardHeader>
              <Separator />
              <CardContent className="pt-6">
                <form
                  onSubmit={passwordForm.handleSubmit(handlePasswordSubmit)}
                  noValidate
                >
                  <Controller
                    name="current_password"
                    control={passwordForm.control}
                    render={({ field, fieldState }) => (
                      <div className="mb-6">
                        <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Current Password</label>
                        <div className="relative">
                          <Input
                            {...field}
                            type={showCurrentPassword ? 'text' : 'password'}
                            className={fieldState.error ? 'border-red-500 pr-10' : 'pr-10'}
                            disabled={passwordSubmitting}
                          />
                          <button
                            type="button"
                            onClick={() => setShowCurrentPassword((prev) => !prev)}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-[var(--text-low)] hover:text-[var(--text-high)]"
                            aria-label={showCurrentPassword ? 'Hide password' : 'Show password'}
                          >
                            {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        </div>
                        {fieldState.error && (
                          <p className="text-xs text-red-400 mt-1">{fieldState.error.message}</p>
                        )}
                      </div>
                    )}
                  />

                  <Controller
                    name="new_password"
                    control={passwordForm.control}
                    render={({ field, fieldState }) => (
                      <div className="mb-6">
                        <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">New Password</label>
                        <div className="relative">
                          <Input
                            {...field}
                            type={showNewPassword ? 'text' : 'password'}
                            className={fieldState.error ? 'border-red-500 pr-10' : 'pr-10'}
                            disabled={passwordSubmitting}
                          />
                          <button
                            type="button"
                            onClick={() => setShowNewPassword((prev) => !prev)}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-[var(--text-low)] hover:text-[var(--text-high)]"
                            aria-label={showNewPassword ? 'Hide password' : 'Show password'}
                          >
                            {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        </div>
                        <p className="text-xs text-[var(--text-low)] mt-1">
                          {fieldState.error?.message || 'Minimum 8 characters with uppercase, lowercase, and a number'}
                        </p>
                      </div>
                    )}
                  />

                  <Controller
                    name="confirm_password"
                    control={passwordForm.control}
                    render={({ field, fieldState }) => (
                      <div className="mb-6">
                        <label className="text-sm font-medium text-[var(--text-high)] mb-1.5 block">Confirm New Password</label>
                        <div className="relative">
                          <Input
                            {...field}
                            type={showConfirmPassword ? 'text' : 'password'}
                            className={fieldState.error ? 'border-red-500 pr-10' : 'pr-10'}
                            disabled={passwordSubmitting}
                          />
                          <button
                            type="button"
                            onClick={() => setShowConfirmPassword((prev) => !prev)}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-[var(--text-low)] hover:text-[var(--text-high)]"
                            aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                          >
                            {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        </div>
                        {fieldState.error && (
                          <p className="text-xs text-red-400 mt-1">{fieldState.error.message}</p>
                        )}
                      </div>
                    )}
                  />

                  <div className="flex justify-end">
                    <Button
                      type="submit"
                      className="bg-amber-600 hover:bg-amber-700 text-white"
                      disabled={passwordSubmitting}
                    >
                      {passwordSubmitting && <Loader2 className="h-4 w-4 animate-spin mr-1" />}
                      {passwordSubmitting ? 'Changing...' : 'Change Password'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
