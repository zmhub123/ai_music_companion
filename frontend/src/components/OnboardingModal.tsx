import { useState } from 'react'
import { App, Button, Modal } from 'antd'
import { submitOnboarding } from '../services/guestService'
import { useGuestStore } from '../stores/guestStore'
import type { SkillLevel } from '../types/api'

const SKILL_OPTIONS: { key: SkillLevel; label: string }[] = [
  { key: 'beginner', label: '零基础' },
  { key: 'intermediate', label: '入门' },
  { key: 'advanced', label: '进阶' },
]

const STYLE_OPTIONS = [
  { key: 'folk', label: '民谣' },
  { key: 'pop', label: '流行' },
  { key: 'rock', label: '摇滚' },
  { key: 'ancient', label: '古风' },
  { key: 'indie', label: '独立' },
]

interface OnboardingModalProps {
  open: boolean
}

export default function OnboardingModal({ open }: OnboardingModalProps) {
  const { message } = App.useApp()
  const setOnboardingDone = useGuestStore((s) => s.setOnboardingDone)
  const [skillLevel, setSkillLevel] = useState<SkillLevel>('beginner')
  const [selectedStyles, setSelectedStyles] = useState<string[]>(['民谣', '流行'])
  const [submitting, setSubmitting] = useState(false)

  const toggleStyle = (label: string) => {
    setSelectedStyles((prev) =>
      prev.includes(label) ? prev.filter((s) => s !== label) : [...prev, label],
    )
  }

  const handleDone = async () => {
    if (selectedStyles.length < 1) {
      message.warning('请至少选择 1 种风格')
      return
    }
    setSubmitting(true)
    try {
      await submitOnboarding({
        skill_level: skillLevel,
        style_preferences: selectedStyles,
      })
      setOnboardingDone(skillLevel, selectedStyles)
      message.success('偏好已保存，开始探索吧')
    } catch (err) {
      message.error(err instanceof Error ? err.message : '保存失败')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      open={open}
      footer={null}
      closable={false}
      maskClosable={false}
      centered
      width={480}
      className="onboarding-modal"
      styles={{ body: { padding: '40px' } }}
    >
      <h2 className="onboarding-title">先认识一下你</h2>
      <p className="onboarding-desc">选择弹唱水平和喜欢的风格，推荐会更懂你</p>

      <p className="onboarding-label">弹唱水平</p>
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

      <p className="onboarding-label">风格偏好（可多选）</p>
      <div className="chip-group">
        {STYLE_OPTIONS.map((opt) => (
          <button
            key={opt.key}
            type="button"
            className={`chip${selectedStyles.includes(opt.label) ? ' selected' : ''}`}
            onClick={() => toggleStyle(opt.label)}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <Button
        type="primary"
        block
        size="large"
        loading={submitting}
        className="onboarding-submit"
        onClick={handleDone}
      >
        开始探索
      </Button>
    </Modal>
  )
}
