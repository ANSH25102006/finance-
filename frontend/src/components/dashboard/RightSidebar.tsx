import { Zap, AlertTriangle, Sparkles, ArrowRight, Activity, CheckCircle2 } from "lucide-react"
import { useInsights } from "@/hooks/useInsights"

export function RightSidebar() {
  const { data: insights = [], isLoading } = useInsights()

  return (
    <div className="os-card flex flex-col group relative overflow-hidden w-full h-full">
      <div className="flex flex-row items-center justify-between border-b border-white/[0.04] pb-3 pt-4 px-5 relative z-10">
        <div className="flex items-center gap-2">
          <Activity className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
          <h2 className="typo-subheading">Auditor Inbox</h2>
        </div>
        <span className="flex items-center gap-1 typo-badge text-[8px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-sm border border-emerald-500/20">
          {insights.length} Active
        </span>
      </div>

      <div className="relative z-10 flex-grow flex flex-col divide-y divide-white/[0.03] overflow-y-auto max-h-[420px]">
        {isLoading ? (
          <div className="p-12 flex flex-col items-center justify-center text-center text-gray-500">
            <Activity className="h-6 w-6 text-emerald-500 animate-spin mb-2" />
            <span className="text-[10px] uppercase tracking-widest">Evaluating Insights...</span>
          </div>
        ) : insights.length === 0 ? (
          <div className="p-10 flex flex-col items-center justify-center text-center text-gray-500 my-auto">
            <CheckCircle2 className="h-8 w-8 text-emerald-500/40 mb-3" />
            <p className="text-xs font-semibold text-gray-300">Auditor Inbox Clean</p>
            <p className="text-[10px] text-gray-500 max-w-[220px] mt-1 leading-normal">
              No financial risks or anomalies detected in your transaction ledger.
            </p>
          </div>
        ) : (
          insights.slice(0, 5).map((insight) => {
            const isCritical = insight.severity === "CRITICAL"
            const isWarning = insight.severity === "WARNING"

            const Icon = isCritical ? AlertTriangle : isWarning ? Zap : Sparkles
            const badgeColor = isCritical
              ? "text-red-400 border-red-500/20 bg-red-500/10"
              : isWarning
              ? "text-amber-400 border-amber-500/20 bg-amber-500/10"
              : "text-emerald-400 border-emerald-500/20 bg-emerald-500/10"
            const iconColor = isCritical ? "text-red-400" : isWarning ? "text-amber-400" : "text-emerald-400"

            return (
              <div
                key={insight.id}
                className="group/insight relative flex flex-col px-5 py-4 bg-transparent hover:bg-white/[0.02] transition-all duration-200 cursor-pointer overflow-hidden"
              >
                <div className="flex items-start justify-between mb-1.5 relative z-10">
                  <div className="flex items-center gap-2">
                    <Icon className={`h-3.5 w-3.5 ${iconColor}`} />
                    <h3 className="text-[12px] font-semibold text-white tracking-tight">{insight.title}</h3>
                  </div>
                  <span className={`text-[8px] font-semibold uppercase tracking-widest px-1.5 py-0.5 rounded-sm border ${badgeColor}`}>
                    {insight.severity}
                  </span>
                </div>

                <div className="relative z-10 mb-3 pl-6">
                  <p className="text-[11px] text-gray-400 font-medium leading-relaxed">{insight.summary}</p>
                  {insight.recommendation && (
                    <div className="mt-1.5 text-[10px] text-gray-500 font-medium italic border-l border-white/10 pl-2 py-0.5">
                      {insight.recommendation}
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2 pl-6 relative z-10">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1.5">
                      <span className="typo-badge text-gray-600">Category</span>
                      <span className="text-[10px] font-semibold text-gray-300 tracking-tight">{insight.category || "General"}</span>
                    </div>
                  </div>

                  <span className="flex items-center gap-1 text-[9px] font-semibold text-gray-400 hover:text-white transition-all uppercase tracking-widest">
                    Details <ArrowRight className="h-3 w-3" />
                  </span>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
