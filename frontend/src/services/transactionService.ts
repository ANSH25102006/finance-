import { apiClient } from '@/services/api'

export interface Transaction {
  id: string
  user_id: string
  account_id: string
  category_id: string | null
  description: string
  amount: number
  transaction_type: 'income' | 'expense' | 'transfer'
  merchant: string | null
  transaction_date: string
  notes: string | null
  recurring: boolean
  attachment_url: string | null
  created_at: string
  updated_at: string
}

export interface TransactionCreate {
  account_id: string
  category_id?: string | null
  description: string
  amount: number
  transaction_type: 'income' | 'expense' | 'transfer'
  merchant?: string | null
  transaction_date: string
  notes?: string | null
  recurring?: boolean
  attachment_url?: string | null
}

export interface TransactionUpdate {
  account_id?: string
  category_id?: string | null
  description?: string
  amount?: number
  transaction_type?: 'income' | 'expense' | 'transfer'
  merchant?: string | null
  transaction_date?: string
  notes?: string | null
  recurring?: boolean
  attachment_url?: string | null
}

export interface TransactionListResponse {
  items: Transaction[]
  total: number
  page: number
  pages: number
  limit: number
}

export interface TransactionFilters {
  page?: number
  limit?: number
  account_id?: string
  category_id?: string
  transaction_type?: string
  start_date?: string
  end_date?: string
  search?: string
  min_amount?: number
  max_amount?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export async function getTransactions(filters: TransactionFilters = {}): Promise<TransactionListResponse> {
  const { data } = await apiClient.get<TransactionListResponse>('/api/transactions/', { params: filters })
  return data
}

export async function getTransaction(id: string): Promise<Transaction> {
  const { data } = await apiClient.get<Transaction>(`/api/transactions/${id}`)
  return data
}

export async function createTransaction(payload: TransactionCreate): Promise<Transaction> {
  const { data } = await apiClient.post<Transaction>('/api/transactions/', payload)
  return data
}

export async function updateTransaction(id: string, payload: TransactionUpdate): Promise<Transaction> {
  const { data } = await apiClient.put<Transaction>(`/api/transactions/${id}`, payload)
  return data
}

export async function deleteTransaction(id: string): Promise<void> {
  await apiClient.delete(`/api/transactions/${id}`)
}
