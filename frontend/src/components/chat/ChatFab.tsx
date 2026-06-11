import { useLocation } from 'react-router-dom'
import { useChatStore } from '../../stores/chatStore'

export default function ChatFab() {
  const location = useLocation()
  const floatState = useChatStore((s) => s.floatState)
  const openChat = useChatStore((s) => s.openChat)

  const isHome = location.pathname === '/'
  const isPlayer = location.pathname.startsWith('/player')
  const hidden = isHome || isPlayer || floatState === 'open'

  if (hidden) return null

  return (
    <button type="button" className="chat-fab" aria-label="打开 AI 助手" onClick={openChat}>
      <span className="chat-fab-icon">♪</span>
      <span className="chat-fab-label">AI 助手</span>
    </button>
  )
}
