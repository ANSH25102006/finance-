/**
 * pages/DashboardPage.tsx
 * Protected dashboard — only accessible to authenticated users.
 * Shows user email and a working logout button.
 */

import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { logout } from '@/services/authService'
import { queryClient } from '@/lib/queryClient'

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    // Invalidate all cached queries so stale user data is cleared
    queryClient.clear()
    navigate('/login', { replace: true })
  }

  return (
    <main style={styles.page}>
      <div style={styles.container}>
        {/* Top bar */}
        <header style={styles.topBar}>
          <span style={styles.brand}>💰 Finance Auditor</span>
          <button
            id="logout-btn"
            onClick={handleLogout}
            style={styles.logoutBtn}
          >
            Sign out
          </button>
        </header>

        {/* Welcome card */}
        <div style={styles.card}>
          <div style={styles.avatar}>
            {user?.email?.[0]?.toUpperCase() ?? '?'}
          </div>
          <h1 style={styles.greeting}>Welcome back!</h1>
          <p style={styles.email}>{user?.email}</p>
          <p style={styles.note}>
            You're authenticated. Your dashboard content will appear here as features are built.
          </p>
          <div style={styles.badge}>🔐 Session active</div>
        </div>
      </div>
    </main>
  )
}

// ---------------------------------------------------------------------------
// Inline styles
// ---------------------------------------------------------------------------
const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    backgroundColor: '#f9fafb',
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  container: {
    maxWidth: '720px',
    margin: '0 auto',
    padding: '1.5rem 1rem',
  },
  topBar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '2rem',
  },
  brand: {
    fontSize: '1.125rem',
    fontWeight: 700,
    color: '#111827',
  },
  logoutBtn: {
    padding: '0.5rem 1rem',
    fontSize: '0.875rem',
    fontWeight: 500,
    color: '#6b7280',
    backgroundColor: '#fff',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'background-color 0.15s',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: '12px',
    padding: '2.5rem',
    boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
    border: '1px solid #e5e7eb',
    textAlign: 'center',
  },
  avatar: {
    width: '64px',
    height: '64px',
    borderRadius: '50%',
    backgroundColor: '#2563eb',
    color: '#fff',
    fontSize: '1.5rem',
    fontWeight: 700,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 1rem',
  },
  greeting: {
    fontSize: '1.5rem',
    fontWeight: 700,
    color: '#111827',
    margin: '0 0 0.5rem',
  },
  email: {
    fontSize: '1rem',
    color: '#6b7280',
    margin: '0 0 1.25rem',
  },
  note: {
    fontSize: '0.875rem',
    color: '#9ca3af',
    margin: '0 0 1.5rem',
    lineHeight: 1.6,
  },
  badge: {
    display: 'inline-block',
    backgroundColor: '#ecfdf5',
    color: '#065f46',
    border: '1px solid #6ee7b7',
    borderRadius: '9999px',
    padding: '0.375rem 1rem',
    fontSize: '0.8125rem',
    fontWeight: 500,
  },
}
