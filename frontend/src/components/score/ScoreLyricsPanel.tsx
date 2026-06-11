import { useEffect, useMemo, useRef, useState } from 'react'
import { Button } from 'antd'
import { CaretRightOutlined, PauseOutlined } from '@ant-design/icons'
import { usePlayerStore } from '../../stores/playerStore'
import type { ScoreData } from '../../types/score'
import { findActiveLineIndex, formatScoreTime } from '../../utils/scoreSync'
import LyricChordLines from './LyricChordLines'

interface ScoreLyricsPanelProps {
  score: ScoreData
  autoFollow?: boolean
}

export default function ScoreLyricsPanel({ score, autoFollow = false }: ScoreLyricsPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [followScroll, setFollowScroll] = useState(autoFollow)

  const currentSong = usePlayerStore((s) => s.currentSong)
  const playing = usePlayerStore((s) => s.playing)
  const progress = usePlayerStore((s) => s.progress)
  const playSong = usePlayerStore((s) => s.playSong)
  const togglePlay = usePlayerStore((s) => s.togglePlay)

  const sameSong = currentSong.netease_song_id === score.netease_song_id
  const lineCount = score.lines.length
  const needsScroll = autoFollow ? lineCount >= 2 : lineCount >= 8
  const currentMs = Math.round(progress * 1000)

  const activeLineIndex = useMemo(
    () => findActiveLineIndex(score.lines, currentMs),
    [score.lines, currentMs],
  )
  const activeFollowScroll = followScroll && playing

  useEffect(() => {
    if (!activeFollowScroll || !sameSong) return
    const container = scrollRef.current
    if (!container) return
    const target = container.querySelector<HTMLElement>(`[data-line-index="${activeLineIndex}"]`)
    if (!target) return
    const containerTop = container.scrollTop
    const containerBottom = containerTop + container.clientHeight
    const targetTop = target.offsetTop
    const targetBottom = targetTop + target.offsetHeight
    if (targetTop < containerTop + 40 || targetBottom > containerBottom - 40) {
      target.scrollIntoView({ block: 'center', behavior: 'smooth' })
    }
  }, [activeFollowScroll, sameSong, activeLineIndex])

  const handleFollowPlay = async () => {
    if (!sameSong) {
      await playSong({
        netease_song_id: score.netease_song_id,
        song_name: score.song_name,
        artist_name: score.artist_name,
        cover_url: score.cover_url,
      })
    } else if (!playing) {
      await togglePlay()
    }
    setFollowScroll(true)
  }

  const activeLine = score.lines[activeLineIndex]

  return (
    <section className="score-lyrics-section">
      <div className="score-lyrics-toolbar">
        <div className="score-meta">
          {activeFollowScroll && activeLine ? (
            <span className="score-sync-hint">
              {formatScoreTime(currentMs)} ·{' '}
              {activeLine.section === 'intro' ? '前奏' : activeLine.lyric_line.slice(0, 14)}
            </span>
          ) : (
            <span>{score.lines.length} 行歌词</span>
          )}
        </div>
        {needsScroll && (
          <Button
            type={activeFollowScroll ? 'primary' : 'default'}
            size="small"
            icon={activeFollowScroll ? <PauseOutlined /> : <CaretRightOutlined />}
            onClick={() => {
              if (activeFollowScroll) {
                void togglePlay()
                setFollowScroll(false)
                return
              }
              void handleFollowPlay()
            }}
          >
            {activeFollowScroll ? '暂停跟唱' : '跟唱滚动'}
          </Button>
        )}
      </div>
      <div
        ref={scrollRef}
        className={`score-lyrics-scroll${needsScroll ? ' scrollable' : ''}${activeFollowScroll ? ' following' : ''}`}
      >
        <LyricChordLines
          instrument={score.instrument}
          lines={score.lines}
          activeLineIndex={playing && sameSong ? activeLineIndex : -1}
          neteaseStyle={score.lyric_source === 'netease'}
        />
      </div>
    </section>
  )
}
