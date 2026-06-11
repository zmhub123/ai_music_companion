import { Button, Layout } from 'antd'
import { useLocation, useNavigate } from 'react-router-dom'
import UserLoginMenu from './auth/UserLoginMenu'
import GlobalSearch from './GlobalSearch'

const { Header } = Layout

const NAV_ITEMS = [
  { key: '/', label: '首页' },
  { key: '/playlists', label: '歌单' },
  { key: '/scores', label: '谱库' },
  { key: '/me', label: '我的' },
]

function navActiveKey(pathname: string) {
  if (pathname.startsWith('/playlists')) return '/playlists'
  if (pathname.startsWith('/player')) return '/'
  return NAV_ITEMS.find((n) => n.key === pathname)?.key ?? '/'
}

export default function AppHeader() {
  const navigate = useNavigate()
  const location = useLocation()
  const activeKey = navActiveKey(location.pathname)
  const handleOpenChat = () => {
    navigate('/')
  }

  return (
    <Header className="app-header">
      <div className="app-brand" onClick={() => navigate('/')}>
        <span className="app-brand-icon">♪</span>
        <span className="app-brand-text">音伴</span>
      </div>
      <nav className="app-nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.key}
            type="button"
            className={`app-nav-link${activeKey === item.key ? ' active' : ''}`}
            onClick={() => navigate(item.key)}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <GlobalSearch />
      <div className="app-header-actions">
        <Button type="default" className="btn-header-chat" onClick={handleOpenChat}>
          AI 助手
        </Button>
        <UserLoginMenu />
      </div>
    </Header>
  )
}
