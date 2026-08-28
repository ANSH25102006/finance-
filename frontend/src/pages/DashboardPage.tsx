/**
 * pages/DashboardPage.tsx
 * Protected premium dashboard.
 */

import { Navbar } from "@/components/dashboard/Navbar"
import { WelcomeHeader } from "@/components/dashboard/WelcomeHeader"
import { FinancialOverview } from "@/components/dashboard/FinancialOverview"
import { CashFlowChart } from "@/components/dashboard/CashFlowChart"
import { FinancialHealth } from "@/components/dashboard/FinancialHealth"
import { SpendingBreakdown } from "@/components/dashboard/SpendingBreakdown"
import { RightSidebar } from "@/components/dashboard/RightSidebar"
import { RecentTransactions } from "@/components/dashboard/RecentTransactions"
import { BudgetProgress } from "@/components/dashboard/BudgetProgress"
import { FinancialInsightsPanel } from "@/components/FinancialInsights"
import { FinancialTimelinePanel } from "@/components/FinancialTimeline"
import { PredictiveIntelligencePanel } from "@/components/PredictiveIntelligence"
import { SavingsSimulatorPanel } from "@/components/SavingsSimulator"
import { useDashboard } from "@/hooks/useDashboard"

export default function DashboardPage() {
  const { data: summary, isLoading, error } = useDashboard()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#060709] text-emerald-500 font-mono text-xs uppercase tracking-widest animate-pulse">
        Loading System...
      </div>
    )
  }

  if (error || !summary) {
    const isAuthError = (error as { response?: { status?: number } })?.response?.status === 401
    if (isAuthError) {
      window.location.href = '/login'
      return null
    }

    return (
      <div className="flex flex-col h-screen items-center justify-center bg-[#060709] text-red-500 font-mono gap-4 p-4 text-center">
        <div className="text-sm uppercase tracking-widest font-semibold">System Offline or Connection Failed</div>
        <p className="text-xs text-neutral-400 max-w-md">
          Unable to fetch dashboard data. Please log in or verify the backend server is running.
        </p>
        <div className="flex gap-3 mt-2">
          <a
            href="/login"
            className="px-4 py-2 text-xs uppercase tracking-wider bg-emerald-600 text-white rounded font-sans font-medium hover:bg-emerald-500 transition-colors"
          >
            Sign In
          </a>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 text-xs uppercase tracking-wider bg-neutral-800 text-neutral-300 rounded font-sans font-medium hover:bg-neutral-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="relative min-h-screen bg-[#060709] text-white selection:bg-emerald-500/30 overflow-hidden">
      
      {/* V5 Subtle Ambient Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-900/5 mesh-blob" />
        <div className="absolute top-[30%] right-[-15%] w-[45%] h-[55%] rounded-full bg-cyan-900/5 mesh-blob" style={{ animationDelay: '-5s' }} />
        <div className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] rounded-full bg-purple-900/5 mesh-blob" style={{ animationDelay: '-10s' }} />
        <div className="absolute inset-0 bg-noise" />
      </div>

      <Navbar />

      <main className="relative z-10 mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 pb-32 pt-16">
        
        <WelcomeHeader summary={summary} />
        
        {/* V5 Zero-Gap Mosaic Grid */}
        <div className="flex flex-col gap-5 mt-4">
          
          {/* Row 1: Bare Metal Analytics (No card wrapping) */}
          <div className="flex flex-col lg:flex-row os-bare-metal rounded-[20px] bg-[#0c0e12]">
            <div className="flex-grow lg:w-2/3 p-6 hairline-r">
              <CashFlowChart summary={summary} />
            </div>
            <div className="lg:w-1/3 p-6">
              <FinancialHealth summary={summary} />
            </div>
          </div>

          {/* Row 2: Inbox & Matrix */}
          <div className="grid grid-cols-12 gap-5">
            <div className="col-span-12 lg:col-span-7 flex">
              <RightSidebar />
            </div>
            <div className="col-span-12 lg:col-span-5 flex">
              <SpendingBreakdown summary={summary} />
            </div>
          </div>

          {/* Row 3: Stripe Pulse Panel */}
          <div className="w-full">
            <FinancialOverview summary={summary} />
          </div>

          {/* Row 4: Apple Wallet Rows */}
          <div className="grid grid-cols-12 gap-5">
            <div className="col-span-12 lg:col-span-8 flex">
              <RecentTransactions summary={summary} />
            </div>
            <div className="col-span-12 lg:col-span-4 flex">
              <BudgetProgress summary={summary} />
            </div>
          </div>

          {/* Row 5: Financial Intelligence Engine Insights */}
          <div className="w-full">
            <FinancialInsightsPanel />
          </div>

          {/* Row 6: Financial Timeline */}
          <div className="w-full">
            <FinancialTimelinePanel />
          </div>

          {/* Row 7: Predictive Intelligence */}
          <div className="w-full">
            <PredictiveIntelligencePanel />
          </div>

          {/* Row 8: Savings Simulator */}
          <div className="w-full">
            <SavingsSimulatorPanel />
          </div>

        </div>
      </main>
    </div>
  )
}

