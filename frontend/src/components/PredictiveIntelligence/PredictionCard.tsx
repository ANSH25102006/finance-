/**
 * components/PredictiveIntelligence/PredictionCard.tsx
 * Individual prediction card.
 */

import { memo } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  Activity,
  Target,
  CreditCard,
  Banknote,
  PiggyBank,
  ShieldAlert
} from 'lucide-react'
import type { Prediction } from '@/services/predictionService'

interface PredictionCardProps {
  prediction: Prediction
  onClick: (prediction: Prediction) => void
  index?: number
}

// Icon mapping based on prediction type
const ICON_MAP: Record<string, React.ElementType> = {
  CASHFLOW: Wallet,
  SPENDING: Activity,
  BUDGET: TrendingDown,
  GOAL: Target,
  SUBSCRIPTION: CreditCard,
  INCOME: Banknote,
  CATEGORY: PiggyBank,
  EMERGENCY_FUND: ShieldAlert,
}

export const PredictionCard = memo(function PredictionCard({
  prediction,
  onClick,
  index = 0,
}: PredictionCardProps) {
  const Icon = ICON_MAP[prediction.type] || TrendingUp
  
  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: prediction.forecast_currency, maximumFractionDigits: 0 }).format(val)

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05, ease: 'easeOut' }}
      className="group relative flex flex-col bg-[#0b0c10] border border-white/[0.04] rounded-[16px] p-4 cursor-pointer focus-within:outline-none transition-all duration-300 hover:bg-white/[0.02] hover:border-white/[0.08]"
      style={{ boxShadow: `inset 0 1px 0 rgba(255,255,255,0.05), 0 1px 3px rgba(0,0,0,0.4)` }}
      onClick={() => onClick(prediction)}
      tabIndex={0}
      role="button"
      aria-label={`View prediction: ${prediction.title}`}
      onKeyDown={(e) => e.key === 'Enter' && onClick(prediction)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-fuchsia-500/10 border border-fuchsia-500/20 flex items-center justify-center">
            <Icon className="h-4 w-4 text-fuchsia-400" />
          </div>
          <div>
            <h4 className="text-[13px] font-semibold text-white tracking-tight leading-snug">
              {prediction.title}
            </h4>
            <span className="text-[10px] text-gray-500 font-medium">
              {prediction.forecast_period.replace('_', ' ')}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[15px] font-bold text-white tabular-nums">
            {formatCurrency(prediction.forecast_value)}
          </div>
        </div>
      </div>
      
      <p className="text-[11.5px] text-gray-400 font-medium leading-relaxed line-clamp-2 mb-3">
        {prediction.summary}
      </p>

      <div className="mt-auto flex items-center justify-between pt-3 border-t border-white/[0.04]">
        <div className="flex flex-col gap-0.5">
          <span className="text-[9px] uppercase tracking-widest text-gray-500 font-semibold">Confidence</span>
          <span className={`text-[10px] font-bold uppercase ${
            prediction.confidence === 'HIGH' ? 'text-emerald-400' :
            prediction.confidence === 'MEDIUM' ? 'text-amber-400' : 'text-red-400'
          }`}>
            {prediction.confidence}
          </span>
        </div>
        
        <div className="flex flex-col gap-0.5 items-end text-right">
          <span className="text-[9px] uppercase tracking-widest text-gray-500 font-semibold">Methodology</span>
          <span className="text-[10px] font-semibold text-gray-300 truncate max-w-[120px]">
            {prediction.methodology}
          </span>
        </div>
      </div>
    </motion.div>
  )
})
