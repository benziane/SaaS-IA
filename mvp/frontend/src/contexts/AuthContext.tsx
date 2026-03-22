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
  // État initial TOUJOURS null pour éviter erreur d'hydration
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();
  
  // Initialisation côté client uniquement (après hydration)
  useEffect(() => {
    console.log('[AuthContext] Initializing...');
    setMounted(true);
    
    try {
      // 1. Essayer localStorage d'abord
      const storedToken = localStorage.getItem('auth_token');
      const storedUser = localStorage.getItem('auth_user');
      
      console.log('[AuthContext] localStorage:', { 
        hasToken: !!storedToken, 
        hasUser: !!storedUser 
      });
      
      if (storedToken && storedUser) {
        console.log('[AuthContext] Found token + user in localStorage');
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        setIsLoading(false);
        return;
      }
      
      // 2. Sinon essayer cookie
      const cookies = document.cookie.split(';');
      for (const cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'auth_token') {
          console.log('[AuthContext] Found token in cookie, fetching user...');
          setToken(value);
          // Fetch user avec ce token
          fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8004'}/api/auth/me`, {
            headers: { Authorization: `Bearer ${value}` }
          })
            .then(res => res.ok ? res.json() : null)
            .then(userData => {
              if (userData) {
                console.log('[AuthContext] User fetched:', userData.email);
                setUser(userData);
                localStorage.setItem('auth_user', JSON.stringify(userData));
              }
            })
            .catch((err) => {
              console.error('[AuthContext] Fetch user error:', err);
            })
            .finally(() => {
              console.log('[AuthContext] Init complete (from cookie)');
              setIsLoading(false);
            });
          return;
        }
      }
      
      // Pas de token trouvé
      console.log('[AuthContext] No token found, user not authenticated');
      setIsLoading(false);
    } catch (error) {
      console.error('[AuthContext] Init error:', error);
      setIsLoading(false);
    }
  }, []);

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

