'use client'

// React Imports
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

// Store Imports
import { useAuthStore } from '@/lib/store'

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

  useEffect(() => {
    // Si pas en cours de chargement et pas authentifié
    if (!isLoading && !isAuthenticated) {
      // Rediriger vers login avec redirect param
      const currentPath = window.location.pathname
      router.replace(`/login?redirect=${encodeURIComponent(currentPath)}`)
    }
  }, [isAuthenticated, isLoading, router])

  // Afficher loader pendant vérification auth
  if (isLoading || !isAuthenticated) {
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

  // Utilisateur authentifié → afficher contenu
  return <>{children}</>
}

export default AuthGuard

