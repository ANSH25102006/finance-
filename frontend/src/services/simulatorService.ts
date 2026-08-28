/**
 * services/simulatorService.ts
 * API client for the Savings Simulator.
 */

import { apiClient } from './api'

export type ScenarioType =
  | 'CANCEL_SUBSCRIPTION'
  | 'REDUCE_CATEGORY_SPEND'
  | 'REDUCE_MERCHANT_SPEND'
  | 'INCREASE_GOAL_CONTRIBUTION'
  | 'CUSTOM_SAVINGS'

export interface SimulationRequest {
  scenario: ScenarioType
  params: Record<string, unknown>
}

export interface SimulationResult {
  scenario: ScenarioType
  monthly_savings: number
  annual_savings: number
  projected_balance_before: number
  projected_balance_after: number
  methodology: string
  metadata: Record<string, unknown>
}

export const runSimulation = async (request: SimulationRequest): Promise<SimulationResult> => {
  const { data } = await apiClient.post<any>('/api/simulator/run', request)
  return {
    scenario: request.scenario,
    monthly_savings: data.monthly_savings || 0,
    annual_savings: data.annual_savings || 0,
    projected_balance_before: data.projected_balance_before || (data.new_balance || 0),
    projected_balance_after: data.new_balance !== undefined ? data.new_balance : (data.projected_balance_after || 0),
    methodology: data.methodology || "Simulation",
    metadata: data.metadata || {}
  }
}
