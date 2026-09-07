/**
 * services/api.ts
 * Axios HTTP client — JWT auth interceptors now active.
 */

import axios from 'axios'

const getBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL
  if (envUrl) {
    return envUrl.trim().replace(/\/+$/, '')
  }
  // Dev fallback: connect to local API server
  const hostname = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1'
  const finalHost = hostname === 'localhost' ? '127.0.0.1' : hostname
  return `http://${finalHost}:8000`
}

export const apiClient = axios.create({
  baseURL: getBaseUrl(),
  headers: { 'Content-Type': 'application/json' },
  timeout: 15_000,
})

// ---------------------------------------------------------------------------
// Request interceptor — attach JWT from localStorage on every request
// ---------------------------------------------------------------------------
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ---------------------------------------------------------------------------
// Response interceptor — clear token and redirect on 401
// ---------------------------------------------------------------------------
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      // Only redirect if not already on auth pages to avoid redirect loops
      const path = window.location.pathname
      if (path !== '/login' && path !== '/signup') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)
