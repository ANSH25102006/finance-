import { ProgressRing } from "@/components/ui/ProgressRing"
import { ShieldCheck } from "lucide-react"
import { motion } from "framer-motion"
import type { DashboardSummary } from "@/services/dashboardService"

interface FinancialHealthProps {
  summary: DashboardSummary
}

export function FinancialHealth({ summary }: FinancialHealthProps) {
  const health = summary.financialHealth
  
  let healthText = "Needs Work"
  if (health >= 80) healthText = "Excellent"
  else if (health >= 60) healthText = "Good"
  else if (health >= 40) healthText = "Fair"

  return (
    <div className="flex flex-col justify-center items-center relative w-full h-full overflow-hidden group">
      
      <div className="relative z-10 flex flex-col items-center">
        <h2 className="text-[11px] font-bold tracking-[0.2em] text-gray-500 uppercase mb-8">Health Score</h2>
        
        <div className="relative mb-8">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 bg-emerald-500/10 blur-[40px] group-hover:blur-[60px] transition-all duration-700 pointer-events-none rounded-full" />
          
          <ProgressRing progress={health} size={140} strokeWidth={4} color="#34d399" trackColor="rgba(255,255,255,0.03)">
            <div className="flex flex-col items-center justify-center pt-2">
              <span className="text-4xl font-semibold tracking-[-0.04em] text-white tabular-nums drop-shadow-md">{Math.round(health)}</span>
              <span className="text-[9px] font-bold text-emerald-400 uppercase tracking-widest mt-1">{healthText}</span>
            </div>
          </ProgressRing>
          
          <motion.div 
            className="absolute -bottom-1 -right-1 bg-[#0c0e12] border border-emerald-500/20 p-2 rounded-full shadow-[0_0_15px_rgba(52,211,153,0.2)]"
            whileHover={{ scale: 1.1 }}
          >
            <ShieldCheck className="h-3 w-3 text-emerald-400" />
          </motion.div>
        </div>

        <div className="w-full flex items-center justify-between px-4">
          <div className="flex flex-col items-center">
            <span className="text-[9px] font-bold text-gray-600 uppercase tracking-widest">Savings</span>
            <span className="text-[11px] font-semibold text-white mt-1 tabular-nums">42%</span>
          </div>
          <div className="h-6 w-px bg-white/[0.05]" />
          <div className="flex flex-col items-center">
            <span className="text-[9px] font-bold text-gray-600 uppercase tracking-widest">Debt</span>
            <span className="text-[11px] font-semibold text-white mt-1 tabular-nums">12%</span>
          </div>
        </div>
      </div>
    </div>
  )
}
