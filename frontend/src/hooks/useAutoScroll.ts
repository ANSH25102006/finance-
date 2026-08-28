import { useEffect, useRef, useState } from 'react'

export function useAutoScroll<T extends HTMLElement>(dependency: any) {
  const scrollRef = useRef<T | null>(null)
  const [showScrollButton, setShowScrollButton] = useState(false)

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior,
      })
    }
  }

  const handleScroll = () => {
    if (!scrollRef.current) return
    const { scrollTop, scrollHeight, clientHeight } = scrollRef.current
    
    // Show scroll button if user has scrolled up by more than 300px
    const isScrolledUp = scrollHeight - scrollTop - clientHeight > 300
    setShowScrollButton(isScrolledUp)
  }

  // Automatically scroll to bottom when dependency changes (e.g. messages length or stream status)
  useEffect(() => {
    if (scrollRef.current && !showScrollButton) {
      scrollToBottom('smooth')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dependency])

  return {
    scrollRef,
    showScrollButton,
    scrollToBottom,
    handleScroll,
  }
}
