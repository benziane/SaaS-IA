'use client'

// React Imports
import { useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

// Auth Context
import { useAuth } from '@/contexts/AuthContext'

// Component Imports
import { CircularProgress, Box } from '@mui/material'

type Props = {
  children: React.ReactNode
}

/**
 * GuestOnlyRoute Component
 *
 * Protects routes that should only be accessible by NON-authenticated users.
 * (e.g., /login, /register)
 *
 * Redirects to /dashboard if the user is already authenticated.
 */
const GuestOnlyRoute = ({ children }: Props) => {
  // Hooks
  const router = useRouter()
  const searchParams = useSearchParams()
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    // Wait until loading is complete
    if (isLoading) return

    // If authenticated, redirect away from guest-only pages
    if (isAuthenticated) {
      const redirectUrl = searchParams?.get('redirect') || '/dashboard'
      router.replace(redirectUrl)
    }
  }, [isAuthenticated, isLoading, router, searchParams])

  // Show loader while checking auth or if already authenticated (redirect pending)
  if (isLoading || isAuthenticated) {
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

  // User is NOT authenticated -> show content (login, register)
  return <>{children}</>
}

export default GuestOnlyRoute
