import { useState } from 'react'
import { App } from 'antd'
import { useNavigate } from 'react-router-dom'
import { useChatStore } from '../stores/chatStore'

const MOOD_TAGS = [
  { label: '今天很开心', mood: '今天很开心，想听欢快的歌' },
  { label: '有点 emo', mood: '有点 emo，想安静一下' },
  { label: '想放松一下', mood: '想放松一下，不要太吵' },
  { label: '适合开车听', mood: '适合开车听的歌，节奏感强一点' },
]

export default function HomeHero() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const sendChat = useChatStore((s) => s.sendMessage)
  const openChat = useChatStore((s) => s.openChat)
  const sending = useChatStore((s) => s.sending)
  const [input, setInput] = useState('')

  const handleSend = async (text?: string) => {
    const content = (text ?? input).trim() || '今天有点累，想听点安静的'
    if (sending) return
    setInput('')
    openChat()
    navigate('/player')
    try {
      await sendChat(content)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '发送失败')
    }
  }

  return (
    <section className="home-hero">
      <h1>AI 音乐陪伴你</h1>
      <p className="subtitle">输入你的心情，让 AI 为你推荐最适合的歌曲</p>
      <div className="search-hero">
        <input
          type="text"
          placeholder="今天心情怎么样？"
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
          className={`btn-send${sending ? ' sending' : ''}`}
          aria-label="发送"
          disabled={sending}
          onClick={() => void handleSend()}
        >
          ↑
        </button>
      </div>
      <div className="mood-tags">
        {MOOD_TAGS.map((tag) => (
          <button
            key={tag.label}
            type="button"
            className="mood-tag"
            disabled={sending}
            onClick={() => {
              setInput(tag.mood)
              setTimeout(() => void handleSend(tag.mood), 200)
            }}
          >
            {tag.label}
          </button>
        ))}
      </div>
    </section>
  )
}
