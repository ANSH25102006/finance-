import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { ArrowDownRight, ArrowUpRight } from "lucide-react"
import type { DashboardSummary } from "@/services/dashboardService"

interface CashFlowChartProps {
  summary: DashboardSummary
}

export function CashFlowChart({ summary }: CashFlowChartProps) {
  // Map our backend monthlyTrend format to the chart's expected format
  const data = summary.monthlyTrend.map((t) => ({
    name: t.month,
    income: t.income,
    expenses: t.expenses
  })).reverse() // Show chronological order

  return (
    <div className="flex flex-col h-full w-full">
      <div className="flex flex-row items-center justify-between mb-8 relative z-10">
        <div>
          <h2 className="typo-heading text-[13px]">Cash Flow Velocity</h2>
          <p className="typo-body text-[11px] mt-0.5">Trailing 7-month liquidity</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 typo-badge text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded">
            <ArrowUpRight className="h-3 w-3" /> Income
          </div>
          <div className="flex items-center gap-1.5 typo-badge text-cyan-400 bg-cyan-500/10 px-2 py-1 rounded">
            <ArrowDownRight className="h-3 w-3" /> Expenses
          </div>
        </div>
      </div>

      <div className="flex-grow w-full h-[220px] relative z-10">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorIncome" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#34d399" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#34d399" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.03)" />
            <XAxis 
              dataKey="name" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fontSize: 10, fill: '#6b7280', fontWeight: 500 }} 
              dy={10} 
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fontSize: 10, fill: '#6b7280', fontWeight: 500 }}
              tickFormatter={(value) => `₹${value / 1000}k`}
              dx={-10}
            />
            <Tooltip
              contentStyle={{ 
                backgroundColor: 'rgba(11, 12, 16, 0.95)', 
                backdropFilter: 'blur(16px)', 
                borderRadius: '8px', 
                border: '1px solid rgba(255,255,255,0.05)', 
                boxShadow: '0 20px 40px rgba(0,0,0,0.8)' 
              }}
              itemStyle={{ fontSize: '11px', fontWeight: 500 }}
              labelStyle={{ color: '#9ca3af', marginBottom: '6px', fontSize: '9px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em' }}
              cursor={{ stroke: 'rgba(255,255,255,0.05)', strokeWidth: 1, strokeDasharray: '4 4' }}
              formatter={(value: any) => [`₹${Number(value).toLocaleString('en-IN')}`, undefined]}
            />
            <Area 
              type="monotone" 
              dataKey="income" 
              stroke="#34d399" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorIncome)" 
              activeDot={{ r: 5, fill: "#34d399", stroke: "#07090C", strokeWidth: 2 }}
              animationDuration={1500}
            />
            <Area 
              type="monotone" 
              dataKey="expenses" 
              stroke="#22d3ee" 
              strokeWidth={2}
              fillOpacity={1} 
              fill="url(#colorExpenses)" 
              activeDot={{ r: 5, fill: "#22d3ee", stroke: "#07090C", strokeWidth: 2 }}
              animationDuration={1500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
