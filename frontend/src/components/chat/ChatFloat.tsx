import { useCallback, useEffect, useRef, useState } from 'react'
import { App } from 'antd'
import { useLocation } from 'react-router-dom'
import { useChatStore } from '../../stores/chatStore'
import SongRecInline from './SongRecInline'

export default function ChatFloat() {
  const { message } = App.useApp()
  const location = useLocation()
  const messages = useChatStore((s) => s.messages)
  const floatState = useChatStore((s) => s.floatState)
  const fetchMessages = useChatStore((s) => s.fetchMessages)
  const sendMessage = useChatStore((s) => s.sendMessage)
  const storeSending = useChatStore((s) => s.sending)
  const resetConversation = useChatStore((s) => s.resetConversation)
  const minimizeChat = useChatStore((s) => s.minimizeChat)
  const closeChat = useChatStore((s) => s.closeChat)
  const playerChatDocked = useChatStore((s) => s.playerChatDocked)
  const enterPlayerChatDock = useChatStore((s) => s.enterPlayerChatDock)

  const [input, setInput] = useState('')
  const sending = storeSending
  const messagesRef = useRef<HTMLDivElement>(null)
  const isPlayer = location.pathname.startsWith('/player')

  const scrollToBottom = useCallback(() => {
    const el = messagesRef.current
    if (!el) return
    const doScroll = () => {
      el.scrollTop = el.scrollHeight
    }
    requestAnimationFrame(() => {
      doScroll()
      requestAnimationFrame(doScroll)
    })
  }, [])

  useEffect(() => {
    void fetchMessages()
  }, [fetchMessages])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    if (floatState === 'open') scrollToBottom()
  }, [floatState, scrollToBottom])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || sending) return
    setInput('')
    scrollToBottom()
    try {
      await sendMessage(text)
      scrollToBottom()
    } catch (err) {
      message.error(err instanceof Error ? err.message : '发送失败')
    }
  }

  const handleReset = async () => {
    try {
      await resetConversation()
      message.success('已开始新对话')
    } catch (err) {
      message.error(err instanceof Error ? err.message : '重置失败')
    }
  }

  const handleMinimize = () => {
    if (isPlayer && playerChatDocked) {
      enterPlayerChatDock()
      return
    }
    minimizeChat()
  }

  const handleClose = () => {
    if (isPlayer && playerChatDocked) {
      enterPlayerChatDock()
      return
    }
    closeChat()
  }

  const classNames = [
    'chat-float',
    floatState === 'open' ? 'open' : '',
    floatState === 'minimized' ? 'minimized' : '',
    isPlayer ? 'chat-float--player' : '',
    isPlayer && playerChatDocked && floatState === 'open' ? 'chat-float--dock-open' : '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={classNames}>
      <div className="chat-float-header">
        <div className="chat-float-title">
          <span className="chat-float-dot" />
          AI 音乐助手
        </div>
        <div className="chat-float-actions">
          <button type="button" className="chat-float-btn" title="新建对话" onClick={() => void handleReset()}>
            ↺
          </button>
          <button type="button" className="chat-float-btn" title="最小化" onClick={handleMinimize}>
            —
          </button>
          <button type="button" className="chat-float-btn" title="关闭" onClick={handleClose}>
            ×
          </button>
        </div>
      </div>
      <div className="chat-float-body">
        <div className="ai-messages" ref={messagesRef}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`bubble bubble-${msg.role === 'user' ? 'user' : 'ai'}${
                msg.metadata?.pending ? ' bubble-pending' : ''
              }`}
            >
              {msg.metadata?.pending ? (
                <span className="chat-typing" aria-label="AI 正在回复">
                  <span />
                  <span />
                  <span />
                </span>
              ) : (
                msg.content
              )}
              {msg.metadata?.recommendations && (
                <SongRecInline recommendations={msg.metadata.recommendations} />
              )}
            </div>
          ))}
        </div>
      </div>
      <div className="chat-float-footer">
        <input
          type="text"
          placeholder="继续和 AI 聊聊…"
          value={input}
          disabled={sending}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              void handleSend()
            }
          }}
        />
        <button
          type="button"
          className="chat-send-btn"
          aria-label="发送"
          disabled={sending}
          onClick={() => void handleSend()}
        >
          ↑
        </button>
      </div>
    </div>
  )
}
