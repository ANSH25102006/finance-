/**
 * App.tsx — Application root
 *
 * Sets up:
 *  - TanStack Query provider (server-state management)
 *  - React Router (client-side routing)
 *  - Top-level route definitions
 *
 * Add new routes here as pages are implemented.
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'

import HomePage from '@/pages/HomePage'
import LoginPage from '@/pages/LoginPage'
import SignupPage from '@/pages/SignupPage'
import DashboardPage from '@/pages/DashboardPage'

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          {/* Protected routes (auth guard to be added later) */}
          <Route path="/dashboard" element={<DashboardPage />} />

          {/* Catch-all: redirect unknown paths to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
