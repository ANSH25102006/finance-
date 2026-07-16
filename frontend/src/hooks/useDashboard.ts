import { useQuery } from '@tanstack/react-query'
import { getDashboardSummary, type DashboardSummary } from '@/services/dashboardService'

export interface UseDashboardReturn {
  data: DashboardSummary | undefined
  isLoading: boolean
  error: Error | null
}

export function useDashboard(): UseDashboardReturn {
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: getDashboardSummary,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })

  return {
    data,
    isLoading,
    error: error as Error | null,
  }
}
