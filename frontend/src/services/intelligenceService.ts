/**
 * services/intelligenceService.ts
 * Fetches deterministic financial insights from the backend engine.
 * The frontend performs zero calculations — everything comes from the API.
 */

import { apiClient } from './api'

// ------------------------------------------------------------------ //
// Types — mirror the backend FinancialInsight model exactly
// ------------------------------------------------------------------ //

export type InsightSeverity = 'CRITICAL' | 'WARNING' | 'INFO' | 'SUCCESS'

export type InsightType =
  | 'SPENDING_SPIKE'
  | 'BUDGET_DRIFT'
  | 'PRICE_INCREASE'
  | 'GOAL_PROGRESS'
  | 'INCOME_CHANGE'
  | 'EMERGENCY_FUND'
  | 'SAVINGS_OPPORTUNITY'
  | 'CATEGORY_TREND'
  | 'LARGE_TRANSACTION'
  | 'MERCHANT_CONCENTRATION'
  | 'CASHFLOW_WARNING'
  | 'LIFESTYLE_INFLATION'
  | 'MONTHLY_COMPARISON'
  | 'WEEKEND_SPENDING'

export interface FinancialInsight {
  id: string
  type: InsightType
  severity: InsightSeverity
  title: string
  summary: string
  recommendation: string
  score: number
  category: string | null
  created_at: string
  metadata: Record<string, unknown>
}

export interface GetInsightsParams {
  severity?: InsightSeverity
  type?: InsightType
  limit?: number
}

export const getInsights = async (params: GetInsightsParams = {}): Promise<FinancialInsight[]> => {
  const { data } = await apiClient.get<FinancialInsight[]>('/api/intelligence/insights', {
    params,
  })
  return data
}
