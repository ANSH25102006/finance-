/**
 * components/FinancialInsights/FinancialInsightsPanel.tsx
 *
 * The primary dashboard section for the Financial Intelligence Engine.
 * Consumes GET /api/intelligence/insights and renders:
 *  - Filter chips (severity)
 *  - Client-side search
 *  - Animated insight cards sorted as returned by backend (CRITICAL first)
 *  - Full-screen details drawer on card click
 *  - Loading skeleton, empty state, and error + retry state
 */

import { useState, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BrainCircuit,
  RefreshCw,
  Sparkles,
  TrendingUp,
  AlertOctagon,
  AlertTriangle,
} from 'lucide-react'
import { useInsights } from '@/hooks/useInsights'
import { InsightCard } from './InsightCard'
import { InsightDetailsDrawer } from './InsightDetailsDrawer'
import { InsightFilters, type FilterOption } from './InsightFilters'
import type { FinancialInsight } from '@/services/intelligenceService'

// ------------------------------------------------------------------ //
// Loading skeleton
// ------------------------------------------------------------------ //

function InsightSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3" aria-label="Loading insights…" aria-busy="true">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="rounded-[16px] border border-white/[0.04] bg-[#0b0c10] p-4 animate-pulse"
          style={{ animationDelay: `${i * 100}ms` }}
        >
          <div className="flex items-start gap-3 mb-3">
            <div className="h-7 w-7 rounded-lg bg-white/[0.04]" />
            <div className="flex-1 space-y-2">
              <div className="h-3 w-48 bg-white/[0.04] rounded" />
              <div className="h-2 w-20 bg-white/[0.02] rounded" />
            </div>
            <div className="h-5 w-14 bg-white/[0.04] rounded" />
          </div>
          <div className="pl-10 space-y-1.5">
            <div className="h-2.5 w-full bg-white/[0.03] rounded" />
            <div className="h-2.5 w-4/5 bg-white/[0.03] rounded" />
          </div>
        </div>
      ))}
    </div>
  )
}

// ------------------------------------------------------------------ //
// Empty state
// ------------------------------------------------------------------ //

function EmptyState({ filtered }: { filtered: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-16 text-center"
      role="status"
      aria-live="polite"
    >
      <div className="h-12 w-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-4">
        <Sparkles className="h-5 w-5 text-emerald-500/60" aria-hidden="true" />
      </div>
      <p className="text-[13px] font-semibold text-white mb-1.5">
        {filtered ? 'No matching insights' : 'No insights yet'}
      </p>
      <p className="text-[11px] text-gray-600 font-medium leading-relaxed max-w-xs">
        {filtered
          ? 'Try adjusting your filters or search query.'
          : 'Import transactions or continue using the app to receive personalised financial analysis.'}
      </p>
    </motion.div>
  )
}

// ------------------------------------------------------------------ //
// Error state
// ------------------------------------------------------------------ //

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-16 text-center"
      role="alert"
    >
      <div className="h-12 w-12 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-4">
        <AlertOctagon className="h-5 w-5 text-red-500/60" aria-hidden="true" />
      </div>
      <p className="text-[13px] font-semibold text-white mb-1.5">
        Could not load insights
      </p>
      <p className="text-[11px] text-gray-600 font-medium leading-relaxed max-w-xs mb-5">
        There was a problem reaching the Financial Intelligence Engine. Your dashboard remains
        fully functional.
      </p>
      <button
        onClick={onRetry}
        className="flex items-center gap-2 px-4 py-2 rounded-xl text-[11px] font-semibold bg-white/[0.04] border border-white/[0.08] text-gray-300 hover:text-white hover:bg-white/[0.08] transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20"
      >
        <RefreshCw className="h-3 w-3" aria-hidden="true" />
        Retry
      </button>
    </motion.div>
  )
}

// ------------------------------------------------------------------ //
// Summary stat chips
// ------------------------------------------------------------------ //

function SummaryStats({ insights }: { insights: FinancialInsight[] }) {
  const criticalCount = insights.filter((i) => i.severity === 'CRITICAL').length
  const warningCount = insights.filter((i) => i.severity === 'WARNING').length
  const successCount = insights.filter((i) => i.severity === 'SUCCESS').length

  if (insights.length === 0) return null

  return (
    <div className="flex items-center gap-2 flex-wrap" aria-label="Insight summary">
      {criticalCount > 0 && (
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-500/10 border border-red-500/20">
          <AlertOctagon className="h-3 w-3 text-red-400" aria-hidden="true" />
          <span className="text-[10px] font-semibold text-red-400 tabular-nums">
            {criticalCount} critical
          </span>
        </div>
      )}
      {warningCount > 0 && (
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <AlertTriangle className="h-3 w-3 text-amber-400" aria-hidden="true" />
          <span className="text-[10px] font-semibold text-amber-400 tabular-nums">
            {warningCount} warnings
          </span>
        </div>
      )}
      {successCount > 0 && (
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <TrendingUp className="h-3 w-3 text-emerald-400" aria-hidden="true" />
          <span className="text-[10px] font-semibold text-emerald-400 tabular-nums">
            {successCount} positive
          </span>
        </div>
      )}
    </div>
  )
}

// ------------------------------------------------------------------ //
// Main panel
// ------------------------------------------------------------------ //

export function FinancialInsightsPanel() {
  const { data: insights, isLoading, isFetching, error, refetch } = useInsights()
  const [activeFilter, setActiveFilter] = useState<FilterOption>('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedInsight, setSelectedInsight] = useState<FinancialInsight | null>(null)

  // Filter + search (client-side, no re-fetch)
  const filtered = useMemo(() => {
    let result = insights

    if (activeFilter !== 'ALL') {
      result = result.filter((i) => i.severity === activeFilter)
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      result = result.filter(
        (i) =>
          i.title.toLowerCase().includes(q) ||
          i.summary.toLowerCase().includes(q) ||
          i.recommendation.toLowerCase().includes(q)
      )
    }

    return result
  }, [insights, activeFilter, searchQuery])

  // Counts per severity for badge display
  const counts = useMemo<Record<FilterOption, number>>(
    () => ({
      ALL: insights.length,
      CRITICAL: insights.filter((i) => i.severity === 'CRITICAL').length,
      WARNING: insights.filter((i) => i.severity === 'WARNING').length,
      SUCCESS: insights.filter((i) => i.severity === 'SUCCESS').length,
      INFO: insights.filter((i) => i.severity === 'INFO').length,
    }),
    [insights]
  )

  const handleCardClick = useCallback((insight: FinancialInsight) => {
    setSelectedInsight(insight)
  }, [])

  const handleCloseDrawer = useCallback(() => {
    setSelectedInsight(null)
  }, [])

  const isFiltered = activeFilter !== 'ALL' || searchQuery.trim() !== ''

  return (
    <>
      <section
        className="os-card flex flex-col relative overflow-hidden w-full"
        aria-labelledby="insights-panel-heading"
      >
        {/* Panel header */}
        <div className="flex flex-col gap-3 border-b border-white/[0.04] pb-4 pt-4 px-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <BrainCircuit
                className="h-3.5 w-3.5 text-cyan-400 animate-pulse"
                aria-hidden="true"
              />
              <h2 id="insights-panel-heading" className="typo-subheading">
                Financial Insights
              </h2>
              {isFetching && !isLoading && (
                <RefreshCw
                  className="h-2.5 w-2.5 text-gray-700 animate-spin"
                  aria-label="Refreshing…"
                />
              )}
            </div>

            <div className="flex items-center gap-2">
              <SummaryStats insights={insights} />
              <button
                onClick={() => refetch()}
                aria-label="Refresh insights"
                disabled={isLoading || isFetching}
                className="h-7 w-7 rounded-lg flex items-center justify-center text-gray-600 hover:text-white hover:bg-white/[0.05] transition-all disabled:opacity-30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20"
              >
                <RefreshCw className={`h-3 w-3 ${isFetching ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Filters (hidden while loading) */}
          {!isLoading && !error && (
            <InsightFilters
              activeFilter={activeFilter}
              onFilterChange={setActiveFilter}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              counts={counts}
            />
          )}
        </div>

        {/* Body */}
        <div className="relative z-10 p-4">
          {isLoading ? (
            <InsightSkeleton count={4} />
          ) : error ? (
            <ErrorState onRetry={refetch} />
          ) : (
            <AnimatePresence mode="wait">
              <motion.div
                key={`${activeFilter}-${searchQuery}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
              >
                {filtered.length === 0 ? (
                  <EmptyState filtered={isFiltered} />
                ) : (
                  <div className="space-y-3">
                    {filtered.map((insight, idx) => (
                      <InsightCard
                        key={insight.id}
                        insight={insight}
                        onClick={handleCardClick}
                        index={idx}
                      />
                    ))}
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </section>

      {/* Details drawer — rendered outside the panel at DOM root level */}
      <InsightDetailsDrawer insight={selectedInsight} onClose={handleCloseDrawer} />
    </>
  )
}
