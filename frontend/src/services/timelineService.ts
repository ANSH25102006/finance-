/**
 * services/timelineService.ts
 * Fetches timeline events from the backend engine.
 */

import { apiClient } from './api'

export type TimelineEventSeverity = 'CRITICAL' | 'WARNING' | 'INFO' | 'SUCCESS'

export type TimelineEventType =
  | 'SALARY_CREDITED'
  | 'LARGE_PURCHASE'
  | 'LARGE_REFUND'
  | 'SPENDING_SPIKE'
  | 'BUDGET_WARNING'
  | 'SUBSCRIPTION_DETECTED'
  | 'PRICE_INCREASE'
  | 'GOAL_MILESTONE'
  | 'EMERGENCY_FUND_MILESTONE'
  | 'CASHFLOW_WARNING'
  | 'SAVINGS_OPPORTUNITY'
  | 'CATEGORY_TREND'
  | 'LIFESTYLE_INFLATION'
  | 'MONTHLY_COMPARISON'

export interface TimelineEvent {
  id: string
  type: TimelineEventType
  severity: TimelineEventSeverity
  title: string
  description: string
  timestamp: string
  related_transaction_ids: string[]
  related_insight_ids: string[]
  metadata: Record<string, unknown>
  created_at: string
}

export interface GetTimelineParams {
  limit?: number
  severity?: TimelineEventSeverity
  event_type?: TimelineEventType
}

export const getTimeline = async (params: GetTimelineParams = {}): Promise<TimelineEvent[]> => {
  const { data } = await apiClient.get<{events: TimelineEvent[]}>('/api/timeline', {
    params,
  })
  return data.events || []
}
