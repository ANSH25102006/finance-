import { apiClient } from './api'

export interface DashboardSummary {
  netWorth: number
  income: { current: number; previous: number; change: number }
  expenses: { current: number; previous: number; change: number }
  cashFlow: number
  savingsRate: number
  financialHealth: number
  budgets: Array<{
    id: string
    title: string
    icon: string
    color: string
    target: number
    current: number
    percent: number
    isExceeded: boolean
  }>
  goals: Array<{
    id: string
    title: string
    target: number
    current: number
    percent: number
    icon: string
    color: string
    date: string
  }>
  recentTransactions: Array<{
    id: string
    merchant: string
    category: string
    date: string
    amount: number
    type: string
    logo: string
    color: string
    status: string
  }>
  categoryBreakdown: Array<{
    name: string
    value: number
    amount: number
    color: string
  }>
  monthlyTrend: Array<{
    month: string
    income: number
    expenses: number
  }>
}

export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const { data } = await apiClient.get('/api/dashboard/summary')
  return data
}
