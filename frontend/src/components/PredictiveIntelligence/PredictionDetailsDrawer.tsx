/**
 * components/PredictiveIntelligence/PredictionDetailsDrawer.tsx
 * Slide-in drawer for full prediction detail.
 */

import { useEffect, useRef } from 'react'
import { X, ExternalLink, Lightbulb, TrendingUp, Sparkles, Binary } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Prediction } from '@/services/predictionService'

interface PredictionDetailsDrawerProps {
  prediction: Prediction | null
  onClose: () => void
}

function MetadataSection({ metadata }: { metadata: Record<string, unknown> }) {
  const fmt = (key: string, val: unknown): string => {
    if (typeof val === 'number') {
      if (/amount|spend|cost|balance|income|expense|saving|price|total|net/i.test(key))
        return `₹${Number(val).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
      if (/pct|percent|rate|ratio/i.test(key)) return `${Number(val).toFixed(2)}%`
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
      <p className="typo-subheading mb-3">Historical Support Data</p>
      <div className="grid grid-cols-2 gap-3">
        {scalars.map(([k, v]) => (
          <div key={k} className="os-inner-panel px-3 py-2.5 bg-fuchsia-500/[0.02] border-fuchsia-500/10">
            <p className="text-[9px] uppercase tracking-widest text-fuchsia-500/60 font-semibold mb-0.5">
              {label(k)}
            </p>
            <p className="text-[13px] font-semibold text-white tabular-nums">{fmt(k, v)}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export function PredictionDetailsDrawer({ prediction, onClose }: PredictionDetailsDrawerProps) {
  const closeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!prediction) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    closeRef.current?.focus()
    return () => document.removeEventListener('keydown', handler)
  }, [prediction, onClose])

  const formatCurrency = (val: number, cur: string) => 
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: cur, maximumFractionDigits: 0 }).format(val)

  return (
    <AnimatePresence>
      {prediction && (
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
            aria-label={`Prediction details: ${prediction.title}`}
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
            className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-md bg-[#0c0e12] border-l border-white/[0.06] flex flex-col overflow-hidden"
            style={{ boxShadow: '-24px 0 64px -16px rgba(0,0,0,0.9)' }}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.04] flex-shrink-0">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-3.5 w-3.5 text-fuchsia-400" aria-hidden="true" />
                <span className="typo-subheading text-fuchsia-100">Prediction Detail</span>
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
                <span className="text-[9px] font-semibold uppercase tracking-widest text-fuchsia-400 border border-fuchsia-500/20 bg-fuchsia-500/10 px-2 py-1 rounded-md">
                  {prediction.type.replace(/_/g, ' ')}
                </span>
                <span className="text-[9px] font-semibold uppercase tracking-widest text-gray-500 border border-white/[0.06] bg-white/[0.02] px-2 py-1 rounded-md">
                  Confidence: {prediction.confidence}
                </span>
              </div>

              <div>
                <h2 className="text-[18px] font-semibold text-white tracking-tight leading-snug mb-1">
                  {prediction.title}
                </h2>
                <div className="text-[24px] font-bold text-white tabular-nums tracking-tight">
                  {formatCurrency(prediction.forecast_value, prediction.forecast_currency)}
                </div>
              </div>

              <div>
                <p className="typo-subheading mb-2">Summary</p>
                <p className="text-[13px] text-gray-300 font-medium leading-relaxed bg-white/[0.02] border border-white/[0.04] p-4 rounded-xl">
                  {prediction.summary}
                </p>
              </div>

              <div>
                <p className="typo-subheading mb-2">Methodology</p>
                <div className="flex items-start gap-3 bg-blue-500/[0.05] border border-blue-500/15 rounded-xl p-4">
                  <Binary className="h-4 w-4 text-blue-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                  <div>
                    <p className="text-[12px] text-blue-100 font-semibold mb-1">
                      {prediction.methodology}
                    </p>
                    <p className="text-[11px] text-blue-200/70 font-medium leading-relaxed">
                      This is a deterministic statistical forecast based purely on your historical data. No AI was used to calculate this value.
                    </p>
                  </div>
                </div>
              </div>

              {prediction.recommendation && (
                <div>
                  <p className="typo-subheading mb-2">Recommendation</p>
                  <div className="flex items-start gap-3 bg-yellow-500/[0.05] border border-yellow-500/15 rounded-xl p-4">
                    <Lightbulb className="h-4 w-4 text-yellow-500/60 flex-shrink-0 mt-0.5" aria-hidden="true" />
                    <p className="text-[12px] text-gray-300 font-medium leading-relaxed">
                      {prediction.recommendation}
                    </p>
                  </div>
                </div>
              )}

              {Object.keys(prediction.metadata).length > 0 && (
                <MetadataSection metadata={prediction.metadata} />
              )}

              {/* Future Action Placeholders */}
              <div>
                <p className="typo-subheading mb-3">Tools</p>
                <div className="space-y-2.5">
                  <button
                    disabled
                    className="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-white/[0.04] bg-white/[0.02] text-[12px] font-medium text-gray-500 cursor-not-allowed"
                  >
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4" />
                      Ask AI to Explain This Forecast
                    </div>
                    <span className="text-[9px] uppercase tracking-widest font-semibold border border-white/[0.06] px-1.5 py-0.5 rounded">
                      Soon
                    </span>
                  </button>

                  <button
                    disabled
                    className="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-white/[0.04] bg-white/[0.02] text-[12px] font-medium text-gray-500 cursor-not-allowed"
                  >
                    <div className="flex items-center gap-2">
                      <ExternalLink className="h-4 w-4" />
                      Run What-If Simulation
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
