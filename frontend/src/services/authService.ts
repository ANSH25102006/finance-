/**
 * services/authService.ts
 * Auth API calls: signup, login, logout, getMe
 */

import { apiClient } from '@/services/api'
import { queryClient } from '@/lib/queryClient'

export interface SignupPayload {
  email: string
  password: string
}

export interface LoginPayload {
  email: string
  password: string
}

export interface UserResponse {
  id: string
  email: string
  created_at: string
  updated_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

/** Register a new account. Returns the created user. */
export async function signup(payload: SignupPayload): Promise<UserResponse> {
  const { data } = await apiClient.post<UserResponse>('/auth/signup', payload)
  return data
}

/** Login with email + password. Stores JWT in localStorage on success and primes user cache. */
export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>('/auth/login', payload)
  localStorage.setItem('access_token', data.access_token)

  // Immediately fetch and seed the user profile into TanStack query cache
  try {
    const meData = await getMe()
    queryClient.setQueryData(['auth', 'me'], meData)
  } catch (err) {
    console.error('Failed to pre-fetch user profile:', err)
  }

  return data
}

/** Remove JWT from localStorage (client-side logout). */
export function logout(): void {
  localStorage.removeItem('access_token')
  queryClient.setQueryData(['auth', 'me'], null)
}

/** Fetch the currently authenticated user's profile. */
export async function getMe(): Promise<UserResponse> {
  const { data } = await apiClient.get<UserResponse>('/auth/me')
  return data
}

/** Returns true if a token exists in localStorage. */
export function isAuthenticated(): boolean {
  return Boolean(localStorage.getItem('access_token'))
}
