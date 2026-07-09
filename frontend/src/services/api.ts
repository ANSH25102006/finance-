/**
 * services/api.ts
 * Axios HTTP client configured to communicate with the FastAPI backend.
 * All API service modules should import and use this instance.
 */

import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Timeout after 15 seconds
  timeout: 15_000,
})

// ---------------------------------------------------------------------------
// Request interceptor
// Add auth headers or request logging here as the project grows.
// ---------------------------------------------------------------------------
apiClient.interceptors.request.use(
  (config) => {
    // TODO: attach JWT token once auth is implemented
    // const token = localStorage.getItem('access_token')
    // if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error),
)

// ---------------------------------------------------------------------------
// Response interceptor
// Handle global error states (401, 500, etc.) here.
// ---------------------------------------------------------------------------
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // TODO: handle 401 unauthorised → redirect to login
    return Promise.reject(error)
  },
)
