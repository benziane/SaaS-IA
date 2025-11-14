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
  role: 'admin' | 'user';
  is_active: boolean;
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
  token_type: string;
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

