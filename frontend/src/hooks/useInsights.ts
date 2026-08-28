/**
 * hooks/useInsights.ts
 * TanStack Query hook for fetching and caching financial insights.
 */

import { useQuery } from '@tanstack/react-query'
import { getInsights, type FinancialInsight, type InsightSeverity } from '@/services/intelligenceService'

export const INSIGHTS_QUERY_KEY = ['intelligence', 'insights'] as const

export interface UseInsightsReturn {
  data: FinancialInsight[]
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  refetch: () => void
}

export function useInsights(): UseInsightsReturn {
  const { data, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: INSIGHTS_QUERY_KEY,
    queryFn: () => getInsights({ limit: 50 }),
    staleTime: 5 * 60 * 1000,   // 5 min — insights are deterministic, don't refresh constantly
    retry: 2,
    retryDelay: (attempt) => attempt * 1000,
  })

  return {
    data: data ?? [],
    isLoading,
    isFetching,
    error: error as Error | null,
    refetch,
  }
}

/** Convenience hook: returns only insights of a given severity. */
export function useInsightsBySeverity(severity: InsightSeverity): FinancialInsight[] {
  const { data } = useInsights()
  return data.filter((i) => i.severity === severity)
}
