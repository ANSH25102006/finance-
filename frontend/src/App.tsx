/**
 * App.tsx — Application root
 *
 * Sets up:
 *  - TanStack Query provider (server-state management)
 *  - React Router (client-side routing)
 *  - Top-level route definitions with auth guard
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import { lazy, Suspense } from 'react'

import ProtectedRoute from '@/components/ProtectedRoute'

const HomePage = lazy(() => import('@/pages/HomePage'))
const LoginPage = lazy(() => import('@/pages/LoginPage'))
const SignupPage = lazy(() => import('@/pages/SignupPage'))
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const TransactionsPage = lazy(() => import('@/pages/TransactionsPage'))
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'))
const ImportStatement = lazy(() => import('@/pages/ImportStatement'))

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={
          <div className="flex h-screen items-center justify-center bg-[#060709] text-emerald-500 font-mono text-xs uppercase tracking-widest animate-pulse">
            Loading Auditor System...
          </div>
        }>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />

            {/* Protected routes — redirect to /login if not authenticated */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/transactions"
              element={
                <ProtectedRoute>
                  <TransactionsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <AnalyticsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/import"
              element={
                <ProtectedRoute>
                  <ImportStatement />
                </ProtectedRoute>
              }
            />

            {/* Catch-all: redirect unknown paths to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

