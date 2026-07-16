import { Zap, AlertTriangle, Sparkles, ArrowRight, BrainCircuit } from "lucide-react"

const insights = [
  {
    id: 1,
    title: "Unusual Subscription Spike",
    description: "AWS bill is 40% higher than your trailing 6-month average.",
    icon: AlertTriangle,
    color: "text-amber-500",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    impact: "-₹12,400",
    confidence: "98%",
    category: "High Priority",
    reasoning: "We detected 3 new EC2 instances spun up last week."
  },
  {
    id: 2,
    title: "Optimization Opportunity",
    description: "Switching idle cash to the Liquid Fund yields better returns.",
    icon: Sparkles,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    impact: "+₹4,200/mo",
    confidence: "92%",
    category: "Action",
    reasoning: "₹5L has been sitting in savings earning only 2.5% for 90 days."
  },
  {
    id: 3,
    title: "Tax Optimization",
    description: "Max out your ELSS to save on 80C limits before March.",
    icon: Zap,
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/30",
    impact: "+₹46,800",
    confidence: "99%",
    category: "Action",
    reasoning: "You still have ₹1.2L room in your 80C bracket."
  }
]

export function RightSidebar() {
  return (
    <div className="os-card flex flex-col group relative overflow-hidden w-full h-full">
      <div className="flex flex-row items-center justify-between border-b border-white/[0.04] pb-3 pt-4 px-5 relative z-10">
        <div className="flex items-center gap-2">
          <BrainCircuit className="h-3 w-3 text-cyan-400 animate-pulse" />
          <h2 className="typo-subheading">Auditor Inbox</h2>
        </div>
        <span className="flex items-center gap-1 typo-badge text-[8px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-sm border border-emerald-500/20">
          3 Active
        </span>
      </div>

      <div className="relative z-10 flex-grow flex flex-col divide-y divide-white/[0.03]">
        {insights.map((insight) => {
          const Icon = insight.icon
          const isAlert = insight.category === "High Priority"
          
          return (
            <div 
              key={insight.id} 
              className="group/insight relative flex flex-col px-5 py-4 bg-transparent hover:bg-white/[0.02] transition-all duration-200 cursor-pointer overflow-hidden"
            >
              
              {/* Linear-style slide-in left border */}
              <div className="absolute left-0 top-0 bottom-0 w-[2px] opacity-0 group-hover/insight:opacity-100 transition-opacity duration-200" style={{ backgroundColor: insight.color.replace('text-', '') }} />
              
              <div className="flex items-start justify-between mb-1.5 relative z-10">
                <div className="flex items-center gap-2">
                  <Icon className={`h-3.5 w-3.5 ${insight.color}`} />
                  <h3 className="text-[12px] font-semibold text-white tracking-tight">{insight.title}</h3>
                </div>
                <span className={`text-[8px] font-semibold uppercase tracking-widest px-1.5 py-0.5 rounded-sm border ${isAlert ? 'text-amber-500 border-amber-500/20 bg-amber-500/10' : 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10'}`}>
                  {insight.category}
                </span>
              </div>
              
              <div className="relative z-10 mb-3 pl-6">
                <p className="text-[11px] text-gray-400 font-medium leading-relaxed">{insight.description}</p>
                <div className="mt-1.5 text-[10px] text-gray-500 font-medium italic border-l border-white/10 pl-2 py-0.5">
                  {insight.reasoning}
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 pl-6 relative z-10">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1.5">
                    <span className="typo-badge text-gray-600">Impact</span>
                    <span className={`text-[11px] font-semibold ${insight.color} tracking-tight`}>{insight.impact}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="typo-badge text-gray-600">Conf</span>
                    <span className="text-[11px] font-semibold text-white tabular-nums">{insight.confidence}</span>
                  </div>
                </div>
                
                <button className="opacity-0 group-hover/insight:opacity-100 flex items-center gap-1 text-[9px] font-semibold text-gray-400 hover:text-white transition-all uppercase tracking-widest">
                  Resolve <ArrowRight className="h-3 w-3" />
                </button>
              </div>

            </div>
          )
        })}
      </div>
    </div>
  )
}
