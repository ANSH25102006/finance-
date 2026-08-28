/**
 * services/predictionService.ts
 * API client for the Predictive Intelligence Engine.
 */

import { apiClient } from './api'

export type PredictionType =
  | 'CASHFLOW'
  | 'SPENDING'
  | 'BUDGET'
  | 'GOAL'
  | 'SUBSCRIPTION'
  | 'INCOME'
  | 'CATEGORY'
  | 'EMERGENCY_FUND'

export type ConfidenceLevel = 'LOW' | 'MEDIUM' | 'HIGH'

export type ForecastPeriod = '30_DAYS' | '90_DAYS' | '180_DAYS' | '365_DAYS'

export interface Prediction {
  id: string
  type: PredictionType
  title: string
  summary: string
  confidence: ConfidenceLevel
  methodology: string
  forecast_value: number
  forecast_currency: string
  forecast_period: ForecastPeriod
  recommendation: string | null
  prediction_date: string
  related_entity_id: string | null
  metadata: Record<string, unknown>
  created_at: string
}

export interface GetPredictionsParams {
  limit?: number
  forecast_period?: ForecastPeriod
  prediction_type?: PredictionType
}

export const getPredictions = async (params: GetPredictionsParams = {}): Promise<Prediction[]> => {
  const { data } = await apiClient.get<{predictions: Prediction[], summary: Record<string, unknown>}>('/api/predictions', {
    params,
  })
  return data.predictions || []
}
