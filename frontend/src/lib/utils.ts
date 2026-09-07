/**
 * lib/utils.ts
 * Shared utility functions for the application.
 * `cn` is the standard shadcn/ui className merger.
 */

import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merges class names using clsx and tailwind-merge.
 * Resolves Tailwind conflicts (e.g., `p-4` vs `p-2` → last wins).
 *
 * Usage:
 *   cn('px-4 py-2', isActive && 'bg-blue-500', className)
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}
