/**
 * Auth Schemas - Grade S++
 * Zod validation schemas for authentication
 */

import { z } from 'zod';

/* ========================================================================
   VALIDATION RULES
   ======================================================================== */

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PASSWORD_MIN_LENGTH = 8;

/* ========================================================================
   LOGIN SCHEMA
   ======================================================================== */

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Invalid email address')
    .regex(EMAIL_REGEX, 'Invalid email format')
    .toLowerCase()
    .trim(),
  
  password: z
    .string()
    .min(1, 'Password is required')
    .min(PASSWORD_MIN_LENGTH, `Password must be at least ${PASSWORD_MIN_LENGTH} characters`),
});

export type LoginSchema = z.infer<typeof loginSchema>;

/* ========================================================================
   REGISTER SCHEMA
   ======================================================================== */

export const registerSchema = z
  .object({
    email: z
      .string()
      .min(1, 'Email is required')
      .email('Invalid email address')
      .regex(EMAIL_REGEX, 'Invalid email format')
      .toLowerCase()
      .trim(),
    
    password: z
      .string()
      .min(1, 'Password is required')
      .min(PASSWORD_MIN_LENGTH, `Password must be at least ${PASSWORD_MIN_LENGTH} characters`)
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Password must contain at least one number'),
    
    confirmPassword: z
      .string()
      .min(1, 'Please confirm your password'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

export type RegisterSchema = z.infer<typeof registerSchema>;

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default {
  loginSchema,
  registerSchema,
};

