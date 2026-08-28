/**
 * hooks/useTimeline.ts
 * TanStack Query hook for fetching timeline events.
 */

import { useQuery } from '@tanstack/react-query'
import { getTimeline, type TimelineEvent, type GetTimelineParams } from '@/services/timelineService'

export const TIMELINE_QUERY_KEY = ['timeline'] as const

export interface UseTimelineReturn {
  data: TimelineEvent[]
  isLoading: boolean
  isFetching: boolean
  error: Error | null
  refetch: () => void
}

export function useTimeline(params: GetTimelineParams = { limit: 50 }): UseTimelineReturn {
  const { data, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: [...TIMELINE_QUERY_KEY, params],
    queryFn: () => getTimeline(params),
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
