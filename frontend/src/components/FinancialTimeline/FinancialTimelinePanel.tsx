/**
 * components/FinancialTimeline/FinancialTimelinePanel.tsx
 *
 * The primary dashboard section for the Financial Timeline.
 */

import { useState, useMemo } from 'react'
import { AnimatePresence } from 'framer-motion'
import {
  History,
  RefreshCw,
  Search,
  X,
  CalendarHeart
} from 'lucide-react'
import { useTimeline } from '@/hooks/useTimeline'
import { TimelineCard } from './TimelineCard'
import { TimelineDetailsDrawer } from './TimelineDetailsDrawer'
import type { TimelineEvent, TimelineEventSeverity } from '@/services/timelineService'

// ------------------------------------------------------------------ //
// Helper Components
// ------------------------------------------------------------------ //

function TimelineSkeleton() {
  return (
    <div className="space-y-4 pt-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="flex gap-4 animate-pulse">
          <div className="h-8 w-8 rounded-full bg-white/[0.04] mt-1 flex-shrink-0" />
          <div className="flex-1 bg-white/[0.02] rounded-[16px] p-3.5 space-y-2 border border-white/[0.02]">
            <div className="h-3 w-1/3 bg-white/[0.04] rounded" />
            <div className="h-2.5 w-3/4 bg-white/[0.03] rounded" />
          </div>
        </div>
      ))}
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="h-10 w-10 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-3">
        <CalendarHeart className="h-5 w-5 text-indigo-400" />
      </div>
      <p className="text-[13px] font-semibold text-white mb-1">No timeline events yet</p>
      <p className="text-[11px] text-gray-500 max-w-xs">
        Your timeline will populate automatically as you add transactions and insights are generated.
      </p>
    </div>
  )
}

// ------------------------------------------------------------------ //
// Main Panel
// ------------------------------------------------------------------ //

export function FinancialTimelinePanel() {
  const { data: events, isLoading, isFetching, error, refetch } = useTimeline()
  
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedSeverity, setSelectedSeverity] = useState<TimelineEventSeverity | 'ALL'>('ALL')
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null)

  // Filter & Search
  const filteredEvents = useMemo(() => {
    let res = events

    if (selectedSeverity !== 'ALL') {
      res = res.filter(e => e.severity === selectedSeverity)
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      res = res.filter(
        e => e.title.toLowerCase().includes(q) || e.description.toLowerCase().includes(q)
      )
    }

    return res
  }, [events, searchQuery, selectedSeverity])

  return (
    <>
      <section className="os-card flex flex-col relative overflow-hidden w-full h-full min-h-[400px]">
        {/* Header */}
        <div className="flex flex-col gap-3 border-b border-white/[0.04] pb-3 pt-4 px-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <History className="h-4 w-4 text-indigo-400" />
              <h2 className="typo-subheading">Financial Timeline</h2>
            </div>
            <button
              onClick={() => refetch()}
              disabled={isLoading || isFetching}
              className="h-7 w-7 rounded-lg flex items-center justify-center text-gray-600 hover:text-white hover:bg-white/[0.05] transition-all"
            >
              <RefreshCw className={`h-3 w-3 ${isFetching ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {/* Simple Filters */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-gray-600" />
              <input
                type="text"
                placeholder="Search events..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-7 pr-3 py-1.5 rounded-lg text-[11px] bg-white/[0.02] border border-white/[0.06] text-white focus:outline-none focus:border-white/20 transition-all"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value as TimelineEventSeverity | 'ALL')}
              className="px-2 py-1.5 rounded-lg text-[11px] font-medium bg-white/[0.02] border border-white/[0.06] text-gray-300 focus:outline-none focus:border-white/20"
            >
              <option value="ALL">All Types</option>
              <option value="CRITICAL">Critical</option>
              <option value="WARNING">Warnings</option>
              <option value="INFO">Info</option>
              <option value="SUCCESS">Success</option>
            </select>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 p-5 overflow-y-auto min-h-0 relative">
          {isLoading ? (
            <TimelineSkeleton />
          ) : error ? (
            <div className="text-center text-[12px] text-red-400 py-10">Failed to load timeline.</div>
          ) : filteredEvents.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="space-y-4">
              <AnimatePresence>
                {filteredEvents.map((event, idx) => (
                  <TimelineCard 
                    key={event.id} 
                    event={event} 
                    onClick={setSelectedEvent} 
                    index={idx}
                  />
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </section>

      <TimelineDetailsDrawer 
        event={selectedEvent} 
        onClose={() => setSelectedEvent(null)} 
      />
    </>
  )
}
