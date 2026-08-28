/**
 * components/FinancialTimeline/TimelineDetailsDrawer.tsx
 * Full-screen slide-in drawer for a single timeline event.
 */

import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, Clock, ExternalLink, ArrowRight, LayoutList, BrainCircuit } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import type { TimelineEvent } from '@/services/timelineService'
import { SeverityBadge } from '@/components/FinancialInsights/SeverityBadge'

interface TimelineDetailsDrawerProps {
  event: TimelineEvent | null
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

// Reuse the MetadataSection logic from Insights
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
  
  if (scalars.length === 0) return null;

  return (
    <div>
      <p className="typo-subheading mb-3">Event Metadata</p>
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
  )
}

export function TimelineDetailsDrawer({ event, onClose }: TimelineDetailsDrawerProps) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (!event) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    closeRef.current?.focus()
    return () => document.removeEventListener('keydown', handler)
  }, [event, onClose])

  const handleViewTransactions = () => {
    if (!event || event.related_transaction_ids.length === 0) return
    // Preselect transactions via query param
    const ids = event.related_transaction_ids.join(',')
    navigate(`/transactions?ids=${ids}`)
    onClose()
  }

  return (
    <AnimatePresence>
      {event && (
        <>
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

          <motion.aside
            key="drawer"
            role="dialog"
            aria-modal="true"
            aria-label={`Event details: ${event.title}`}
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
            className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-md bg-[#0c0e12] border-l border-white/[0.06] flex flex-col overflow-hidden"
            style={{ boxShadow: '-24px 0 64px -16px rgba(0,0,0,0.9)' }}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.04] flex-shrink-0">
              <div className="flex items-center gap-2">
                <Clock className="h-3.5 w-3.5 text-indigo-400" aria-hidden="true" />
                <span className="typo-subheading">Event Detail</span>
              </div>
              <button
                ref={closeRef}
                onClick={onClose}
                aria-label="Close details"
                className="h-7 w-7 rounded-lg flex items-center justify-center text-gray-600 hover:text-white hover:bg-white/[0.05] transition-all"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-5 space-y-6">
              
              <div className="flex items-center gap-2 flex-wrap">
                <SeverityBadge severity={event.severity} size="md" />
                <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-600 border border-white/[0.06] bg-white/[0.02] px-2 py-1 rounded-md">
                  {event.type.replace(/_/g, ' ')}
                </span>
              </div>

              <div>
                <h2 className="text-[18px] font-semibold text-white tracking-tight leading-snug mb-2">
                  {event.title}
                </h2>
                <div className="flex items-center gap-1.5 text-[11px] text-gray-500 font-medium">
                  <Clock className="h-3 w-3" aria-hidden="true" />
                  {formatIso(event.timestamp)}
                </div>
              </div>

              <div>
                <p className="typo-subheading mb-2">Description</p>
                <p className="text-[13px] text-gray-300 font-medium leading-relaxed bg-white/[0.02] border border-white/[0.04] p-4 rounded-xl">
                  {event.description}
                </p>
              </div>

              {Object.keys(event.metadata).length > 0 && (
                <MetadataSection metadata={event.metadata} />
              )}

              <div>
                <p className="typo-subheading mb-3">Related Actions</p>
                <div className="space-y-2.5">
                  {event.related_transaction_ids.length > 0 && (
                    <button
                      onClick={handleViewTransactions}
                      className="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-indigo-500/20 bg-indigo-500/10 text-[12px] font-semibold text-indigo-100 hover:bg-indigo-500/20 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <LayoutList className="h-4 w-4 text-indigo-400" />
                        View {event.related_transaction_ids.length} Transaction(s)
                      </div>
                      <ArrowRight className="h-4 w-4 text-indigo-400" />
                    </button>
                  )}

                  {event.related_insight_ids.length > 0 && (
                    <button
                      disabled
                      className="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-white/[0.04] bg-white/[0.02] text-[12px] font-medium text-gray-500 cursor-not-allowed"
                    >
                      <div className="flex items-center gap-2">
                        <BrainCircuit className="h-4 w-4" />
                        View Related Insight
                      </div>
                      <span className="text-[9px] uppercase tracking-widest font-semibold border border-white/[0.06] px-1.5 py-0.5 rounded">
                        Soon
                      </span>
                    </button>
                  )}

                  <button
                    disabled
                    className="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-white/[0.04] bg-white/[0.02] text-[12px] font-medium text-gray-500 cursor-not-allowed"
                  >
                    <div className="flex items-center gap-2">
                      <ExternalLink className="h-4 w-4" />
                      Ask AI About This
                    </div>
                    <span className="text-[9px] uppercase tracking-widest font-semibold border border-white/[0.06] px-1.5 py-0.5 rounded">
                      Soon
                    </span>
                  </button>
                </div>
              </div>

            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}
