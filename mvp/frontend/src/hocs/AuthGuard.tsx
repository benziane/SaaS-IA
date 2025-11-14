'use client'

// React Imports
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

// Store Imports
import { useAuthStore } from '@/lib/store'
import { useAuthInit } from '@/lib/useAuthInit'

// Component Imports
import { CircularProgress, Box } from '@mui/material'

type Props = {
  children: React.ReactNode
}

/**
 * AuthGuard Component
 * 
 * Protège les routes qui nécessitent une authentification.
 * Redirige vers /login si l'utilisateur n'est pas authentifié.
 * 
 * Utilise le store Zustand (JWT backend) au lieu de NextAuth.
 */
const AuthGuard = ({ children }: Props) => {
  // Hooks
  const router = useRouter()
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)
  const isLoading = useAuthStore(state => state.isLoading)
  const isInitialized = useAuthInit() // Initialiser l'auth au démarrage

  console.log('[AuthGuard] State:', { isInitialized, isAuthenticated, isLoading });

  useEffect(() => {
    console.log('[AuthGuard] useEffect triggered', { isInitialized, isAuthenticated, isLoading });
    
    // Attendre que l'initialisation soit terminée
    if (!isInitialized) {
      console.log('[AuthGuard] Waiting for initialization...');
      return;
    }

    // Si pas en cours de chargement et pas authentifié
    if (!isLoading && !isAuthenticated) {
      // Rediriger vers login avec redirect param
      const currentPath = window.location.pathname;
      console.log('[AuthGuard] Not authenticated, redirecting to login from:', currentPath);
      router.replace(`/login?redirect=${encodeURIComponent(currentPath)}`);
    } else {
      console.log('[AuthGuard] User is authenticated or loading');
    }
  }, [isInitialized, isAuthenticated, isLoading, router])

  // Afficher loader pendant initialisation ou vérification auth
  if (!isInitialized || isLoading || !isAuthenticated) {
    console.log('[AuthGuard] Showing loader:', { isInitialized, isLoading, isAuthenticated });
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh'
        }}
      >
        <CircularProgress />
      </Box>
    )
  }

  console.log('[AuthGuard] Rendering children');
  // Utilisateur authentifié → afficher contenu
  return <>{children}</>
}

export default AuthGuard

