import { ArrowUpRight, ArrowDownRight, Wallet, PiggyBank, CreditCard } from "lucide-react"
import { CountUp } from "@/components/ui/CountUp"
import { LineChart, Line, ResponsiveContainer } from "recharts"
import { motion } from "framer-motion"
import type { DashboardSummary } from "@/services/dashboardService"

interface FinancialOverviewProps {
  summary: DashboardSummary
}

export function FinancialOverview({ summary }: FinancialOverviewProps) {
  const formatCompact = (num: number) => {
    if (num >= 100000) return `₹${(num / 100000).toFixed(1)}L`
    if (num >= 1000) return `₹${(num / 1000).toFixed(1)}k`
    return `₹${num.toFixed(0)}`
  }

  const overviewData = [
    {
      title: "Income",
      value: summary.income.current,
      change: `${summary.income.change > 0 ? '+' : ''}${summary.income.change.toFixed(1)}%`,
      trend: summary.income.change >= 0 ? "up" : "down",
      icon: Wallet,
      color: "text-emerald-400",
      glow: "rgba(52,211,153,0.3)",
      data: summary.monthlyTrend.map(t => t.income).reverse(),
      stats: { average: formatCompact(summary.income.previous), projection: "N/A" }
    },
    {
      title: "Expenses",
      value: summary.expenses.current,
      change: `${summary.expenses.change > 0 ? '+' : ''}${summary.expenses.change.toFixed(1)}%`,
      trend: summary.expenses.change <= 0 ? "down" : "up", // Less expenses is good, but trend down arrow
      icon: CreditCard,
      color: "text-cyan-400",
      glow: "rgba(34,211,238,0.3)",
      data: summary.monthlyTrend.map(t => t.expenses).reverse(),
      stats: { average: formatCompact(summary.expenses.previous), projection: "N/A" }
    },
    {
      title: "Savings Rate",
      value: summary.savingsRate,
      suffix: "%",
      change: "0%", // Backend currently doesn't compute savings rate change, just keeping mock change
      trend: "up",
      icon: PiggyBank,
      color: "text-purple-400",
      glow: "rgba(167,139,250,0.3)",
      data: summary.monthlyTrend.map(t => ((t.income - t.expenses) / t.income) * 100 || 0).reverse(),
      stats: { average: `${summary.savingsRate.toFixed(1)}%`, projection: "N/A" }
    },
  ]

  return (
    <div className="os-card w-full relative overflow-hidden flex flex-col md:flex-row divide-y md:divide-y-0 md:divide-x divide-white/[0.04]">
      {overviewData.map((item, idx) => {
        const Icon = item.icon
        const isUp = item.trend === "up"
        
        return (
          <motion.div 
            key={idx} 
            whileHover={{ backgroundColor: "rgba(255,255,255,0.01)" }}
            className="flex-1 p-6 relative overflow-hidden group cursor-pointer transition-colors duration-500"
          >
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 blur-[40px] opacity-0 group-hover:opacity-60 transition-opacity duration-700 pointer-events-none rounded-full" style={{ backgroundColor: item.glow }} />
            
            <div className="flex items-center justify-between relative z-10 mb-6">
              <div className="flex items-center gap-2">
                <Icon className={`h-3.5 w-3.5 ${item.color}`} />
                <p className="typo-subheading">{item.title}</p>
              </div>
              <div className="flex items-center gap-1 text-[10px] font-semibold text-white bg-white/[0.03] border border-white/[0.05] px-2 py-0.5 rounded-full shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] tracking-tight">
                {isUp ? <ArrowUpRight className="h-3 w-3 text-emerald-400" /> : <ArrowDownRight className="h-3 w-3 text-cyan-400" />}
                {item.change}
              </div>
            </div>
            
            <div className="relative z-10">
              <div className="flex items-end justify-between">
                <h3 className="text-[32px] font-semibold tracking-[-0.04em] text-white tabular-nums leading-none drop-shadow-md">
                  <CountUp value={item.value} prefix={item.suffix ? "" : "₹"} suffix={item.suffix} />
                </h3>
                <div className="h-8 w-20 opacity-30 group-hover:opacity-100 transition-all duration-500 transform group-hover:translate-x-1 group-hover:-translate-y-1">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={item.data.map((val, i) => ({ val, i }))}>
                      <Line 
                        type="monotone" 
                        dataKey="val" 
                        stroke={item.color.replace('text-', '')} 
                        strokeWidth={2} 
                        dot={false} 
                        isAnimationActive={true} 
                        animationDuration={1500}
                        style={{ filter: `drop-shadow(0 2px 4px ${item.glow})` }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
              
              <div className="flex items-center gap-4 mt-6 pt-4 border-t border-white/[0.03]">
                <div className="flex items-baseline gap-1.5">
                  <span className="typo-badge text-gray-600">Avg</span>
                  <span className="text-[11px] font-semibold text-gray-400">{item.stats.average}</span>
                </div>
                <div className="flex items-baseline gap-1.5">
                  <span className="typo-badge text-gray-600">Proj</span>
                  <span className="text-[11px] font-semibold text-gray-400">{item.stats.projection}</span>
                </div>
              </div>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
