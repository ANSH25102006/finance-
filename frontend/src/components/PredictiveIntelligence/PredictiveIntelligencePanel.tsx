/**
 * components/PredictiveIntelligence/PredictiveIntelligencePanel.tsx
 * Main dashboard widget for predictive intelligence.
 */

import { useState, useMemo } from 'react'
import { AnimatePresence } from 'framer-motion'
import {
  TrendingUp,
  RefreshCw,
  Search,
  X,
  LineChart
} from 'lucide-react'
import { usePredictions } from '@/hooks/usePredictions'
import { PredictionCard } from './PredictionCard'
import { PredictionDetailsDrawer } from './PredictionDetailsDrawer'
import type { Prediction, PredictionType } from '@/services/predictionService'

function PredictionSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="bg-white/[0.02] rounded-[16px] p-4 space-y-3 border border-white/[0.02] animate-pulse">
          <div className="flex justify-between">
            <div className="h-4 w-1/2 bg-white/[0.04] rounded" />
            <div className="h-4 w-1/4 bg-white/[0.04] rounded" />
          </div>
          <div className="h-3 w-3/4 bg-white/[0.03] rounded" />
          <div className="pt-2 flex justify-between border-t border-white/[0.02]">
            <div className="h-2 w-1/4 bg-white/[0.03] rounded" />
            <div className="h-2 w-1/4 bg-white/[0.03] rounded" />
          </div>
        </div>
      ))}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="h-10 w-10 rounded-full bg-fuchsia-500/10 border border-fuchsia-500/20 flex items-center justify-center mb-3">
        <LineChart className="h-5 w-5 text-fuchsia-400" />
      </div>
      <p className="text-[13px] font-semibold text-white mb-1">Insufficient Historical Data</p>
      <p className="text-[11px] text-gray-500 max-w-xs">
        Predictive models require more transaction history to generate reliable forecasts. Keep using the app!
      </p>
    </div>
  )
}

export function PredictiveIntelligencePanel() {
  const { data: predictions, isLoading, isFetching, error, refetch } = usePredictions()
  
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState<PredictionType | 'ALL'>('ALL')
  const [selectedPrediction, setSelectedPrediction] = useState<Prediction | null>(null)

  const filteredPredictions = useMemo(() => {
    let res = predictions

    if (selectedType !== 'ALL') {
      res = res.filter(p => p.type === selectedType)
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      res = res.filter(
        p => p.title.toLowerCase().includes(q) || p.summary.toLowerCase().includes(q)
      )
    }

    return res
  }, [predictions, searchQuery, selectedType])

  return (
    <>
      <section className="os-card flex flex-col relative overflow-hidden w-full min-h-[300px]">
        {/* Header */}
        <div className="flex flex-col gap-3 border-b border-white/[0.04] pb-3 pt-4 px-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-fuchsia-400" />
              <h2 className="typo-subheading text-fuchsia-50">Predictive Intelligence</h2>
            </div>
            <button
              onClick={() => refetch()}
              disabled={isLoading || isFetching}
              className="h-7 w-7 rounded-lg flex items-center justify-center text-gray-600 hover:text-white hover:bg-white/[0.05] transition-all"
            >
              <RefreshCw className={`h-3 w-3 ${isFetching ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-600" />
              <input
                type="text"
                placeholder="Search forecasts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-7 pr-3 py-1.5 rounded-lg text-[11px] bg-white/[0.02] border border-white/[0.06] text-white focus:outline-none focus:border-white/20 transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value as PredictionType | 'ALL')}
              className="px-2 py-1.5 rounded-lg text-[11px] font-medium bg-white/[0.02] border border-white/[0.06] text-gray-300 focus:outline-none focus:border-white/20"
            >
              <option value="ALL">All Types</option>
              <option value="CASHFLOW">Cash Flow</option>
              <option value="SPENDING">Spending</option>
              <option value="BUDGET">Budgets</option>
              <option value="GOAL">Goals</option>
            </select>
          </div>
        </div>

        {/* Body */}
        <div className="p-5">
          {isLoading ? (
            <PredictionSkeleton />
          ) : error ? (
            <div className="text-center text-[12px] text-red-400 py-10">Failed to load predictive models.</div>
          ) : filteredPredictions.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <AnimatePresence>
                {filteredPredictions.map((prediction, idx) => (
                  <PredictionCard 
                    key={prediction.id} 
                    prediction={prediction} 
                    onClick={setSelectedPrediction} 
                    index={idx}
                  />
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </section>

      <PredictionDetailsDrawer 
        prediction={selectedPrediction} 
        onClose={() => setSelectedPrediction(null)} 
      />
    </>
  )
}
