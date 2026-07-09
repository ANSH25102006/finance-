/**
 * layouts/RootLayout.tsx
 * Root layout wrapper for shared page chrome (nav, footer, etc.).
 * Wrap pages with this layout via React Router's <Outlet /> pattern.
 *
 * Usage in App.tsx:
 *   <Route element={<RootLayout />}>
 *     <Route path="/" element={<HomePage />} />
 *   </Route>
 */

import { type ReactNode } from 'react'

interface RootLayoutProps {
  children: ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col">
      {/* TODO: Add <Navbar /> component here */}
      <main className="flex-1">
        {children}
      </main>
      {/* TODO: Add <Footer /> component here */}
    </div>
  )
}
