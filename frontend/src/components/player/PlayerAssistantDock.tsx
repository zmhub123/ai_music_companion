import { useChatStore } from '../../stores/chatStore'

export default function PlayerAssistantDock() {
  const floatState = useChatStore((s) => s.floatState)
  const openChat = useChatStore((s) => s.openChat)

  if (floatState === 'open') return null

  return (
    <button
      type="button"
      className="player-assistant-dock"
      aria-label="打开 AI 助手"
      onClick={openChat}
    >
      <span className="player-assistant-dock-icon">✦</span>
      <span className="player-assistant-dock-label">AI 助手</span>
    </button>
  )
}
