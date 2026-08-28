/**
 * components/FinancialTimeline/TimelineCard.tsx
 * Individual timeline event card in the vertical list.
 */

import { memo } from 'react'
import { motion } from 'framer-motion'
import {
  Banknote,
  ShoppingCart,
  Undo2,
  TrendingUp,
  AlertTriangle,
  CreditCard,
  ArrowUpCircle,
  Target,
  ShieldAlert,
  Wallet,
  PiggyBank,
  Activity,
  ArrowUpRight,
  CalendarDays,
  CircleDot
} from 'lucide-react'
import type { TimelineEvent } from '@/services/timelineService'
import { SEVERITY_CONFIG } from '@/components/FinancialInsights/SeverityBadge'

interface TimelineCardProps {
  event: TimelineEvent
  onClick: (event: TimelineEvent) => void
  index?: number
}

// Icon mapping based on event type
const ICON_MAP: Record<string, React.ElementType> = {
  SALARY_CREDITED: Banknote,
  LARGE_PURCHASE: ShoppingCart,
  LARGE_REFUND: Undo2,
  SPENDING_SPIKE: TrendingUp,
  BUDGET_WARNING: AlertTriangle,
  SUBSCRIPTION_DETECTED: CreditCard,
  PRICE_INCREASE: ArrowUpCircle,
  GOAL_MILESTONE: Target,
  EMERGENCY_FUND_MILESTONE: ShieldAlert,
  CASHFLOW_WARNING: Wallet,
  SAVINGS_OPPORTUNITY: PiggyBank,
  CATEGORY_TREND: Activity,
  LIFESTYLE_INFLATION: ArrowUpRight,
  MONTHLY_COMPARISON: CalendarDays,
}

export const TimelineCard = memo(function TimelineCard({
  event,
  onClick,
  index = 0,
}: TimelineCardProps) {
  const cfg = SEVERITY_CONFIG[event.severity]
  const Icon = ICON_MAP[event.type] || CircleDot

  const relativeTime = (iso: string) => {
    try {
      const date = new Date(iso)
      const now = new Date()
      
      // If it's today, return time
      if (date.toDateString() === now.toDateString()) {
        return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
      }
      
      // Otherwise return date
      return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
    } catch {
      return ''
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05, ease: 'easeOut' }}
      className="group relative flex gap-4 cursor-pointer focus-within:outline-none"
      onClick={() => onClick(event)}
      tabIndex={0}
      role="button"
      aria-label={`View timeline event: ${event.title}`}
      onKeyDown={(e) => e.key === 'Enter' && onClick(event)}
    >
      {/* Timeline vertical line (behind the dot) */}
      <div className="absolute left-[15px] top-8 bottom-[-16px] w-[2px] bg-white/[0.04] group-last:hidden" />

      {/* Icon node */}
      <div className="relative z-10 flex-shrink-0 mt-1">
        <div 
          className={`h-8 w-8 rounded-full flex items-center justify-center ${cfg.bgColor} border ${cfg.borderColor} transition-transform duration-300 group-hover:scale-110 shadow-lg`}
          style={{ boxShadow: `0 0 10px ${cfg.glowColor}` }}
        >
          <Icon className={`h-4 w-4 ${cfg.textColor}`} aria-hidden="true" />
        </div>
      </div>

      {/* Content card */}
      <div 
        className="flex-1 bg-[#0b0c10] border border-white/[0.04] rounded-[16px] p-3.5 transition-all duration-300 group-hover:bg-white/[0.02] group-hover:border-white/[0.08]"
        style={{ boxShadow: `inset 0 1px 0 rgba(255,255,255,0.05), 0 1px 3px rgba(0,0,0,0.4)` }}
      >
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <h4 className="text-[13px] font-semibold text-white tracking-tight leading-snug">
            {event.title}
          </h4>
          <span className="text-[10px] text-gray-500 font-medium whitespace-nowrap">
            {relativeTime(event.timestamp)}
          </span>
        </div>
        <p className="text-[11.5px] text-gray-400 font-medium leading-relaxed line-clamp-2">
          {event.description}
        </p>
      </div>
    </motion.div>
  )
})
