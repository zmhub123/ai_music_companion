import { useLocation } from 'react-router-dom'
import { useChatStore } from '../../stores/chatStore'

export default function PlayerChatDock() {
  const location = useLocation()
  const playerChatDocked = useChatStore((s) => s.playerChatDocked)
  const floatState = useChatStore((s) => s.floatState)
  const messages = useChatStore((s) => s.messages)
  const openPlayerChatFromDock = useChatStore((s) => s.openPlayerChatFromDock)

  const onPlayer = location.pathname.startsWith('/player')
  if (!onPlayer || !playerChatDocked || floatState === 'open') return null

  const lastMessage = messages[messages.length - 1]
  const preview =
    lastMessage?.role === 'assistant'
      ? lastMessage.content
      : messages
          .slice()
          .reverse()
          .find((m) => m.role === 'assistant')?.content

  return (
    <div className="player-chat-dock">
      <div className="player-chat-dock-preview" aria-hidden="true">
        <div className="player-chat-dock-preview-title">AI 音乐助手</div>
        <p className="player-chat-dock-preview-text">
          {preview ? (preview.length > 72 ? `${preview.slice(0, 72)}…` : preview) : '继续聊聊音乐吧～'}
        </p>
      </div>
      <button
        type="button"
        className="player-chat-dock-btn"
        aria-label="打开 AI 音乐助手"
        onClick={openPlayerChatFromDock}
      >
        <span className="player-chat-dock-btn-icon">✦</span>
        <span className="player-chat-dock-btn-label">AI</span>
      </button>
    </div>
  )
}
