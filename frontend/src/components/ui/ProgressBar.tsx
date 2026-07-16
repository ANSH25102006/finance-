import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface ProgressBarProps {
  progress: number // 0 to 100
  height?: number
  color?: string
  trackColor?: string
  className?: string
}

export function ProgressBar({
  progress,
  height = 8,
  color = "#22c55e", // emerald-500
  trackColor = "#f3f4f6", // gray-100
  className,
}: ProgressBarProps) {
  const normalizedProgress = Math.min(Math.max(progress, 0), 100)

  return (
    <div
      className={cn("w-full overflow-hidden rounded-full", className)}
      style={{ height, backgroundColor: trackColor }}
    >
      <motion.div
        className="h-full rounded-full"
        style={{ backgroundColor: color }}
        initial={{ width: 0 }}
        animate={{ width: `${normalizedProgress}%` }}
        transition={{ duration: 1, ease: "easeOut" }}
      />
    </div>
  )
}
