/**
 * components/FinancialInsights/SeverityBadge.tsx
 * Visual severity indicator — icon + label + color.
 * Never relies on color alone; always includes icon and text.
 */

import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Info,
} from 'lucide-react'
import type { InsightSeverity } from '@/services/intelligenceService'

interface SeverityConfig {
  icon: React.ElementType
  label: string
  textColor: string
  bgColor: string
  borderColor: string
  dotColor: string
  glowColor: string
}

export const SEVERITY_CONFIG: Record<InsightSeverity, SeverityConfig> = {
  CRITICAL: {
    icon: AlertOctagon,
    label: 'Critical',
    textColor: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    dotColor: 'bg-red-400',
    glowColor: 'rgba(239,68,68,0.15)',
  },
  WARNING: {
    icon: AlertTriangle,
    label: 'Warning',
    textColor: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    dotColor: 'bg-amber-400',
    glowColor: 'rgba(245,158,11,0.12)',
  },
  SUCCESS: {
    icon: CheckCircle2,
    label: 'Success',
    textColor: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
    dotColor: 'bg-emerald-400',
    glowColor: 'rgba(52,211,153,0.12)',
  },
  INFO: {
    icon: Info,
    label: 'Info',
    textColor: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    dotColor: 'bg-blue-400',
    glowColor: 'rgba(96,165,250,0.12)',
  },
}

interface SeverityBadgeProps {
  severity: InsightSeverity
  size?: 'sm' | 'md'
}

export function SeverityBadge({ severity, size = 'sm' }: SeverityBadgeProps) {
  const cfg = SEVERITY_CONFIG[severity]
  const Icon = cfg.icon

  if (size === 'md') {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold uppercase tracking-widest border ${cfg.textColor} ${cfg.bgColor} ${cfg.borderColor}`}
        aria-label={`Severity: ${cfg.label}`}
      >
        <Icon className="h-3 w-3" aria-hidden="true" />
        {cfg.label}
      </span>
    )
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-sm text-[9px] font-semibold uppercase tracking-widest border ${cfg.textColor} ${cfg.bgColor} ${cfg.borderColor}`}
      aria-label={`Severity: ${cfg.label}`}
    >
      <Icon className="h-2.5 w-2.5" aria-hidden="true" />
      {cfg.label}
    </span>
  )
}
