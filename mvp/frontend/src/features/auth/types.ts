/**
 * Auth Types - Grade S++
 * Type definitions for authentication
 */

/* ========================================================================
   USER
   ======================================================================== */

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: 'admin' | 'user';
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
}

/* ========================================================================
   PROFILE
   ======================================================================== */

export interface UpdateProfileRequest {
  full_name: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

/* ========================================================================
   REQUESTS
   ======================================================================== */

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

/* ========================================================================
   RESPONSES
   ======================================================================== */

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

/* ========================================================================
   FORM DATA
   ======================================================================== */

export interface LoginFormData {
  email: string;
  password: string;
}

export interface RegisterFormData {
  email: string;
  password: string;
  confirmPassword: string;
}

