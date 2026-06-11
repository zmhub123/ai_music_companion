import { useCallback, useEffect, useRef, useState } from 'react'
import {
  CaretRightOutlined,
  PauseOutlined,
  StepBackwardOutlined,
  StepForwardOutlined,
  RetweetOutlined,
  PlusOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { App, Spin } from 'antd'
import SongCover from '../common/SongCover'
import AddToPlaylistModal from './AddToPlaylistModal'
import { bindAudioEnded, usePlayerStore } from '../../stores/playerStore'
import { useScoreStore } from '../../stores/scoreStore'
import { confirmVipPlayback } from '../../utils/playConfirm'

function formatTime(sec: number) {
  if (!sec || !Number.isFinite(sec)) return '00:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function VinylPlayer() {
  const { message } = App.useApp()
  const currentSong = usePlayerStore((s) => s.currentSong)
  const playing = usePlayerStore((s) => s.playing)
  const loading = usePlayerStore((s) => s.loading)
  const progress = usePlayerStore((s) => s.progress)
  const duration = usePlayerStore((s) => s.duration)
  const togglePlay = usePlayerStore((s) => s.togglePlay)
  const seek = usePlayerStore((s) => s.seek)
  const tickProgress = usePlayerStore((s) => s.tickProgress)
  const pause = usePlayerStore((s) => s.pause)
  const openGenerateModal = useScoreStore((s) => s.openGenerateModal)
  const [playlistModalOpen, setPlaylistModalOpen] = useState(false)

  const barRef = useRef<HTMLDivElement>(null)
  const draggingRef = useRef(false)

  useEffect(() => {
    bindAudioEnded(() => pause())
  }, [pause])

  useEffect(() => {
    if (!playing) return
    const id = window.setInterval(tickProgress, 250)
    return () => clearInterval(id)
  }, [playing, tickProgress])

  const ratio = duration > 0 ? (progress / duration) * 100 : 0

  const seekFromClientX = useCallback(
    (clientX: number) => {
      const bar = barRef.current
      if (!bar) return
      const rect = bar.getBoundingClientRect()
      const r = (clientX - rect.left) / rect.width
      seek(r)
    },
    [seek],
  )

  const onPointerDown = (e: React.PointerEvent) => {
    draggingRef.current = true
    barRef.current?.setPointerCapture(e.pointerId)
    barRef.current?.classList.add('dragging')
    seekFromClientX(e.clientX)
  }

  const onPointerMove = (e: React.PointerEvent) => {
    if (!draggingRef.current) return
    seekFromClientX(e.clientX)
  }

  const onPointerUp = (e: React.PointerEvent) => {
    if (!draggingRef.current) return
    draggingRef.current = false
    barRef.current?.releasePointerCapture(e.pointerId)
    barRef.current?.classList.remove('dragging')
    seekFromClientX(e.clientX)
  }

  const armState = playing ? 'playing' : 'paused'

  const handlePlayToggle = () => {
    void togglePlay().then(async (err) => {
      if (!err) return
      if (err === '已取消播放') return
      if (err.startsWith('http')) {
        if (currentSong.vip_only) {
          await confirmVipPlayback(currentSong.song_name, err)
          return
        }
        message.warning('暂无法内嵌播放，请尝试外链播放')
        window.open(err, '_blank', 'noopener,noreferrer')
        return
      }
      message.error(err)
    })
  }

  return (
    <section className="panel-center">
      <div className="vinyl-wrap">
        <div className={`vinyl-disc${playing ? ' playing' : ''}`}>
          <div className="vinyl-label">
            <SongCover
              coverUrl={currentSong.cover_url}
              alt={`${currentSong.song_name} 封面`}
              className="vinyl-label-cover"
            />
          </div>
        </div>
        <div className="vinyl-arm-mount" aria-hidden="true">
          <div className="vinyl-arm" data-state={armState}>
            <span className="vinyl-arm-bar" />
            <span className="vinyl-arm-head" />
          </div>
        </div>
      </div>

      <div className="player-now-playing">
        <h2 className="player-title">
          {currentSong.song_name}
          {currentSong.vip_only ? <span className="song-vip-tag">VIP</span> : null}
        </h2>
        <p className="player-artist">{currentSong.artist_name}</p>
      </div>

      <div className="progress-wrap">
        <div
          ref={barRef}
          className="progress-bar"
          role="slider"
          aria-label="播放进度"
          aria-valuemin={0}
          aria-valuemax={100}
          tabIndex={0}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        >
          <div className="progress-fill" style={{ width: `${ratio}%` }} />
          <div className="progress-thumb" style={{ left: `${ratio}%` }} />
        </div>
        <div className="progress-time">
          <span>{formatTime(progress)}</span>
          <span className="progress-time-sep">/</span>
          <span>{formatTime(duration || 0)}</span>
        </div>
      </div>

      <div className="player-controls">
        <button type="button" className="ctrl-btn ctrl-btn-icon" title="上一首" aria-label="上一首">
          <StepBackwardOutlined />
        </button>
        <button
          type="button"
          className={`ctrl-btn play-main${playing ? ' playing-pulse' : ''}`}
          title={playing ? '暂停' : '播放'}
          aria-label={playing ? '暂停' : '播放'}
          disabled={loading}
          onClick={handlePlayToggle}
        >
          {loading ? (
            <Spin size="small" />
          ) : playing ? (
            <PauseOutlined />
          ) : (
            <CaretRightOutlined />
          )}
        </button>
        <button type="button" className="ctrl-btn ctrl-btn-icon" title="下一首" aria-label="下一首">
          <StepForwardOutlined />
        </button>
        <button type="button" className="ctrl-btn ctrl-btn-icon" title="循环播放" aria-label="循环播放">
          <RetweetOutlined />
        </button>
      </div>

      <div className="player-actions">
        <button type="button" className="btn-primary-action" onClick={openGenerateModal}>
          <FileTextOutlined />
          <span>生成曲谱</span>
        </button>
        <button type="button" className="btn-outline" onClick={() => setPlaylistModalOpen(true)}>
          <PlusOutlined />
          <span>加入歌单</span>
        </button>
      </div>
      <AddToPlaylistModal open={playlistModalOpen} onClose={() => setPlaylistModalOpen(false)} />
    </section>
  )
}
