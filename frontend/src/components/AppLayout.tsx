import { Layout } from 'antd'
import { useEffect, type ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import ChatFab from './chat/ChatFab'
import ChatFloat from './chat/ChatFloat'
import PlayerChatDock from './chat/PlayerChatDock'
import MiniPlayer from './player/MiniPlayer'
import AppHeader from './AppHeader'
import ScoreGenerateModal from './score/ScoreGenerateModal'
import { useChatStore } from '../stores/chatStore'
import { useScoreStore } from '../stores/scoreStore'

const { Content } = Layout

export default function AppLayout({ children }: { children: ReactNode }) {
  const location = useLocation()
  const syncForRoute = useChatStore((s) => s.syncForRoute)
  const floatState = useChatStore((s) => s.floatState)
  const playerChatDocked = useChatStore((s) => s.playerChatDocked)
  const scoreOpen = useScoreStore((s) => s.open)

  useEffect(() => {
    syncForRoute(location.pathname)
    document.body.classList.toggle('page-player-active', location.pathname.startsWith('/player'))
    document.body.classList.toggle('page-home-active', location.pathname === '/')
  }, [location.pathname, syncForRoute])

  useEffect(() => {
    const onPlayer = location.pathname.startsWith('/player')
    document.body.classList.toggle(
      'page-player-chat-open',
      onPlayer && floatState === 'open' && !playerChatDocked,
    )
    document.body.classList.toggle('page-player-chat-docked', onPlayer && playerChatDocked)
    document.body.classList.toggle(
      'with-score-chat',
      onPlayer && scoreOpen && floatState === 'open' && !playerChatDocked,
    )
  }, [location.pathname, scoreOpen, floatState, playerChatDocked])

  return (
    <Layout className="app-layout">
      <AppHeader />
      <Content className="app-content">{children}</Content>
      <ChatFloat />
      <PlayerChatDock />
      <ChatFab />
      <MiniPlayer />
      <ScoreGenerateModal />
    </Layout>
  )
}
