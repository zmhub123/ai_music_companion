import { useEffect, useRef, useState } from 'react'
import { Button, Progress, Spin } from 'antd'
import { CloseOutlined } from '@ant-design/icons'
import { resolveChordShape } from '../../constants/chordShapes'
import { getScoreChordLines } from '../../mocks/score'
import { isScoreLoadAbortError, loadScoreWithProgress, ScoreJobError } from '../../services/scoreService'
import { useAuthStore } from '../../stores/authStore'
import { usePlayerStore } from '../../stores/playerStore'
import { useScoreStore } from '../../stores/scoreStore'
import type { ScoreData } from '../../types/score'
import ChordDiagram from './ChordDiagram'
import RhythmPattern from './RhythmPattern'
import ScoreLyricsPanel from './ScoreLyricsPanel'

export default function ScorePanel() {
  const instrument = useScoreStore((s) => s.instrument)
  const vocalVersion = useScoreStore((s) => s.vocalVersion)
  const closePanel = useScoreStore((s) => s.closePanel)
  const setInstrument = useScoreStore((s) => s.setInstrument)
  const setVocalVersion = useScoreStore((s) => s.setVocalVersion)
  const currentSong = usePlayerStore((s) => s.currentSong)
  const openNeteaseLogin = useAuthStore((s) => s.openNeteaseLogin)
  const scoreRetryNonce = useAuthStore((s) => s.scoreRetryNonce)

  const [score, setScore] = useState<ScoreData | null>(null)
  const [error, setError] = useState('')
  const [fetching, setFetching] = useState(false)
  const [progress, setProgress] = useState(0)
  const [stageLabel, setStageLabel] = useState('准备生成曲谱…')
  const loadTokenRef = useRef(0)

  useEffect(() => {
    const loadToken = ++loadTokenRef.current
    const abort = new AbortController()
    const songId = currentSong.netease_song_id

    setFetching(true)
    setError('')
    setScore(null)
    setProgress(0)
    setStageLabel('准备生成曲谱…')

    void (async () => {
      try {
        const data = await loadScoreWithProgress(
          songId,
          instrument,
          vocalVersion,
          (job) => {
            if (loadToken !== loadTokenRef.current) return
            setProgress(job.progress)
            setStageLabel(job.stage_label || job.stage)
          },
          abort.signal,
        )
        if (loadToken !== loadTokenRef.current) return
        setScore(data)
        setError('')
      } catch (e) {
        if (loadToken !== loadTokenRef.current || isScoreLoadAbortError(e)) return
        setScore(null)
        if (e instanceof ScoreJobError && e.code === 'NEED_NETEASE_LOGIN') {
          setError('需要登录网易云账号后才能生成曲谱')
          openNeteaseLogin()
        } else if (e instanceof ScoreJobError && e.code === 'VIP_REQUIRED') {
          setError('抱歉，呜呜音源要钱')
        } else {
          setError(e instanceof Error ? e.message : '加载失败')
        }
      } finally {
        if (loadToken === loadTokenRef.current) {
          setFetching(false)
        }
      }
    })()

    return () => {
      abort.abort()
    }
  }, [instrument, vocalVersion, currentSong.netease_song_id, openNeteaseLogin, scoreRetryNonce])

  const loading = fetching
  const stringCount = instrument === 'guitar' ? 6 : 4
  const uniqueChords = score
    ? [
        ...new Set(
          score.lines.flatMap((line) =>
            (line.chord_marks?.length
              ? line.chord_marks.map((mark) => mark.chord)
              : line.chord.split(/\s+/))
              .filter(Boolean),
          ),
        ),
      ]
    : getScoreChordLines(instrument).unique

  return (
    <aside className="score-side-panel">
      <div className="score-header">
        <div className="score-header-text">
          <h3>{currentSong.song_name}</h3>
          <span className="score-header-sub">弹唱谱</span>
        </div>
        <Button type="text" size="small" icon={<CloseOutlined />} onClick={closePanel} aria-label="关闭曲谱" />
      </div>

      <div className="score-layout">
        <nav className="score-side-nav" aria-label="曲谱设置">
          <div className="score-nav-group">
            <span className="score-nav-label">乐器</span>
            <button
              type="button"
              className={`score-nav-btn${instrument === 'guitar' ? ' active' : ''}`}
              onClick={() => setInstrument('guitar')}
            >
              吉他
            </button>
            <button
              type="button"
              className={`score-nav-btn${instrument === 'ukulele' ? ' active' : ''}`}
              onClick={() => setInstrument('ukulele')}
            >
              尤克里里
            </button>
          </div>
          <div className="score-nav-group">
            <span className="score-nav-label">音色</span>
            <button
              type="button"
              className={`score-nav-btn${vocalVersion === 'male' ? ' active' : ''}`}
              onClick={() => setVocalVersion('male')}
            >
              男声
            </button>
            <button
              type="button"
              className={`score-nav-btn${vocalVersion === 'female' ? ' active' : ''}`}
              onClick={() => setVocalVersion('female')}
            >
              女声
            </button>
          </div>
        </nav>

        <div className="score-body">
          {loading && !error && (
            <div className="score-loading">
              <Spin />
              <p className="score-progress-label">{stageLabel}</p>
              <Progress percent={progress} status="active" />
            </div>
          )}
          {error && (
            <div className="score-error-block">
              <p className="score-error">{error}</p>
              {error.includes('登录网易云') && (
                <Button type="primary" size="small" onClick={openNeteaseLogin}>
                  扫码登录网易云
                </Button>
              )}
            </div>
          )}
          {!loading && !error && score && score.netease_song_id === currentSong.netease_song_id && (
            <div className="score-split">
              <div className="score-col-lyrics">
                {score.practice_tips && <p className="score-tips">{score.practice_tips}</p>}
                <ScoreLyricsPanel
                  key={`${score.netease_song_id}-${instrument}-${vocalVersion}`}
                  score={{ ...score, instrument }}
                  autoFollow
                />
              </div>
              <div className="score-col-charts">
                <div className="score-key-meta">
                  {score.key && <span>原调 {score.key}</span>}
                  <span>选调 {score.key || 'C'}</span>
                  {score.capo > 0 && <span>Capo {score.capo}</span>}
                  <span>编配 音伴 AI</span>
                </div>
                <div className="score-charts-block">
                  <div className="score-charts-label">和弦指法</div>
                  <div className="chord-diagrams-row">
                    {uniqueChords.map((name) => (
                      <ChordDiagram
                        key={name}
                        name={name}
                        shape={resolveChordShape(name, instrument) ?? { tops: [], dots: [] }}
                        stringCount={stringCount}
                      />
                    ))}
                  </div>
                </div>
                <RhythmPattern instrument={instrument} pattern={score.rhythm_pattern} />
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
