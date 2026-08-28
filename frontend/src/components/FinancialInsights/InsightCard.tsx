/**
 * components/FinancialInsights/InsightCard.tsx
 * Individual insight card with collapsible metadata and recommendation.
 */

import { useState, memo } from 'react'
import { ChevronDown, ChevronUp, Lightbulb, BarChart2, Tag } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import type { FinancialInsight } from '@/services/intelligenceService'
import { SeverityBadge, SEVERITY_CONFIG } from './SeverityBadge'

// ------------------------------------------------------------------ //
// Metadata table renderer — formats the backend metadata object
// ------------------------------------------------------------------ //

function MetadataTable({ metadata }: { metadata: Record<string, unknown> }) {
  const entries = Object.entries(metadata).filter(
    ([, v]) => v !== null && v !== undefined && typeof v !== 'object'
  )
  const nested = Object.entries(metadata).filter(
    ([, v]) => v !== null && v !== undefined && typeof v === 'object' && !Array.isArray(v)
  )
  const arrays = Object.entries(metadata).filter(([, v]) => Array.isArray(v))

  const fmt = (key: string, val: unknown): string => {
    if (typeof val === 'number') {
      // Detect currency-like keys
      if (/amount|spend|cost|balance|income|expense|saving|price|total/i.test(key)) {
        return `₹${Number(val).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
      }
      if (/pct|percent|rate|ratio/i.test(key)) {
        return `${Number(val).toFixed(1)}%`
      }
      if (/months|days/i.test(key)) {
        return `${Number(val).toFixed(1)}`
      }
      return String(val)
    }
    return String(val)
  }

  const label = (key: string) =>
    key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

  return (
    <div className="space-y-3">
      {entries.length > 0 && (
        <div className="grid grid-cols-2 gap-x-4 gap-y-2">
          {entries.map(([k, v]) => (
            <div key={k} className="flex flex-col gap-0.5">
              <span className="text-[9px] uppercase tracking-widest text-gray-600 font-semibold">
                {label(k)}
              </span>
              <span className="text-[12px] font-semibold text-white tabular-nums">
                {fmt(k, v)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Monthly series / nested objects */}
      {nested.map(([k, v]) => (
        <div key={k}>
          <p className="text-[9px] uppercase tracking-widest text-gray-600 font-semibold mb-1.5">
            {label(k)}
          </p>
          <div className="grid grid-cols-3 gap-1.5">
            {Object.entries(v as Record<string, unknown>).map(([mk, mv]) => (
              <div key={mk} className="os-inner-panel px-2 py-1.5 text-center">
                <p className="text-[9px] text-gray-600 font-medium">{mk}</p>
                <p className="text-[11px] font-semibold text-white tabular-nums">
                  {fmt(mk, mv)}
                </p>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Array lists */}
      {arrays.map(([k, arr]) => (
        <div key={k}>
          <p className="text-[9px] uppercase tracking-widest text-gray-600 font-semibold mb-1.5">
            {label(k)}
          </p>
          <ul className="space-y-1">
            {(arr as unknown[]).slice(0, 5).map((item, i) => (
              <li key={i} className="flex items-start gap-1.5 text-[11px] text-gray-400">
                <span className="mt-[3px] h-1 w-1 rounded-full bg-gray-600 flex-shrink-0" />
                {typeof item === 'object'
                  ? Object.entries(item as Record<string, unknown>)
                      .map(([mk, mv]) => `${label(mk)}: ${fmt(mk, mv)}`)
                      .join('  ·  ')
                  : String(item)}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}

// ------------------------------------------------------------------ //
// InsightCard
// ------------------------------------------------------------------ //

interface InsightCardProps {
  insight: FinancialInsight
  onClick: (insight: FinancialInsight) => void
  index?: number
}

export const InsightCard = memo(function InsightCard({
  insight,
  onClick,
  index = 0,
}: InsightCardProps) {
  const [expanded, setExpanded] = useState(false)
  const cfg = SEVERITY_CONFIG[insight.severity]
  const Icon = cfg.icon
  const hasMetadata = Object.keys(insight.metadata).length > 0

  const toggleExpanded = (e: React.MouseEvent) => {
    e.stopPropagation()
    setExpanded((v) => !v)
  }

  const relativeTime = (iso: string) => {
    try {
      const diff = Date.now() - new Date(iso).getTime()
      const mins = Math.floor(diff / 60000)
      if (mins < 60) return `${mins}m ago`
      const hrs = Math.floor(mins / 60)
      if (hrs < 24) return `${hrs}h ago`
      return `${Math.floor(hrs / 24)}d ago`
    } catch {
      return ''
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: index * 0.04, ease: 'easeOut' }}
      className="group/card relative overflow-hidden rounded-[16px] border border-white/[0.04] bg-[#0b0c10] cursor-pointer"
      style={{ boxShadow: `inset 0 1px 0 rgba(255,255,255,0.05), 0 1px 3px rgba(0,0,0,0.4)` }}
      onClick={() => onClick(insight)}
      tabIndex={0}
      role="button"
      aria-label={`View details: ${insight.title}`}
      onKeyDown={(e) => e.key === 'Enter' && onClick(insight)}
    >
      {/* Severity left-edge glow strip */}
      <div
        className="absolute left-0 top-0 bottom-0 w-[2px] transition-opacity duration-300 opacity-60 group-hover/card:opacity-100"
        style={{ backgroundColor: cfg.dotColor.replace('bg-', '').includes('red') ? '#f87171' : cfg.dotColor.includes('amber') ? '#fbbf24' : cfg.dotColor.includes('emerald') ? '#34d399' : '#60a5fa' }}
        aria-hidden="true"
      />

      {/* Subtle severity glow on hover */}
      <div
        className="absolute inset-0 opacity-0 group-hover/card:opacity-100 transition-opacity duration-500 pointer-events-none rounded-[16px]"
        style={{ background: `radial-gradient(ellipse at 0% 50%, ${cfg.glowColor} 0%, transparent 60%)` }}
        aria-hidden="true"
      />

      <div className="relative z-10 p-4">
        {/* Header row */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div
              className={`flex-shrink-0 h-7 w-7 rounded-lg flex items-center justify-center ${cfg.bgColor} border ${cfg.borderColor}`}
              aria-hidden="true"
            >
              <Icon className={`h-3.5 w-3.5 ${cfg.textColor}`} />
            </div>
            <div className="min-w-0">
              <h3 className="text-[12px] font-semibold text-white tracking-tight leading-tight truncate">
                {insight.title}
              </h3>
              <div className="flex items-center gap-2 mt-0.5">
                {insight.category && (
                  <span className="flex items-center gap-1 text-[9px] text-gray-600 font-medium">
                    <Tag className="h-2 w-2" aria-hidden="true" />
                    {insight.category}
                  </span>
                )}
                {insight.created_at && (
                  <span className="text-[9px] text-gray-700 font-medium">
                    {relativeTime(insight.created_at)}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <SeverityBadge severity={insight.severity} size="sm" />
            {/* Score mini-bar */}
            {insight.score > 0 && (
              <div className="flex items-center gap-1" title={`Score: ${insight.score.toFixed(0)}`}>
                <BarChart2 className="h-3 w-3 text-gray-700" aria-hidden="true" />
                <div className="w-10 h-1 rounded-full bg-white/5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${cfg.dotColor}`}
                    style={{ width: `${Math.min(insight.score, 100)}%` }}
                    aria-hidden="true"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Summary */}
        <p className="text-[11px] text-gray-400 font-medium leading-relaxed mb-3 pl-[2.375rem]">
          {insight.summary}
        </p>

        {/* Recommendation box */}
        {insight.recommendation && (
          <div className="pl-[2.375rem] mb-3">
            <div className="flex items-start gap-2 bg-white/[0.02] border border-white/[0.04] rounded-xl p-3">
              <Lightbulb
                className="h-3 w-3 text-yellow-500/70 flex-shrink-0 mt-[1px]"
                aria-hidden="true"
              />
              <p className="text-[10.5px] text-gray-500 font-medium leading-relaxed">
                {insight.recommendation}
              </p>
            </div>
          </div>
        )}

        {/* Expand / collapse metadata */}
        {hasMetadata && (
          <div className="pl-[2.375rem]">
            <button
              onClick={toggleExpanded}
              aria-expanded={expanded}
              aria-controls={`metadata-${insight.id}`}
              className="flex items-center gap-1.5 text-[10px] font-semibold text-gray-600 hover:text-gray-400 transition-colors uppercase tracking-widest focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20 rounded"
            >
              {expanded ? (
                <>
                  <ChevronUp className="h-3 w-3" aria-hidden="true" />
                  Hide details
                </>
              ) : (
                <>
                  <ChevronDown className="h-3 w-3" aria-hidden="true" />
                  Show details
                </>
              )}
            </button>

            <AnimatePresence>
              {expanded && (
                <motion.div
                  id={`metadata-${insight.id}`}
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2, ease: 'easeOut' }}
                  className="overflow-hidden"
                >
                  <div className="pt-3 border-t border-white/[0.04] mt-3">
                    <MetadataTable metadata={insight.metadata} />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
    </motion.div>
  )
})
