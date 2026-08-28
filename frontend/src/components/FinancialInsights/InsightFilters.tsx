/**
 * components/FinancialInsights/InsightFilters.tsx
 * Severity filter chips + search input.
 */

import { Search, X } from 'lucide-react'
import type { InsightSeverity } from '@/services/intelligenceService'
import { SEVERITY_CONFIG } from './SeverityBadge'

export type FilterOption = InsightSeverity | 'ALL'

const FILTER_OPTIONS: { value: FilterOption; label: string }[] = [
  { value: 'ALL', label: 'All' },
  { value: 'CRITICAL', label: 'Critical' },
  { value: 'WARNING', label: 'Warnings' },
  { value: 'SUCCESS', label: 'Success' },
  { value: 'INFO', label: 'Info' },
]

interface InsightFiltersProps {
  activeFilter: FilterOption
  onFilterChange: (f: FilterOption) => void
  searchQuery: string
  onSearchChange: (q: string) => void
  counts: Record<FilterOption, number>
}

export function InsightFilters({
  activeFilter,
  onFilterChange,
  searchQuery,
  onSearchChange,
  counts,
}: InsightFiltersProps) {
  return (
    <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
      {/* Filter chips */}
      <div className="flex items-center gap-1.5 flex-wrap" role="group" aria-label="Filter insights by severity">
        {FILTER_OPTIONS.map(({ value, label }) => {
          const isActive = activeFilter === value
          const cfg = value !== 'ALL' ? SEVERITY_CONFIG[value as InsightSeverity] : null
          const count = counts[value] ?? 0

          return (
            <button
              key={value}
              onClick={() => onFilterChange(value)}
              aria-pressed={isActive}
              className={`
                relative flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold
                uppercase tracking-widest border transition-all duration-200 cursor-pointer
                focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20
                ${isActive
                  ? cfg
                    ? `${cfg.textColor} ${cfg.bgColor} ${cfg.borderColor}`
                    : 'text-white bg-white/10 border-white/20'
                  : 'text-gray-500 bg-transparent border-white/[0.04] hover:border-white/10 hover:text-gray-300'
                }
              `}
            >
              {cfg && (
                <span
                  className={`h-1.5 w-1.5 rounded-full ${isActive ? cfg.dotColor : 'bg-gray-600'}`}
                  aria-hidden="true"
                />
              )}
              {label}
              {count > 0 && (
                <span className={`text-[9px] tabular-nums ${isActive ? 'opacity-80' : 'opacity-40'}`}>
                  {count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Search */}
      <div className="relative flex-shrink-0 sm:ml-auto">
        <Search
          className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-600"
          aria-hidden="true"
        />
        <input
          type="search"
          placeholder="Search insights…"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          aria-label="Search insights"
          className="
            w-full sm:w-48 pl-7 pr-7 py-1.5 rounded-lg text-[11px] font-medium
            bg-white/[0.03] border border-white/[0.06] text-white placeholder-gray-600
            focus:outline-none focus:border-white/15 focus:bg-white/[0.05]
            transition-all duration-200
          "
        />
        {searchQuery && (
          <button
            onClick={() => onSearchChange('')}
            aria-label="Clear search"
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400 transition-colors"
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </div>
    </div>
  )
}
