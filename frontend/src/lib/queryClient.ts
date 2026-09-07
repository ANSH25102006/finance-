/**
 * lib/queryClient.ts
 * Shared TanStack Query client configuration.
 * Import this instance anywhere you need to use QueryClient directly.
 */

import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Data considered fresh for 60 seconds
      staleTime: 60 * 1000,
      // Retry failed requests up to 1 time
      retry: 1,
    },
  },
})
