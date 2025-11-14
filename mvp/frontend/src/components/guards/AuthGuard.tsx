/**
 * Auth Guard - REFONTE COMPLÈTE
 * Protection des routes authentifiées - Version simplifiée et rapide
 */

'use client';

import { useEffect, type ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { CircularProgress, Box } from '@mui/material';

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
    // Attendre la fin du chargement
    if (isLoading) return;

    // Si pas authentifié, rediriger vers login
    if (!isAuthenticated) {
      const redirectUrl = `/login?redirect=${encodeURIComponent(pathname)}`;
      router.replace(redirectUrl);
    }
  }, [isAuthenticated, isLoading, router, pathname]);

  // Afficher loader pendant chargement ou redirection
  if (isLoading || !isAuthenticated) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Utilisateur authentifié → afficher contenu
  return <>{children}</>;
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default AuthGuard;

