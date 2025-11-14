/**
 * Core Types - Grade S++
 * Type definitions for the application
 */

/* ========================================================================
   THEME TYPES
   ======================================================================== */

export type Mode = 'light' | 'dark' | 'system';
export type Skin = 'default' | 'bordered';
export type Layout = 'vertical' | 'horizontal' | 'collapsed';
export type LayoutComponentPosition = 'fixed' | 'static';
export type LayoutComponentWidth = 'compact' | 'wide';

/* ========================================================================
   SETTINGS TYPES
   ======================================================================== */

export interface Settings {
  mode: Mode;
  skin: Skin;
  semiDark: boolean;
  layout: Layout;
  navbarContentWidth: LayoutComponentWidth;
  contentWidth: LayoutComponentWidth;
  footerContentWidth: LayoutComponentWidth;
}

/* ========================================================================
   NAVIGATION TYPES
   ======================================================================== */

export interface NavLink {
  title: string;
  path: string;
  icon?: string;
  badgeContent?: string;
  badgeColor?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
}

export interface NavGroup {
  title: string;
  icon?: string;
  children: NavLink[];
}

export type NavItem = NavLink | NavGroup;

/* ========================================================================
   USER TYPES
   ======================================================================== */

export interface User {
  id: number;
  email: string;
  role: 'admin' | 'user';
  is_active: boolean;
}

/* ========================================================================
   API TYPES
   ======================================================================== */

export interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown;
}

