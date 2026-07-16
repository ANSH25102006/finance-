import { ArrowUpRight } from "lucide-react"
import { CountUp } from "@/components/ui/CountUp"
import { motion } from "framer-motion"
import type { DashboardSummary } from "@/services/dashboardService"

interface WelcomeHeaderProps {
  summary: DashboardSummary
}

export function WelcomeHeader({ summary }: WelcomeHeaderProps) {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className="flex flex-col items-center justify-center pt-8 pb-10 relative z-10"
    >
      
      {/* V5 Refined Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-32 bg-emerald-500/10 blur-[80px] pointer-events-none rounded-full" />
      
      <motion.div 
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.5, ease: "easeOut" }}
        className="flex items-center gap-1.5 px-3 py-1 rounded-full glass-panel mb-6 cursor-default"
      >
        <span className="relative flex h-1.5 w-1.5 items-center justify-center">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-1 w-1 bg-emerald-500"></span>
        </span>
        <span className="typo-badge text-emerald-400">System Nominal</span>
        <span className="typo-badge text-gray-500 ml-1">Syncing live</span>
      </motion.div>

      <div className="text-center relative">
        <p className="typo-subheading mb-2">Total Net Worth</p>
        <h1 className="text-5xl md:text-6xl lg:text-7xl typo-display mb-4 tabular-nums relative leading-none text-white">
          <span className="text-gray-600 font-medium mr-1 text-4xl align-top">₹</span>
          <CountUp value={summary.netWorth} duration={1.5} />
        </h1>
        
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="flex items-center justify-center gap-2"
        >
          <div className="flex items-center gap-1 typo-badge text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full backdrop-blur-md">
            <ArrowUpRight className="h-3 w-3" />
            +₹42,500 (2.4%)
          </div>
          <span className="typo-caption">vs last month</span>
        </motion.div>
      </div>

    </motion.div>
  )
}
