/**
 * components/SavingsSimulator/SavingsSimulatorPanel.tsx
 * The main panel for running what-if savings scenarios.
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useMutation } from '@tanstack/react-query'
import {
  Calculator,
  ArrowRight,
  TrendingUp,
  CreditCard,
  PieChart,
  PiggyBank,
  RefreshCw,
} from 'lucide-react'
import { runSimulation, type ScenarioType, type SimulationResult } from '@/services/simulatorService'
import { useQuery } from '@tanstack/react-query'
import { getCategories } from '@/services/categoryService'

const formatCurrency = (val: number) => 
  new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val)

export function SavingsSimulatorPanel() {
  const [scenario, setScenario] = useState<ScenarioType>('CANCEL_SUBSCRIPTION')
  const [amount, setAmount] = useState<number>(500)
  const [categoryId, setCategoryId] = useState<string>('')
  const [reductionPct, setReductionPct] = useState<number>(10)
  const [result, setResult] = useState<SimulationResult | null>(null)

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: () => getCategories(),
  })

  const expenseCategories = categories.filter((c: any) => c.type === 'expense')

  const simulationMutation = useMutation({
    mutationFn: runSimulation,
    onSuccess: (data) => {
      setResult(data)
    }
  })

  const handleRun = () => {
    let params: Record<string, unknown> = {}
    if (scenario === 'CANCEL_SUBSCRIPTION') params = { amount }
    if (scenario === 'CUSTOM_SAVINGS') params = { amount }
    if (scenario === 'REDUCE_CATEGORY_SPEND') params = { category_id: categoryId, reduction_pct: reductionPct }

    simulationMutation.mutate({ scenario, params })
  }

  return (
    <section className="os-card flex flex-col relative overflow-hidden w-full min-h-[350px]">
      <div className="flex flex-col gap-3 border-b border-white/[0.04] pb-3 pt-4 px-5">
        <div className="flex items-center gap-2">
          <Calculator className="h-4 w-4 text-emerald-400" />
          <h2 className="typo-subheading text-emerald-50">Savings Simulator</h2>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row flex-1 overflow-hidden">
        {/* Controls */}
        <div className="w-full lg:w-1/2 p-5 border-r border-white/[0.04] flex flex-col gap-5 overflow-y-auto">
          <div>
            <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2 block">
              Choose Scenario
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => { setScenario('CANCEL_SUBSCRIPTION'); setResult(null) }}
                className={`flex items-center gap-2 p-3 rounded-xl border transition-all text-left ${
                  scenario === 'CANCEL_SUBSCRIPTION' 
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-white/[0.02] border-white/[0.04] text-gray-400 hover:bg-white/[0.05]'
                }`}
              >
                <CreditCard className="h-4 w-4 flex-shrink-0" />
                <span className="text-[12px] font-medium leading-tight">Cancel Subscription</span>
              </button>
              
              <button
                onClick={() => { setScenario('REDUCE_CATEGORY_SPEND'); setResult(null) }}
                className={`flex items-center gap-2 p-3 rounded-xl border transition-all text-left ${
                  scenario === 'REDUCE_CATEGORY_SPEND' 
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-white/[0.02] border-white/[0.04] text-gray-400 hover:bg-white/[0.05]'
                }`}
              >
                <PieChart className="h-4 w-4 flex-shrink-0" />
                <span className="text-[12px] font-medium leading-tight">Reduce Category</span>
              </button>

              <button
                onClick={() => { setScenario('CUSTOM_SAVINGS'); setResult(null) }}
                className={`flex items-center gap-2 p-3 rounded-xl border transition-all text-left col-span-2 ${
                  scenario === 'CUSTOM_SAVINGS' 
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-white/[0.02] border-white/[0.04] text-gray-400 hover:bg-white/[0.05]'
                }`}
              >
                <PiggyBank className="h-4 w-4 flex-shrink-0" />
                <span className="text-[12px] font-medium leading-tight">Custom Monthly Savings</span>
              </button>
            </div>
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={scenario}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              className="space-y-4"
            >
              {(scenario === 'CANCEL_SUBSCRIPTION' || scenario === 'CUSTOM_SAVINGS') && (
                <div>
                  <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2 block">
                    Monthly Amount (₹)
                  </label>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(Number(e.target.value))}
                    className="w-full bg-[#0b0c10] border border-white/[0.08] rounded-xl px-4 py-2.5 text-white focus:border-emerald-500/50 focus:outline-none transition-colors"
                  />
                  <input
                    type="range"
                    min="100"
                    max="10000"
                    step="100"
                    value={amount}
                    onChange={(e) => setAmount(Number(e.target.value))}
                    className="w-full mt-3 accent-emerald-500"
                  />
                </div>
              )}

              {scenario === 'REDUCE_CATEGORY_SPEND' && (
                <>
                  <div>
                    <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2 block">
                      Target Category
                    </label>
                    <select
                      value={categoryId}
                      onChange={(e) => setCategoryId(e.target.value)}
                      className="w-full bg-[#0b0c10] border border-white/[0.08] rounded-xl px-4 py-2.5 text-white focus:border-emerald-500/50 focus:outline-none transition-colors"
                    >
                      <option value="">Select a category...</option>
                      {expenseCategories.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mb-2 flex justify-between block">
                      <span>Reduction Target</span>
                      <span className="text-emerald-400">{reductionPct}%</span>
                    </label>
                    <input
                      type="range"
                      min="5"
                      max="100"
                      step="5"
                      value={reductionPct}
                      onChange={(e) => setReductionPct(Number(e.target.value))}
                      className="w-full mt-1 accent-emerald-500"
                    />
                  </div>
                </>
              )}
            </motion.div>
          </AnimatePresence>

          <button
            onClick={handleRun}
            disabled={simulationMutation.isPending || (scenario === 'REDUCE_CATEGORY_SPEND' && !categoryId)}
            className="w-full mt-auto bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-emerald-100 rounded-xl px-4 py-3 font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {simulationMutation.isPending ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Calculator className="h-4 w-4" />
            )}
            Run Simulation
          </button>
        </div>

        {/* Results */}
        <div className="w-full lg:w-1/2 p-5 bg-[#0b0c10]/50 relative overflow-y-auto">
          {result ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-6"
            >
              <div className="grid grid-cols-2 gap-4">
                <div className="os-inner-panel p-4 bg-emerald-500/[0.02] border-emerald-500/10">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-500/60 mb-1">
                    Monthly Savings
                  </p>
                  <p className="text-[24px] font-bold text-emerald-400 tabular-nums">
                    {formatCurrency(result.monthly_savings)}
                  </p>
                </div>
                <div className="os-inner-panel p-4 bg-emerald-500/[0.02] border-emerald-500/10">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-500/60 mb-1">
                    Annual Impact
                  </p>
                  <p className="text-[24px] font-bold text-emerald-400 tabular-nums">
                    {formatCurrency(result.annual_savings)}
                  </p>
                </div>
              </div>

              <div>
                <p className="typo-subheading mb-3">Projected End-of-Month Balance</p>
                <div className="flex items-center justify-between p-4 rounded-[16px] bg-white/[0.02] border border-white/[0.04]">
                  <div>
                    <p className="text-[11px] text-gray-500 font-medium mb-0.5">Before</p>
                    <p className="text-[16px] font-semibold text-gray-300 tabular-nums">
                      {formatCurrency(result.projected_balance_before)}
                    </p>
                  </div>
                  <ArrowRight className="h-5 w-5 text-gray-600" />
                  <div className="text-right">
                    <p className="text-[11px] text-emerald-500/80 font-medium mb-0.5">After</p>
                    <p className="text-[18px] font-bold text-emerald-400 tabular-nums">
                      {formatCurrency(result.projected_balance_after)}
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <p className="typo-subheading mb-2">Methodology</p>
                <div className="p-3 bg-white/[0.02] border border-white/[0.04] rounded-xl">
                  <p className="text-[12px] text-gray-400 font-medium leading-relaxed">
                    {result.methodology}
                  </p>
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center text-gray-500">
              <TrendingUp className="h-8 w-8 mb-3 opacity-20" />
              <p className="text-[13px] font-semibold text-gray-400">Run a simulation</p>
              <p className="text-[11px] max-w-[200px] mt-1">
                Configure a scenario on the left and see its deterministic impact on your finances.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
