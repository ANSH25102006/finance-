/**
 * components/FinancialInsights/InsightDetailsDrawer.tsx
 * Full-screen slide-in drawer for a single insight.
 * Future-ready slots for: View Transactions, View Timeline, Ask AI.
 */

import { useEffect, useRef } from 'react'
import { X, BrainCircuit, Clock, Tag, BarChart2, Lightbulb, ArrowRight } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import type { FinancialInsight } from '@/services/intelligenceService'
import { SeverityBadge, SEVERITY_CONFIG } from './SeverityBadge'

interface InsightDetailsDrawerProps {
  insight: FinancialInsight | null
  onClose: () => void
}

function formatIso(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function MetadataSection({ metadata }: { metadata: Record<string, unknown> }) {
  const fmt = (key: string, val: unknown): string => {
    if (typeof val === 'number') {
      if (/amount|spend|cost|balance|income|expense|saving|price|total/i.test(key))
        return `₹${Number(val).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
      if (/pct|percent|rate|ratio/i.test(key)) return `${Number(val).toFixed(1)}%`
      return Number(val).toLocaleString('en-IN', { maximumFractionDigits: 2 })
    }
    if (typeof val === 'boolean') return val ? 'Yes' : 'No'
    return String(val)
  }
  const label = (k: string) => k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

  const scalars = Object.entries(metadata).filter(
    ([, v]) => v !== null && v !== undefined && typeof v !== 'object'
  )
  const objects = Object.entries(metadata).filter(
    ([, v]) => v !== null && v !== undefined && typeof v === 'object' && !Array.isArray(v)
  )
  const arrays = Object.entries(metadata).filter(([, v]) => Array.isArray(v))

  return (
    <div className="space-y-5">
      {/* Scalar key/value grid */}
      {scalars.length > 0 && (
        <div>
          <p className="typo-subheading mb-3">Details</p>
          <div className="grid grid-cols-2 gap-3">
            {scalars.map(([k, v]) => (
              <div key={k} className="os-inner-panel px-3 py-2.5">
                <p className="text-[9px] uppercase tracking-widest text-gray-600 font-semibold mb-0.5">
                  {label(k)}
                </p>
                <p className="text-[13px] font-semibold text-white tabular-nums">{fmt(k, v)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Nested objects */}
      {objects.map(([k, v]) => (
        <div key={k}>
          <p className="typo-subheading mb-3">{label(k)}</p>
          <div className="grid grid-cols-3 gap-2">
            {Object.entries(v as Record<string, unknown>).map(([mk, mv]) => (
              <div key={mk} className="os-inner-panel px-2 py-2 text-center">
                <p className="text-[9px] text-gray-600 font-medium mb-0.5">{mk}</p>
                <p className="text-[11px] font-semibold text-white tabular-nums">{fmt(mk, mv)}</p>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Arrays */}
      {arrays.map(([k, arr]) => (
        <div key={k}>
          <p className="typo-subheading mb-3">{label(k)}</p>
          <ul className="space-y-1.5">
            {(arr as unknown[]).slice(0, 8).map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-[11px] text-gray-400 font-medium">
                <span className="mt-1.5 h-1 w-1 rounded-full bg-gray-600 flex-shrink-0" />
                <span>
                  {typeof item === 'object'
                    ? Object.entries(item as Record<string, unknown>)
                        .map(([mk, mv]) => `${label(mk)}: ${fmt(mk, mv)}`)
                        .join('  ·  ')
                    : String(item)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

export function InsightDetailsDrawer({ insight, onClose }: InsightDetailsDrawerProps) {
  const closeRef = useRef<HTMLButtonElement>(null)

  // Close on Escape, trap focus
  useEffect(() => {
    if (!insight) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    closeRef.current?.focus()
    return () => document.removeEventListener('keydown', handler)
  }, [insight, onClose])

  const cfg = insight ? SEVERITY_CONFIG[insight.severity] : null
  const Icon = cfg?.icon

  return (
    <AnimatePresence>
      {insight && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm"
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Drawer */}
          <motion.aside
            key="drawer"
            role="dialog"
            aria-modal="true"
            aria-label={`Insight details: ${insight.title}`}
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
            className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-md bg-[#0c0e12] border-l border-white/[0.06] flex flex-col overflow-hidden"
            style={{
              boxShadow: '-24px 0 64px -16px rgba(0,0,0,0.9)',
            }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.04] flex-shrink-0">
              <div className="flex items-center gap-2">
                <BrainCircuit className="h-3.5 w-3.5 text-cyan-400" aria-hidden="true" />
                <span className="typo-subheading">Insight Detail</span>
              </div>
              <button
                ref={closeRef}
                onClick={onClose}
                aria-label="Close insight details"
                className="h-7 w-7 rounded-lg flex items-center justify-center text-gray-600 hover:text-white hover:bg-white/[0.05] transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Scrollable body */}
            <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">

              {/* Severity + type row */}
              <div className="flex items-center gap-2 flex-wrap">
                <SeverityBadge severity={insight.severity} size="md" />
                <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-600 border border-white/[0.06] bg-white/[0.02] px-2 py-1 rounded-md">
                  {insight.type.replace(/_/g, ' ')}
                </span>
              </div>

              {/* Title */}
              <div className="flex items-start gap-3">
                {cfg && Icon && (
                  <div className={`flex-shrink-0 h-9 w-9 rounded-xl flex items-center justify-center ${cfg.bgColor} border ${cfg.borderColor}`}>
                    <Icon className={`h-4.5 w-4.5 ${cfg.textColor}`} />
                  </div>
                )}
                <div>
                  <h2 className="text-[15px] font-semibold text-white tracking-tight leading-snug">
                    {insight.title}
                  </h2>
                  <div className="flex items-center gap-3 mt-1">
                    {insight.category && (
                      <span className="flex items-center gap-1 text-[10px] text-gray-600 font-medium">
                        <Tag className="h-2.5 w-2.5" aria-hidden="true" />
                        {insight.category}
                      </span>
                    )}
                    {insight.created_at && (
                      <span className="flex items-center gap-1 text-[10px] text-gray-600 font-medium">
                        <Clock className="h-2.5 w-2.5" aria-hidden="true" />
                        {formatIso(insight.created_at)}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Summary */}
              <div>
                <p className="typo-subheading mb-2">Summary</p>
                <p className="text-[12.5px] text-gray-300 font-medium leading-relaxed">
                  {insight.summary}
                </p>
              </div>

              {/* Recommendation */}
              {insight.recommendation && (
                <div>
                  <p className="typo-subheading mb-2">Recommendation</p>
                  <div className="flex items-start gap-3 bg-yellow-500/[0.05] border border-yellow-500/15 rounded-xl p-4">
                    <Lightbulb className="h-4 w-4 text-yellow-500/60 flex-shrink-0 mt-0.5" aria-hidden="true" />
                    <p className="text-[12px] text-gray-300 font-medium leading-relaxed">
                      {insight.recommendation}
                    </p>
                  </div>
                </div>
              )}

              {/* Score */}
              {insight.score > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="flex items-center gap-1.5 typo-subheading">
                      <BarChart2 className="h-3 w-3" aria-hidden="true" />
                      Signal Strength
                    </span>
                    <span className={`text-[11px] font-semibold tabular-nums ${cfg?.textColor}`}>
                      {insight.score.toFixed(0)}
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-white/5 overflow-hidden">
                    <motion.div
                      className={`h-full rounded-full ${cfg?.dotColor}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(insight.score, 100)}%` }}
                      transition={{ duration: 0.6, ease: 'easeOut', delay: 0.15 }}
                      aria-hidden="true"
                    />
                  </div>
                </div>
              )}

              {/* Metadata */}
              {Object.keys(insight.metadata).length > 0 && (
                <div>
                  <p className="typo-subheading mb-3">Analysis Data</p>
                  <MetadataSection metadata={insight.metadata} />
                </div>
              )}

              {/* Future-ready action buttons (disabled placeholders) */}
              <div>
                <p className="typo-subheading mb-3">Actions</p>
                <div className="space-y-2">
                  {[
                    { label: 'View Related Transactions', soon: true },
                    { label: 'View Timeline Event', soon: true },
                    { label: 'Ask AI About This Insight', soon: true },
                  ].map(({ label, soon }) => (
                    <button
                      key={label}
                      disabled={soon}
                      aria-disabled="true"
                      className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl border border-white/[0.04] bg-white/[0.01] text-[11px] font-medium text-gray-700 cursor-not-allowed opacity-50"
                    >
                      {label}
                      <div className="flex items-center gap-2">
                        <span className="text-[8px] uppercase tracking-widest font-semibold text-gray-700 border border-white/[0.06] px-1.5 py-0.5 rounded">
                          Soon
                        </span>
                        <ArrowRight className="h-3 w-3" aria-hidden="true" />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
