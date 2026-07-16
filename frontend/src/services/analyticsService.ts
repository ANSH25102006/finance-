import { apiClient } from './api'

export interface AnalyticsDashboardSummary {
  current_balance: number
  total_income: number
  total_expenses: number
  net_cash_flow: number
  total_transaction_count: number
  average_transaction_value: number
  highest_expense: number
  highest_income: number
}

export interface MonthlyTrend {
  month: string
  income: number
  expense: number
  net_cash_flow: number
}

export interface CategoryBreakdown {
  category_name: string
  total_amount: number
  percentage: number
  transaction_count: number
}

export interface TopMerchant {
  merchant_name: string
  total_amount: number
  transaction_count: number
}

export interface LargestExpense {
  merchant: string
  amount: number
  category: string
  date: string
  description: string
}

export interface DailySpending {
  date: string
  total_spend: number
}

export interface SpendingTrend {
  average_daily_spend: number
  average_monthly_spend: number
  average_transaction_amount: number
  median_transaction_amount: number
}

export interface FinancialHealthScore {
  score: number
  rating: 'Excellent' | 'Good' | 'Fair' | 'Needs Improvement'
  explanations: string[]
}

export async function getAnalyticsDashboard(): Promise<AnalyticsDashboardSummary> {
  const { data } = await apiClient.get<AnalyticsDashboardSummary>('/api/analytics/dashboard')
  return data
}

export async function getAnalyticsMonthlyTrends(): Promise<MonthlyTrend[]> {
  const { data } = await apiClient.get<MonthlyTrend[]>('/api/analytics/monthly-trends')
  return data
}

export async function getAnalyticsCategoryBreakdown(): Promise<CategoryBreakdown[]> {
  const { data } = await apiClient.get<CategoryBreakdown[]>('/api/analytics/category-breakdown')
  return data
}

export async function getAnalyticsTopMerchants(): Promise<TopMerchant[]> {
  const { data } = await apiClient.get<TopMerchant[]>('/api/analytics/top-merchants')
  return data
}

export async function getAnalyticsLargestExpenses(): Promise<LargestExpense[]> {
  const { data } = await apiClient.get<LargestExpense[]>('/api/analytics/largest-expenses')
  return data
}

export async function getAnalyticsCashFlow(): Promise<MonthlyTrend[]> {
  const { data } = await apiClient.get<MonthlyTrend[]>('/api/analytics/cash-flow')
  return data
}

export async function getAnalyticsDailySpending(): Promise<DailySpending[]> {
  const { data } = await apiClient.get<DailySpending[]>('/api/analytics/daily-spending')
  return data
}

export async function getAnalyticsSpendingTrend(): Promise<SpendingTrend> {
  const { data } = await apiClient.get<SpendingTrend>('/api/analytics/spending-trend')
  return data
}

export async function getAnalyticsFinancialHealth(): Promise<FinancialHealthScore> {
  const { data } = await apiClient.get<FinancialHealthScore>('/api/analytics/financial-health')
  return data
}
