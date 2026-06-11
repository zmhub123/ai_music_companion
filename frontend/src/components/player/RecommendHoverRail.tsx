import { useRef, useState } from 'react'
import { MenuOutlined } from '@ant-design/icons'
import RecommendList from './RecommendList'

export default function RecommendHoverRail() {
  const [open, setOpen] = useState(false)
  const closeTimerRef = useRef<number | null>(null)

  const clearCloseTimer = () => {
    if (closeTimerRef.current !== null) {
      window.clearTimeout(closeTimerRef.current)
      closeTimerRef.current = null
    }
  }

  const handleEnter = () => {
    clearCloseTimer()
    setOpen(true)
  }

  const handleLeave = () => {
    clearCloseTimer()
    closeTimerRef.current = window.setTimeout(() => setOpen(false), 160)
  }

  return (
    <div
      className={`rec-glass-flyout${open ? ' open' : ''}`}
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
    >
      <button type="button" className="rec-glass-trigger" aria-label="展开推荐列表" aria-expanded={open}>
        <MenuOutlined />
      </button>
      <div className="rec-glass-panel">
        <RecommendList />
      </div>
    </div>
  )
}
