/**
 * Guest Guard - REFONTE COMPLÈTE
 * Protection des routes pour invités uniquement (login/register) - Version simplifiée
 */

'use client';

import { useEffect, type ReactNode } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CircularProgress, Box } from '@mui/material';

import { useAuth } from '@/contexts/AuthContext';

/* ========================================================================
   COMPONENT
   ======================================================================== */

interface GuestGuardProps {
  children: ReactNode;
}

export function GuestGuard({ children }: GuestGuardProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Attendre la fin du chargement
    if (isLoading) return;

    // Si déjà authentifié, rediriger vers dashboard ou redirect param
    if (isAuthenticated) {
      const redirectUrl = searchParams?.get('redirect') || '/dashboard';
      router.replace(redirectUrl);
    }
  }, [isAuthenticated, isLoading, router, searchParams]);

  // Afficher loader pendant chargement ou redirection
  if (isLoading || isAuthenticated) {
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

  // Utilisateur NON authentifié → afficher contenu (login/register)
  return <>{children}</>;
}

/* ========================================================================
   EXPORTS
   ======================================================================== */

export default GuestGuard;

