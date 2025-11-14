/**
 * Auth Context - REFONTE COMPLÈTE
 * Système d'authentification simplifié et performant
 */

'use client';

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

/* ========================================================================
   TYPES
   ======================================================================== */

export interface User {
  id: number;
  email: string;
  role: 'admin' | 'user';
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
}

/* ========================================================================
   CONTEXT
   ======================================================================== */

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/* ========================================================================
   PROVIDER
   ======================================================================== */

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  // Initialisation synchrone depuis localStorage
  const [user, setUser] = useState<User | null>(() => {
    if (typeof window === 'undefined') return null;
    try {
      const storedUser = localStorage.getItem('auth_user');
      return storedUser ? JSON.parse(storedUser) : null;
    } catch {
      return null;
    }
  });
  
  const [token, setToken] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null;
    try {
      return localStorage.getItem('auth_token');
    } catch {
      return null;
    }
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  // Login
  const login = useCallback((newUser: User, newToken: string) => {
    try {
      // Sauvegarder dans localStorage
      localStorage.setItem('auth_token', newToken);
      localStorage.setItem('auth_user', JSON.stringify(newUser));
      
      // Sauvegarder dans cookie pour middleware
      document.cookie = `auth_token=${newToken}; path=/; max-age=1800; SameSite=Lax`;
      
      // Mettre à jour state
      setToken(newToken);
      setUser(newUser);
      
      // Rediriger vers dashboard
      router.push('/dashboard');
    } catch (error) {
      console.error('[AuthContext] Login error:', error);
      toast.error('Login failed', {
        description: 'Could not save authentication data',
      });
    }
  }, [router]);

  // Logout
  const logout = useCallback(() => {
    try {
      // Nettoyer localStorage
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      
      // Nettoyer cookie
      document.cookie = 'auth_token=; path=/; max-age=0';
      
      // Réinitialiser state
      setToken(null);
      setUser(null);
      
      // Rediriger vers login
      router.push('/login');
    } catch (error) {
      console.error('[AuthContext] Logout error:', error);
    }
  }, [router]);

  const isAuthenticated = !!user && !!token;

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated,
    isLoading,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/* ========================================================================
   HOOK
   ======================================================================== */

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  
  return context;
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default AuthContext;

