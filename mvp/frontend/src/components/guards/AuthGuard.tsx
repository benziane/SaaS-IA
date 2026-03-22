/**
 * Auth Guard - REFONTE COMPLÈTE
 * Protection des routes authentifiées - Version simplifiée et rapide
 */

'use client';

import { useEffect, type ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';

import { useAuth } from '@/contexts/AuthContext';

/* ========================================================================
   COMPONENT
   ======================================================================== */

interface AuthGuardProps {
  children: ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    console.log('[AuthGuard] State:', { isAuthenticated, isLoading, pathname });
    
    // Attendre la fin du chargement
    if (isLoading) {
      console.log('[AuthGuard] Still loading, waiting...');
      return;
    }
    
    // Si pas authentifié, rediriger vers login
    if (!isAuthenticated) {
      console.log('[AuthGuard] Not authenticated, redirecting to login');
      const redirectUrl = `/login?redirect=${encodeURIComponent(pathname)}`;
      router.replace(redirectUrl);
    } else {
      console.log('[AuthGuard] Authenticated, showing content');
    }
  }, [isAuthenticated, isLoading, router, pathname]);

  // Afficher le contenu immédiatement (pas de loader)
  // La redirection se fera en arrière-plan si non authentifié
  return <>{children}</>;
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default AuthGuard;

