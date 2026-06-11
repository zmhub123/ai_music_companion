import { useCallback, useRef, useState } from 'react'
import ScorePanel from '../score/ScorePanel'
import { useScoreStore } from '../../stores/scoreStore'
import RecommendHoverRail from './RecommendHoverRail'
import RecommendList from './RecommendList'
import VinylPlayer from './VinylPlayer'

const MIN_PLAYER_W = 260
const MAX_PLAYER_W = 400
const DEFAULT_PLAYER_W = 300

export default function PlayerWorkbench() {
  const scoreOpen = useScoreStore((s) => s.open)
  const [playerWidth, setPlayerWidth] = useState(DEFAULT_PLAYER_W)
  const draggingRef = useRef(false)
  const splitRef = useRef<HTMLDivElement>(null)

  const onDividerMove = useCallback((clientX: number) => {
    const split = splitRef.current
    if (!split) return
    const rect = split.getBoundingClientRect()
    const next = clientX - rect.left
    setPlayerWidth(Math.min(MAX_PLAYER_W, Math.max(MIN_PLAYER_W, next)))
  }, [])

  const onDividerPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!scoreOpen) return
    draggingRef.current = true
    e.currentTarget.setPointerCapture(e.pointerId)
    onDividerMove(e.clientX)
  }

  const onDividerPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!draggingRef.current) return
    onDividerMove(e.clientX)
  }

  const onDividerPointerUp = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!draggingRef.current) return
    draggingRef.current = false
    e.currentTarget.releasePointerCapture(e.pointerId)
  }

  return (
    <div className={`page-player active${scoreOpen ? ' with-score' : ''}`}>
      {!scoreOpen ? <RecommendList /> : null}

      <div className="player-score-split" ref={splitRef}>
        <div
          className="player-stage"
          style={scoreOpen ? { width: playerWidth, maxWidth: playerWidth } : undefined}
        >
          {scoreOpen ? <RecommendHoverRail /> : null}
          <VinylPlayer />
        </div>

        {scoreOpen ? (
          <>
            <div
              className="score-split-handle"
              role="separator"
              aria-orientation="vertical"
              aria-label="调节播放器与曲谱宽度"
              onPointerDown={onDividerPointerDown}
              onPointerMove={onDividerPointerMove}
              onPointerUp={onDividerPointerUp}
              onPointerCancel={onDividerPointerUp}
            />
            <ScorePanel />
          </>
        ) : null}
      </div>
    </div>
  )
}
