import { ProgressRing } from "@/components/ui/ProgressRing"
import { ArrowRight, Plane, Shield, Laptop, Home, Star } from "lucide-react"
import type { DashboardSummary } from "@/services/dashboardService"

interface BudgetProgressProps {
  summary: DashboardSummary
}

export function BudgetProgress({ summary }: BudgetProgressProps) {
  const formatCompact = (num: number) => {
    if (num >= 100000) return `₹${(num / 100000).toFixed(1)}L`
    if (num >= 1000) return `₹${(num / 1000).toFixed(1)}k`
    return `₹${num.toFixed(0)}`
  }

  // Fallback goals if none exist
  const mockGoals = [
    { title: "No Goals Set", current: 0, target: 100, percent: 0, icon: "Star", color: "#6b7280", date: "-" }
  ]
  const goals = summary.goals.length > 0 ? summary.goals : mockGoals
  return (
    <div className="os-card flex flex-col relative overflow-hidden group w-full h-full">
      <div className="flex flex-row items-center justify-between border-b border-white/[0.04] pb-3 pt-4 px-5 relative z-10">
        <div>
          <h2 className="typo-subheading">Strategic Goals</h2>
        </div>
        <button className="flex items-center gap-1 typo-badge text-[9px] text-gray-500 hover:text-white transition-colors uppercase bg-white/[0.02] hover:bg-white/[0.05] px-2 py-1 rounded-md border border-white/[0.02]">
          Manage <ArrowRight className="h-3 w-3" />
        </button>
      </div>

      <div className="p-4 relative z-10 flex-grow">
        <div className="grid grid-cols-2 gap-3 h-full">
          {goals.map((goal, idx) => {
            const iconMap: Record<string, any> = { Plane, Shield, Laptop, Home, Star }
            const IconComponent = iconMap[goal.icon] || Star
            const trackColor = `${goal.color}20` // Add 20% opacity for track
            
            return (
              <div key={idx} className="group/goal flex flex-col items-center justify-center text-center bg-transparent hover:bg-white/[0.01] border border-white/[0.02] hover:border-white/[0.06] shadow-[inset_0_1px_0_rgba(255,255,255,0.02)] rounded-xl p-3 transition-all duration-300 cursor-pointer relative overflow-hidden">
                <div className="absolute inset-0 opacity-0 group-hover/goal:opacity-20 transition-opacity duration-500 blur-[30px] pointer-events-none" style={{ backgroundColor: goal.color }} />
                
                <div className="relative z-10 mb-2.5">
                  <ProgressRing progress={goal.percent} size={48} strokeWidth={3} color={goal.color} trackColor={trackColor}>
                    <IconComponent className="h-4 w-4" style={{ color: goal.color }} />
                  </ProgressRing>
                </div>
                
                <div className="relative z-10 w-full">
                  <p className="text-[11px] font-semibold text-white tracking-tight truncate mb-1">{goal.title}</p>
                  <p className="text-[10px] font-semibold text-gray-500 tabular-nums uppercase tracking-widest flex items-center justify-center gap-1">
                    <span className="text-gray-300">{formatCompact(goal.current)}</span>
                    <span className="text-gray-600">/</span>
                    <span>{formatCompact(goal.target)}</span>
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
