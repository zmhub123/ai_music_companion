import { useEffect } from 'react'
import { Button, Dropdown } from 'antd'
import type { MenuProps } from 'antd'
import { UserOutlined } from '@ant-design/icons'
import { ensureGuestSession } from '../../services/neteaseAuthService'
import { useAuthStore } from '../../stores/authStore'
import NeteaseLoginModal from './NeteaseLoginModal'

export default function UserLoginMenu() {
  const guestReady = useAuthStore((s) => s.guestReady)
  const netease = useAuthStore((s) => s.netease)
  const refreshAuth = useAuthStore((s) => s.refreshAuth)
  const logoutNeteaseAccount = useAuthStore((s) => s.logoutNeteaseAccount)
  const loginOpen = useAuthStore((s) => s.neteaseLoginOpen)
  const openNeteaseLogin = useAuthStore((s) => s.openNeteaseLogin)
  const closeNeteaseLogin = useAuthStore((s) => s.closeNeteaseLogin)

  useEffect(() => {
    void (async () => {
      try {
        await ensureGuestSession()
        await refreshAuth()
      } catch {
        /* guest session best-effort */
      }
    })()
  }, [refreshAuth])

  const label = netease.logged_in
    ? `网易云 · ${netease.nickname || '已登录'}`
    : guestReady
      ? '游客模式'
      : '登录'

  const items: MenuProps['items'] = netease.logged_in
    ? [
        { key: 'guest', label: '当前：游客 Session（偏好/歌单）', disabled: true },
        { type: 'divider' },
        {
          key: 'logout-netease',
          label: '退出网易云账号',
          onClick: () => void logoutNeteaseAccount(),
        },
      ]
    : [
        { key: 'guest', label: '游客模式（无需登录即可使用）', disabled: true },
        { type: 'divider' },
        {
          key: 'netease-login',
          label: '登录网易云账号',
          onClick: () => openNeteaseLogin(),
        },
      ]

  return (
    <>
      <Dropdown menu={{ items }} trigger={['click']}>
        <Button icon={<UserOutlined />} className="btn-user-login">
          {label}
        </Button>
      </Dropdown>
      <NeteaseLoginModal open={loginOpen} onClose={() => closeNeteaseLogin()} />
    </>
  )
}
