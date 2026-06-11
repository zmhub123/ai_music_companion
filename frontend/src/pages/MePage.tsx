import { useEffect, useState } from 'react'
import { App, Modal } from 'antd'
import { useNavigate } from 'react-router-dom'
import { clearGuestData, getGuestMe, updatePreferences } from '../services/guestService'
import { useGuestStore } from '../stores/guestStore'
import type { SkillLevel } from '../types/api'

const SKILL_OPTIONS: { key: SkillLevel; label: string }[] = [
  { key: 'beginner', label: '零基础' },
  { key: 'intermediate', label: '入门' },
  { key: 'advanced', label: '进阶' },
]

const STYLE_OPTIONS = ['民谣', '流行', '摇滚', '古风', '独立']

export default function MePage() {
  const { message } = App.useApp()
  const navigate = useNavigate()
  const fetchProfile = useGuestStore((s) => s.fetchProfile)
  const profile = useGuestStore((s) => s.profile)

  const [skillLevel, setSkillLevel] = useState<SkillLevel>('beginner')
  const [styles, setStyles] = useState<string[]>(['民谣', '流行'])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    void getGuestMe().then((p) => {
      if (p.skill_level) setSkillLevel(p.skill_level)
      if (p.style_preferences.length) setStyles(p.style_preferences)
    })
  }, [])

  const toggleStyle = (label: string) => {
    setStyles((prev) =>
      prev.includes(label) ? prev.filter((s) => s !== label) : [...prev, label],
    )
  }

  const handleSave = async () => {
    if (styles.length < 1) {
      message.warning('请至少选择 1 种风格')
      return
    }
    setSaving(true)
    try {
      await updatePreferences({ skill_level: skillLevel, style_preferences: styles })
      message.success('偏好已保存')
      await fetchProfile()
    } catch (err) {
      message.error(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleClear = () => {
    Modal.confirm({
      title: '清除全部数据？',
      content: '将删除歌单、对话与偏好设置，此操作不可恢复。',
      okText: '确认清除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        await clearGuestData()
        await fetchProfile()
        message.success('数据已清除')
        navigate('/')
      },
    })
  }

  return (
    <div className="page-content page-me">
      <h2>我的</h2>
      <div className="settings-section">
        <h3>弹唱偏好</h3>
        <div className="chip-group">
          {SKILL_OPTIONS.map((opt) => (
            <button
              key={opt.key}
              type="button"
              className={`chip${skillLevel === opt.key ? ' selected' : ''}`}
              onClick={() => setSkillLevel(opt.key)}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <div className="chip-group" style={{ marginTop: 12 }}>
          {STYLE_OPTIONS.map((label) => (
            <button
              key={label}
              type="button"
              className={`chip${styles.includes(label) ? ' selected' : ''}`}
              onClick={() => toggleStyle(label)}
            >
              {label}
            </button>
          ))}
        </div>
        <button type="button" className="btn-save-prefs" disabled={saving} onClick={() => void handleSave()}>
          保存偏好
        </button>
      </div>
      <div className="settings-section">
        <h3>游客说明</h3>
        <p className="guest-notice">
          当前为游客模式，歌单与对话数据保存在本设备。清除浏览器数据后将无法恢复。
        </p>
        {profile && (
          <p className="guest-meta">
            游客 ID：{profile.guest_id.slice(0, 8)}…
          </p>
        )}
      </div>
      <button type="button" className="danger-link" onClick={handleClear}>
        清除全部数据
      </button>
    </div>
  )
}
