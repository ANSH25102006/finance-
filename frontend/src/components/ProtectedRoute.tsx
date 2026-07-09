/**
 * components/ProtectedRoute.tsx
 * Wraps a route element and redirects to /login if not authenticated.
 * Shows a loading spinner while the auth check is in flight.
 */

import { Navigate } from 'react-router-dom'
import { type ReactNode } from 'react'
import { useAuth } from '@/hooks/useAuth'

interface ProtectedRouteProps {
  children: ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()

  // While checking auth status, show a minimal loader
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        fontFamily: 'sans-serif',
        color: '#6b7280',
      }}>
        Verifying session…
      </div>
    )
  }

  // Not authenticated — redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
