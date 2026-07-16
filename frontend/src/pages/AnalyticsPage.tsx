import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  RefreshCw,
  Award
} from "lucide-react"
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell,
  Pie,
  PieChart
} from "recharts"

import { Navbar } from "@/components/dashboard/Navbar"
import { 
  getAnalyticsDashboard,
  getAnalyticsMonthlyTrends,
  getAnalyticsCategoryBreakdown,
  getAnalyticsTopMerchants,
  getAnalyticsLargestExpenses,
  getAnalyticsDailySpending,
  getAnalyticsSpendingTrend,
  getAnalyticsFinancialHealth
} from "@/services/analyticsService"

// Category Colors fallback
const CATEGORY_COLORS = [
  "#10b981", "#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b",
  "#ef4444", "#06b6d4", "#14b8a6", "#a855f7", "#6366f1"
]

export default function AnalyticsPage() {
  const [activePieIndex, setActivePieIndex] = useState(0)

  // 1. Dashboard summary
  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: getAnalyticsDashboard,
  })

  // 2. Monthly trends
  const { data: trends = [] } = useQuery({
    queryKey: ["analytics", "monthly-trends"],
    queryFn: getAnalyticsMonthlyTrends,
  })

  // 3. Category breakdown
  const { data: categoryData = [] } = useQuery({
    queryKey: ["analytics", "category-breakdown"],
    queryFn: getAnalyticsCategoryBreakdown,
  })

  // 4. Top merchants
  const { data: topMerchants = [] } = useQuery({
    queryKey: ["analytics", "top-merchants"],
    queryFn: getAnalyticsTopMerchants,
  })

  // 5. Largest expenses
  const { data: largestExpenses = [] } = useQuery({
    queryKey: ["analytics", "largest-expenses"],
    queryFn: getAnalyticsLargestExpenses,
  })

  // 6. Daily spending
  const { data: dailySpending = [] } = useQuery({
    queryKey: ["analytics", "daily-spending"],
    queryFn: getAnalyticsDailySpending,
  })

  // 7. Spending trends
  const { data: spendingTrend } = useQuery({
    queryKey: ["analytics", "spending-trend"],
    queryFn: getAnalyticsSpendingTrend,
  })

  // 8. Financial health
  const { data: health } = useQuery({
    queryKey: ["analytics", "financial-health"],
    queryFn: getAnalyticsFinancialHealth,
  })

  const isLoading = loadingSummary

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#060709] text-emerald-500">
        <div className="text-sm uppercase tracking-widest font-mono flex items-center gap-2">
          <RefreshCw className="h-4 w-4 animate-spin" /> Load Analytics Engine...
        </div>
      </div>
    )
  }

  // Formatting helper
  const formatCurrency = (val: number) => {
    return `₹${val.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  // Prepare heatmap data: last 20 weeks (140 days)
  const renderHeatmap = () => {
    const daysToShow = 140
    const cells = []
    const today = new Date()
    today.setHours(0,0,0,0)
    
    // Mapping of date ISO string -> spend amount
    const dailySpendMap = new Map(dailySpending.map(d => [d.date, d.total_spend]))

    for (let i = daysToShow - 1; i >= 0; i--) {
      const d = new Date()
      d.setDate(today.getDate() - i)
      d.setHours(0,0,0,0)
      const dateStr = d.toISOString().split("T")[0]
      const spend = dailySpendMap.get(dateStr) || 0

      let colorClass = "bg-white/[0.02] border-white/[0.01]"
      if (spend > 0) {
        if (spend < 1000) colorClass = "bg-emerald-500/10 border-emerald-500/5"
        else if (spend < 5000) colorClass = "bg-emerald-500/30 border-emerald-500/10"
        else if (spend < 15000) colorClass = "bg-emerald-500/60 border-emerald-500/20"
        else colorClass = "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)] border-emerald-400/30"
      }

      cells.push(
        <div 
          key={dateStr} 
          className={`h-2.5 w-2.5 rounded-[2px] border ${colorClass} transition-all duration-300 hover:scale-125 cursor-pointer`}
          title={`${d.toLocaleDateString("en-IN")}: ${formatCurrency(spend)}`}
        />
      )
    }
    return cells
  }

  // Pie chart helper
  const PieComponent = Pie as any
  const pieChartData = categoryData.map((c, index) => ({
    name: c.category_name,
    value: c.total_amount,
    percentage: c.percentage,
    color: CATEGORY_COLORS[index % CATEGORY_COLORS.length]
  }))

  const activeCategory = pieChartData[activePieIndex] || { name: "None", value: 0, percentage: 0 }

  return (
    <div className="relative min-h-screen bg-[#060709] text-white selection:bg-emerald-500/30 overflow-hidden">
      {/* Subtle Ambient Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-900/5 mesh-blob" />
        <div className="absolute top-[30%] right-[-15%] w-[45%] h-[55%] rounded-full bg-cyan-900/5 mesh-blob" style={{ animationDelay: '-5s' }} />
        <div className="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] rounded-full bg-purple-900/5 mesh-blob" style={{ animationDelay: '-10s' }} />
        <div className="absolute inset-0 bg-noise" />
      </div>

      <Navbar />

      <main className="relative z-10 mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8 pb-32 pt-28">
        
        {/* Header */}
        <div className="border-b border-white/5 pb-6">
          <h1 className="typo-display text-2xl font-bold">Financial Analytics</h1>
          <p className="typo-body text-gray-500 mt-1">Deep computational breakdown of cashflow and health metrics</p>
        </div>

        {/* row 1: Key Summary stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mt-6">
          
          {/* Card: Balance */}
          <div className="os-card p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="typo-subheading">Net Portfolio Value</span>
              <DollarSign className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="mt-4">
              <h3 className="text-xl font-bold tabular-nums">{formatCurrency(summary?.current_balance || 0)}</h3>
              <p className="typo-caption text-gray-500 mt-1">Total account liquidity</p>
            </div>
          </div>

          {/* Card: Income */}
          <div className="os-card p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="typo-subheading">Total Income Received</span>
              <TrendingUp className="h-4 w-4 text-emerald-500" />
            </div>
            <div className="mt-4">
              <h3 className="text-xl font-bold tabular-nums text-emerald-400">{formatCurrency(summary?.total_income || 0)}</h3>
              <p className="typo-caption text-gray-500 mt-1">All-time cash inflow</p>
            </div>
          </div>

          {/* Card: Expenses */}
          <div className="os-card p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="typo-subheading">Total Expenses Incurred</span>
              <TrendingDown className="h-4 w-4 text-cyan-400" />
            </div>
            <div className="mt-4">
              <h3 className="text-xl font-bold tabular-nums">{formatCurrency(summary?.total_expenses || 0)}</h3>
              <p className="typo-caption text-gray-500 mt-1">All-time cash outflow</p>
            </div>
          </div>

          {/* Card: Net Flow */}
          <div className="os-card p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="typo-subheading">Aggregate Net Flow</span>
              <Activity className="h-4 w-4 text-purple-400" />
            </div>
            <div className="mt-4">
              <h3 className={`text-xl font-bold tabular-nums ${(summary?.net_cash_flow || 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {formatCurrency(summary?.net_cash_flow || 0)}
              </h3>
              <p className="typo-caption text-gray-500 mt-1">Difference in net inflow/outflow</p>
            </div>
          </div>

        </div>

        {/* Row 2: Health Score Widget & Cash flow Chart */}
        <div className="grid grid-cols-12 gap-5 mt-6">
          
          {/* Health Score */}
          <div className="col-span-12 lg:col-span-4 os-card p-6 flex flex-col justify-between border border-white/5">
            <div>
              <div className="flex items-center justify-between">
                <h3 className="typo-heading text-sm font-semibold">Financial Health</h3>
                <Award className="h-4 w-4 text-amber-500" />
              </div>
              <p className="typo-caption text-gray-500 mt-0.5">Algorithm computed scorecard</p>
            </div>

            <div className="flex flex-col items-center justify-center py-6">
              <div className="relative flex items-center justify-center">
                {/* Score circle */}
                <svg className="w-28 h-28 transform -rotate-90">
                  <circle
                    cx="56"
                    cy="56"
                    r="48"
                    className="stroke-white/[0.02]"
                    strokeWidth="8"
                    fill="transparent"
                  />
                  <circle
                    cx="56"
                    cy="56"
                    r="48"
                    className="stroke-emerald-500 transition-all duration-1000"
                    strokeWidth="8"
                    fill="transparent"
                    strokeDasharray={301.6}
                    strokeDashoffset={301.6 - (301.6 * (health?.score || 0)) / 100}
                    style={{ filter: "drop-shadow(0 0 8px rgba(16,185,129,0.4))" }}
                  />
                </svg>
                <div className="absolute flex flex-col items-center">
                  <span className="text-3xl font-extrabold tracking-tight tabular-nums text-white">{health?.score || 0}</span>
                  <span className="text-[9px] uppercase tracking-widest text-emerald-400 font-bold mt-0.5">{health?.rating}</span>
                </div>
              </div>
            </div>

            <div className="space-y-2 border-t border-white/5 pt-4">
              <span className="typo-subheading text-[8px] text-gray-500">Calculated Metrics Feedback:</span>
              <ul className="space-y-1.5 mt-2">
                {(health?.explanations || []).map((exp, idx) => (
                  <li key={idx} className="typo-body text-[10px] text-gray-400 leading-snug flex items-start gap-1.5">
                    <span className="h-1 w-1 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                    {exp}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Cashflow Velocity Chart */}
          <div className="col-span-12 lg:col-span-8 os-card p-6 border border-white/5">
            <div className="flex flex-row items-center justify-between mb-8">
              <div>
                <h3 className="typo-heading text-sm font-semibold">Cash Flow Trends</h3>
                <p className="typo-caption text-gray-500 mt-0.5">Trailing monthly liquidity velocity</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1 typo-badge text-[8px] text-emerald-400"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Income</div>
                <div className="flex items-center gap-1 typo-badge text-[8px] text-cyan-400"><span className="h-1.5 w-1.5 rounded-full bg-cyan-400" /> Expense</div>
              </div>
            </div>
            
            <div className="w-full h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="incGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="expGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.02)" />
                  <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: "#4b5563" }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: "#4b5563" }} tickFormatter={(val) => `₹${val / 1000}k`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0c0e12", border: "1px solid rgba(255,255,255,0.05)", borderRadius: "8px" }}
                    labelStyle={{ fontSize: "9px", color: "#6b7280", textTransform: "uppercase" }}
                    itemStyle={{ fontSize: "11px", fontWeight: 500 }}
                  />
                  <Area type="monotone" dataKey="income" stroke="#10b981" fillOpacity={1} fill="url(#incGrad)" strokeWidth={2} />
                  <Area type="monotone" dataKey="expense" stroke="#06b6d4" fillOpacity={1} fill="url(#expGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>

        {/* Row 3: Category Breakdown & Top Statistics */}
        <div className="grid grid-cols-12 gap-5 mt-6">

          {/* Donut Category spending */}
          <div className="col-span-12 lg:col-span-5 os-card p-6 flex flex-col justify-between border border-white/5">
            <div>
              <h3 className="typo-heading text-sm font-semibold">Category Allocations</h3>
              <p className="typo-caption text-gray-500 mt-0.5">Top expense sectors</p>
            </div>

            <div className="flex-grow flex items-center justify-center py-4 relative">
              {categoryData.length === 0 ? (
                <span className="typo-body text-gray-600">No categories calculated</span>
              ) : (
                <>
                  <div className="w-48 h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart data={pieChartData} style={{ outline: "none" }}>
                        <PieComponent
                          data={pieChartData}
                          cx="50%"
                          cy="50%"
                          innerRadius={65}
                          outerRadius={80}
                          paddingAngle={3}
                          dataKey="value"
                          stroke="none"
                          activeIndex={activePieIndex}
                          onMouseEnter={(_: any, idx: number) => setActivePieIndex(idx)}
                          animationDuration={1000}
                        >
                          {pieChartData.map((entry, idx) => (
                            <Cell key={idx} fill={entry.color} fillOpacity={activePieIndex === idx ? 1 : 0.3} />
                          ))}
                        </PieComponent>
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="absolute flex flex-col items-center pointer-events-none">
                    <span className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold">{activeCategory.name}</span>
                    <span className="text-xl font-bold tabular-nums text-white mt-0.5">{activeCategory.percentage}%</span>
                  </div>
                </>
              )}
            </div>

            <div className="divide-y divide-white/[0.02]">
              {pieChartData.slice(0, 4).map((item, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-gray-400 font-medium">{item.name}</span>
                  </div>
                  <span className="font-semibold text-white font-mono tabular-nums">{formatCurrency(item.value)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Average Spending Stats & Daily Spending Heatmap */}
          <div className="col-span-12 lg:col-span-7 flex flex-col gap-5">
            
            {/* Stats Card */}
            <div className="os-card p-6 flex-grow border border-white/5">
              <h3 className="typo-heading text-sm font-semibold">Spending Statistics</h3>
              <p className="typo-caption text-gray-500 mt-0.5">Computational trends index</p>

              <div className="grid grid-cols-2 gap-6 mt-6">
                <div>
                  <span className="typo-subheading text-[8px] text-gray-500">Average Daily Spend</span>
                  <h4 className="text-xl font-bold tracking-tight text-white tabular-nums mt-1">{formatCurrency(spendingTrend?.average_daily_spend || 0)}</h4>
                  <p className="text-[10px] text-gray-500 mt-1">Calculated over the last 30 days</p>
                </div>
                
                <div>
                  <span className="typo-subheading text-[8px] text-gray-500">Average Monthly Spend</span>
                  <h4 className="text-xl font-bold tracking-tight text-white tabular-nums mt-1">{formatCurrency(spendingTrend?.average_monthly_spend || 0)}</h4>
                  <p className="text-[10px] text-gray-500 mt-1">Calculated over the last 12 months</p>
                </div>

                <div>
                  <span className="typo-subheading text-[8px] text-gray-500">Transaction Average</span>
                  <h4 className="text-xl font-bold tracking-tight text-white tabular-nums mt-1">{formatCurrency(spendingTrend?.average_transaction_amount || 0)}</h4>
                  <p className="text-[10px] text-gray-500 mt-1">Average value of all expenses</p>
                </div>

                <div>
                  <span className="typo-subheading text-[8px] text-gray-500">Transaction Median</span>
                  <h4 className="text-xl font-bold tracking-tight text-white tabular-nums mt-1">{formatCurrency(spendingTrend?.median_transaction_amount || 0)}</h4>
                  <p className="text-[10px] text-gray-500 mt-1">Midpoint value of expense transactions</p>
                </div>
              </div>
            </div>

            {/* Daily spending Heatmap */}
            <div className="os-card p-6 border border-white/5">
              <div>
                <h3 className="typo-heading text-sm font-semibold">Daily Heatmap</h3>
                <p className="typo-caption text-gray-500 mt-0.5">Previous 140 days spending frequency</p>
              </div>

              {/* Grid of cells */}
              <div className="flex flex-wrap gap-1 mt-6 justify-start">
                {renderHeatmap()}
              </div>

              <div className="flex items-center justify-end gap-1.5 mt-4 text-[9px] text-gray-500 uppercase font-mono tracking-widest">
                <span>Less</span>
                <div className="h-2 w-2 rounded-[1px] bg-white/[0.02] border border-white/[0.01]" />
                <div className="h-2 w-2 rounded-[1px] bg-emerald-500/10" />
                <div className="h-2 w-2 rounded-[1px] bg-emerald-500/30" />
                <div className="h-2 w-2 rounded-[1px] bg-emerald-500/60" />
                <div className="h-2 w-2 rounded-[1px] bg-emerald-500" />
                <span>More</span>
              </div>
            </div>

          </div>

        </div>

        {/* Row 4: Lists/Tables (Top Merchants & Largest Expenses) */}
        <div className="grid grid-cols-12 gap-5 mt-6">

          {/* Top Merchants Table */}
          <div className="col-span-12 lg:col-span-5 os-card p-6 border border-white/5">
            <h3 className="typo-heading text-sm font-semibold mb-4">Top Merchants</h3>
            {topMerchants.length === 0 ? (
              <p className="typo-body text-gray-600 mt-2">No merchant records logged</p>
            ) : (
              <div className="overflow-hidden">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-white/[0.04] text-[9px] uppercase tracking-widest text-gray-500 font-bold">
                      <th className="pb-3">Merchant</th>
                      <th className="pb-3 text-center">Transactions</th>
                      <th className="pb-3 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.02]">
                    {topMerchants.slice(0, 5).map((m, idx) => (
                      <tr key={idx} className="group hover:bg-white/[0.01] transition-colors">
                        <td className="py-3 font-semibold text-white">{m.merchant_name}</td>
                        <td className="py-3 text-center text-gray-500 font-mono">{m.transaction_count}</td>
                        <td className="py-3 text-right text-emerald-400 font-semibold font-mono tabular-nums">{formatCurrency(m.total_amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Largest Expenses Table */}
          <div className="col-span-12 lg:col-span-7 os-card p-6 border border-white/5">
            <h3 className="typo-heading text-sm font-semibold mb-4">Largest Expense Items</h3>
            {largestExpenses.length === 0 ? (
              <p className="typo-body text-gray-600 mt-2">No expense transactions logged</p>
            ) : (
              <div className="overflow-hidden">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-white/[0.04] text-[9px] uppercase tracking-widest text-gray-500 font-bold">
                      <th className="pb-3">Merchant</th>
                      <th className="pb-3">Category</th>
                      <th className="pb-3">Date</th>
                      <th className="pb-3 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.02]">
                    {largestExpenses.slice(0, 5).map((tx, idx) => (
                      <tr key={idx} className="group hover:bg-white/[0.01] transition-colors">
                        <td className="py-3">
                          <div className="flex flex-col">
                            <span className="font-semibold text-white">{tx.merchant}</span>
                            <span className="text-[10px] text-gray-500 max-w-[150px] truncate" title={tx.description}>{tx.description}</span>
                          </div>
                        </td>
                        <td className="py-3 text-gray-400">{tx.category}</td>
                        <td className="py-3 text-gray-500 font-mono">{new Date(tx.date).toLocaleDateString("en-IN")}</td>
                        <td className="py-3 text-right text-white font-semibold font-mono tabular-nums">{formatCurrency(tx.amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>

      </main>
    </div>
  )
}

