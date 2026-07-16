import { ArrowRight, FileText, Edit2 } from "lucide-react"
import type { DashboardSummary } from "@/services/dashboardService"

interface RecentTransactionsProps {
  summary: DashboardSummary
}

export function RecentTransactions({ summary }: RecentTransactionsProps) {
  const transactions = summary.recentTransactions
  return (
    <div className="os-card flex flex-col group relative overflow-hidden w-full h-full">
      <div className="flex flex-row items-center justify-between border-b border-white/[0.04] pb-3 pt-4 px-5 relative z-10">
        <div>
          <h2 className="typo-subheading">Recent Activity</h2>
        </div>
        <button className="flex items-center gap-1 typo-badge text-[9px] text-gray-500 hover:text-white transition-colors uppercase bg-white/[0.02] hover:bg-white/[0.05] px-2 py-1 rounded-md border border-white/[0.02]">
          View All <ArrowRight className="h-3 w-3" />
        </button>
      </div>
      
      <div className="p-0 relative z-10 flex-grow">
        <div className="divide-y divide-white/[0.03]">
          {transactions.map((tx) => {
            const isIncome = tx.type === "income"
            return (
              <div key={tx.id} className="relative flex items-center justify-between p-3.5 px-5 hover:bg-[#12141a] transition-colors group/row cursor-pointer overflow-hidden">
                {/* Swipe-like Action Background */}
                <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-white/[0.03] to-transparent opacity-0 group-hover/row:opacity-100 transition-opacity duration-300 pointer-events-none" />
                
                <div className="flex items-center gap-4 relative z-10">
                  <div 
                    className="flex h-9 w-9 items-center justify-center rounded-[8px] text-sm font-semibold shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] border border-white/[0.05]"
                    style={{ backgroundColor: `${tx.color}20`, color: tx.color }}
                  >
                    {tx.logo}
                  </div>
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <p className="text-[12px] font-semibold text-white tracking-tight leading-none">{tx.merchant}</p>
                      {tx.status === "Pending" && <span className="typo-badge text-[7px] bg-white/[0.05] border border-white/[0.05] text-gray-400 px-1 py-0.5 rounded-sm leading-none">Pending</span>}
                    </div>
                    <div className="flex items-center gap-1.5 typo-caption text-[10px]">
                      <span>{tx.category}</span>
                      <span className="text-gray-600">•</span>
                      <span>{new Date(tx.date).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-4 text-right relative z-10">
                  <div className="flex items-center gap-1.5 opacity-0 group-hover/row:opacity-100 transition-all duration-300 transform translate-x-4 group-hover/row:translate-x-0">
                    <button className="p-1.5 bg-white/[0.02] hover:bg-white/[0.08] border border-white/[0.05] rounded-md text-gray-400 hover:text-white transition-colors shadow-sm"><FileText className="h-3 w-3" /></button>
                    <button className="p-1.5 bg-white/[0.02] hover:bg-white/[0.08] border border-white/[0.05] rounded-md text-gray-400 hover:text-white transition-colors shadow-sm"><Edit2 className="h-3 w-3" /></button>
                  </div>
                  <span className={`text-[13px] font-semibold tabular-nums tracking-[-0.02em] ${isIncome ? 'text-emerald-400' : 'text-white'}`}>
                    {isIncome ? '+' : '-'}₹{Math.abs(tx.amount).toLocaleString('en-IN')}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
