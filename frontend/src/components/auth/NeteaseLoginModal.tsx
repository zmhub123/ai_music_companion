import { useEffect, useRef, useState } from 'react'
import { Modal, Spin, Typography } from 'antd'
import { pollNeteaseQrLogin, startNeteaseQrLogin } from '../../services/neteaseAuthService'
import { useAuthStore } from '../../stores/authStore'

interface NeteaseLoginModalProps {
  open: boolean
  onClose: () => void
  onSuccess?: () => void
}

export default function NeteaseLoginModal({ open, onClose, onSuccess }: NeteaseLoginModalProps) {
  const refreshAuth = useAuthStore((s) => s.refreshAuth)
  const [loading, setLoading] = useState(false)
  const [qrImage, setQrImage] = useState('')
  const [hint, setHint] = useState('请使用网易云音乐 App 扫码登录')
  const tokenRef = useRef('')
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    if (!open) return

    let cancelled = false
    void (async () => {
      setLoading(true)
      setHint('正在获取二维码…')
      try {
        const started = await startNeteaseQrLogin()
        if (cancelled) return
        tokenRef.current = started.login_token
        setQrImage(`data:image/png;base64,${started.qr_image_base64}`)
        setHint('请使用网易云音乐 App 扫码登录')
      } catch (e) {
        setHint(e instanceof Error ? e.message : '获取二维码失败')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()

    return () => {
      cancelled = true
      if (timerRef.current) window.clearInterval(timerRef.current)
    }
  }, [open])

  useEffect(() => {
    if (!open || !tokenRef.current) return

    timerRef.current = window.setInterval(() => {
      void (async () => {
        try {
          const result = await pollNeteaseQrLogin(tokenRef.current)
          if (result.status === 'waiting') {
            setHint(result.message)
          } else if (result.status === 'scanned') {
            setHint(result.message)
          } else if (result.status === 'expired') {
            setHint(result.message)
            if (timerRef.current) window.clearInterval(timerRef.current)
          } else if (result.status === 'success') {
            setHint('登录成功')
            if (timerRef.current) window.clearInterval(timerRef.current)
            await refreshAuth()
            useAuthStore.getState().bumpScoreRetry()
            onSuccess?.()
            onClose()
          }
        } catch (e) {
          setHint(e instanceof Error ? e.message : '登录状态查询失败')
        }
      })()
    }, 2000)

    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current)
    }
  }, [open, onClose, onSuccess, refreshAuth, qrImage])

  return (
    <Modal
      title="登录网易云音乐"
      open={open}
      onCancel={onClose}
      footer={null}
      centered
      destroyOnHidden
    >
      <div className="netease-login-modal">
        <Typography.Paragraph type="secondary">{hint}</Typography.Paragraph>
        <div className="netease-qr-wrap">
          {loading ? <Spin /> : qrImage ? <img src={qrImage} alt="网易云登录二维码" /> : null}
        </div>
      </div>
    </Modal>
  )
}
