import { useEffect, useState } from "react"
import { animate } from "framer-motion"

export function CountUp({
  value,
  duration = 1.5,
  prefix = "",
  suffix = "",
}: {
  value: number
  duration?: number
  prefix?: string
  suffix?: string
}) {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    const controls = animate(0, value, {
      duration,
      ease: "easeOut",
      onUpdate(val) {
        setDisplayValue(val)
      }
    })
    return () => controls.stop()
  }, [value, duration])

  return (
    <span>
      {prefix}
      {Math.round(displayValue).toLocaleString("en-IN")}
      {suffix}
    </span>
  )
}
