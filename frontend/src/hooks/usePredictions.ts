/**
 * hooks/usePredictions.ts
 * TanStack Query hook for fetching predictions.
 */

import { useQuery } from '@tanstack/react-query'
import { getPredictions, type Prediction, type GetPredictionsParams } from '@/services/predictionService'

export const PREDICTIONS_QUERY_KEY = ['predictions'] as const

export interface UsePredictionsReturn {
  data: Prediction[]
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  refetch: () => void
}

export function usePredictions(params: GetPredictionsParams = { limit: 50 }): UsePredictionsReturn {
  const { data, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: [...PREDICTIONS_QUERY_KEY, params],
    queryFn: () => getPredictions(params),
    staleTime: 5 * 60 * 1000, // 5 min
    retry: 2,
  })

  return {
    data: data ?? [],
    isLoading,
    isFetching,
    error: error as Error | null,
    refetch,
  }
}
