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
