import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import SongCover from '../common/SongCover'
import { usePlayerStore } from '../../stores/playerStore'
import { useScoreStore } from '../../stores/scoreStore'

function formatTime(sec: number) {
  if (!sec || !Number.isFinite(sec)) return '00:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function MiniPlayer() {
  const location = useLocation()
  const navigate = useNavigate()
  const currentSong = usePlayerStore((s) => s.currentSong)
  const playing = usePlayerStore((s) => s.playing)
  const progress = usePlayerStore((s) => s.progress)
  const duration = usePlayerStore((s) => s.duration)
  const miniPlayerVisible = usePlayerStore((s) => s.miniPlayerVisible)
  const togglePlay = usePlayerStore((s) => s.togglePlay)
  const dismissMiniPlayer = usePlayerStore((s) => s.dismissMiniPlayer)
  const tickProgress = usePlayerStore((s) => s.tickProgress)
  const openGenerateModal = useScoreStore((s) => s.openGenerateModal)

  const isPlayerPage = location.pathname.startsWith('/player')
  const visible = miniPlayerVisible && !isPlayerPage

  useEffect(() => {
    if (!visible || !playing) return
    const id = window.setInterval(tickProgress, 250)
    return () => clearInterval(id)
  }, [visible, playing, tickProgress])

  useEffect(() => {
    document.body.classList.toggle('mini-player-active', visible)
  }, [visible])

  if (!visible) return null

  const ratio = duration > 0 ? (progress / duration) * 100 : 0

  return (
    <div className="mini-player">
      <button
        type="button"
        className="mini-player-info"
        onClick={() => {
          navigate('/player')
          openGenerateModal()
        }}
      >
        <SongCover coverUrl={currentSong.cover_url} alt={`${currentSong.song_name} 封面`} />
        <div className="song-info">
          <div className="name">{currentSong.song_name}</div>
          <div className="artist">{currentSong.artist_name}</div>
        </div>
      </button>
      <div className="mini-player-progress">
        <div className="mini-progress-fill" style={{ width: `${ratio}%` }} />
      </div>
      <span className="mini-player-time">{formatTime(progress)}</span>
      <button type="button" className="mini-player-play" onClick={() => void togglePlay()}>
        {playing ? '⏸' : '▶'}
      </button>
      <button
        type="button"
        className="mini-player-expand"
        onClick={() => navigate('/player')}
        title="打开播放页"
      >
        ⤢
      </button>
      <button type="button" className="mini-player-close" onClick={dismissMiniPlayer} title="关闭">
        ×
      </button>
    </div>
  )
}
