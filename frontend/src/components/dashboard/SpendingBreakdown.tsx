import { useState } from "react"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Sector } from "recharts"
import { LayoutGrid } from "lucide-react"

const PieComponent = Pie as any
import type { DashboardSummary } from "@/services/dashboardService"

interface SpendingBreakdownProps {
  summary: DashboardSummary
}

const renderActiveShape = (props: any) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill } = props
  return (
    <g>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius - 3}
        outerRadius={outerRadius + 3}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        className="transition-all duration-300"
      />
    </g>
  )
}

export function SpendingBreakdown({ summary }: SpendingBreakdownProps) {
  const [activeIndex, setActiveIndex] = useState(0)

  // Fallback data if no expenses
  const defaultData = [{ name: "No Data", value: 100, color: "#4b5563", amount: "₹0" }]
  const rawData = summary.categoryBreakdown.length > 0 ? summary.categoryBreakdown : defaultData
  
  const data = rawData.map(c => ({
    name: c.name,
    value: c.value,
    color: c.color,
    amount: `₹${(c.amount || 0).toLocaleString('en-IN')}`
  }))

  const activeItem = data[activeIndex] || data[0]

  return (
    <div className="os-card flex flex-col group relative overflow-hidden w-full h-full">
      <div className="absolute top-1/2 left-1/4 w-32 h-32 bg-purple-500/10 rounded-full blur-[80px] pointer-events-none transition-all duration-700 group-hover:bg-purple-500/20" />
      
      <div className="flex flex-row items-center justify-between border-b border-white/[0.04] pb-3 pt-4 px-5 relative z-10">
        <div className="flex items-center gap-2">
          <LayoutGrid className="h-3.5 w-3.5 text-purple-400" />
          <h2 className="typo-subheading">Spending Matrix</h2>
        </div>
      </div>
      
      <div className="p-4 relative z-10 flex-grow flex items-center justify-between gap-6">
        
        {/* Chart Area */}
        <div className="w-[180px] h-[180px] relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <defs>
                <filter id="pieGlowMatrix">
                  <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                  <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                  </feMerge>
                </filter>
              </defs>
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              <PieComponent
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={65}
                outerRadius={80}
                paddingAngle={4}
                dataKey="value"
                stroke="none"
                activeIndex={activeIndex}
                activeShape={renderActiveShape}
                onMouseEnter={(_: any, index: any) => setActiveIndex(index)}
                animationDuration={1500}
                style={{ filter: 'url(#pieGlowMatrix)' }}
              >
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.color} 
                    fillOpacity={activeIndex === index ? 1 : 0.2} 
                    className="transition-all duration-300 outline-none cursor-pointer" 
                  />
                ))}
              </PieComponent>
              <Tooltip 
                contentStyle={{ backgroundColor: 'rgba(11, 12, 16, 0.95)', backdropFilter: 'blur(16px)', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', boxShadow: '0 20px 40px rgba(0,0,0,0.8)' }}
                itemStyle={{ fontSize: '11px', fontWeight: 600, padding: '2px 0' }}
                labelStyle={{ display: 'none' }}
                formatter={((value: any, name: any) => [`${value}%`, String(name).toUpperCase()]) as any}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none transition-all duration-300">
            <span className="typo-badge text-gray-500 mb-0.5">{activeItem.name}</span>
            <span className="text-[20px] font-semibold tabular-nums tracking-[-0.04em] drop-shadow-lg transition-colors duration-300" style={{ color: activeItem.color }}>
              {activeItem.value}%
            </span>
          </div>
        </div>

        {/* Legend Grid */}
        <div className="flex-1 grid grid-cols-2 gap-x-4 gap-y-3">
          {data.map((item, idx) => (
            <div 
              key={item.name} 
              className={`flex flex-col p-2.5 rounded-[10px] cursor-pointer transition-all duration-300 border ${activeIndex === idx ? 'bg-[#12141a] border-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]' : 'bg-transparent border-transparent hover:bg-white/[0.02]'}`}
              onMouseEnter={() => setActiveIndex(idx)}
            >
              <div className="flex items-center gap-2 mb-1">
                <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: item.color, boxShadow: activeIndex === idx ? `0 0 8px ${item.color}` : 'none' }} />
                <span className={`typo-badge ${activeIndex === idx ? 'text-white' : 'text-gray-500'}`}>{item.name}</span>
              </div>
              <div className="flex items-end gap-2 pl-3.5">
                <span className="text-[12px] font-semibold tabular-nums tracking-tight text-white">{item.amount}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
