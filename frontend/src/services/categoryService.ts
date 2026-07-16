import { apiClient } from '@/services/api'

export interface Category {
  id: string
  user_id: string | null
  name: string
  type: string
  icon: string | null
  color: string | null
  created_at: string
  updated_at: string
}

export async function getCategories(type?: string): Promise<Category[]> {
  const { data } = await apiClient.get<Category[]>('/api/categories/', {
    params: type ? { type } : undefined,
  })
  return data
}
