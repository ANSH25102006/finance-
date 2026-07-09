/**
 * hooks/useAuth.ts
 * Custom hook wrapping the /auth/me query via TanStack Query.
 * Returns the authenticated user, loading state, and authentication status.
 */

import { useQuery } from '@tanstack/react-query'
import { getMe, isAuthenticated, type UserResponse } from '@/services/authService'

export interface UseAuthReturn {
  user: UserResponse | undefined
  isLoading: boolean
  isAuthenticated: boolean
  error: Error | null
}

export function useAuth(): UseAuthReturn {
  const hasToken = isAuthenticated()

  const { data: user, isLoading, error } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: getMe,
    // Only fetch if we have a token — avoids unnecessary 401s
    enabled: hasToken,
    // Don't retry on auth failures
    retry: false,
    // Keep data fresh for 5 minutes
    staleTime: 5 * 60 * 1000,
  })

  return {
    user,
    isLoading: hasToken ? isLoading : false,
    isAuthenticated: Boolean(user),
    error: error as Error | null,
  }
}
