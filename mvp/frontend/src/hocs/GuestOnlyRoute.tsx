'use client'

// React Imports
import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

// Hook Imports
import { useAuth } from '@/features/auth/hooks/useAuth'

// Component Imports
import { CircularProgress, Box } from '@mui/material'

type Props = {
  children: React.ReactNode
}

/**
 * GuestOnlyRoute Component
 * 
 * Protège les routes qui ne doivent être accessibles QUE par les utilisateurs NON authentifiés.
 * (Ex: /login, /register)
 * 
 * Redirige vers /dashboard si l'utilisateur est déjà authentifié.
 * 
 * Utilise le store Zustand (JWT backend) au lieu de NextAuth.
 */
const GuestOnlyRoute = ({ children }: Props) => {
  // Hooks
  const router = useRouter()
  const searchParams = useSearchParams()
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    // Si pas en cours de chargement et authentifié
    if (!isLoading && isAuthenticated) {
      // Récupérer redirect param ou rediriger vers dashboard par défaut
      const redirectUrl = searchParams?.get('redirect') || '/dashboard'
      router.replace(redirectUrl)
    }
  }, [isAuthenticated, isLoading, router, searchParams])

  // Afficher loader pendant vérification auth
  if (isLoading) {
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

  // Si authentifié, afficher loader (redirect en cours)
  if (isAuthenticated) {
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

  // Utilisateur NON authentifié → afficher contenu (login, register)
  return <>{children}</>
}

export default GuestOnlyRoute

