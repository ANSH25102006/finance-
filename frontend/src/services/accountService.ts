import { apiClient } from '@/services/api'

export interface Account {
  id: string
  user_id: string
  name: string
  balance: number
  currency: string
  icon: string | null
  color: string | null
  institution: string | null
  archived: boolean
  created_at: string
  updated_at: string
}

export async function getAccounts(): Promise<Account[]> {
  const { data } = await apiClient.get<Account[]>('/api/accounts/')
  return data
}

export interface CreateAccountPayload {
  name: string
  balance?: number
  currency?: string
  institution?: string
}

export async function createAccount(payload: CreateAccountPayload): Promise<Account> {
  const { data } = await apiClient.post<Account>('/api/accounts/', payload)
  return data
}
