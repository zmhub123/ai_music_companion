import type { RhythmPatternData, ScoreInstrument } from '../../types/score'

const FALLBACK_PATTERNS = {
  guitar: {
    label: '节奏型 · 4/4 基础扫弦',
    names: ['e', 'B', 'G', 'D', 'A', 'E'],
    rows: [
      ['', '', '×', '', '', ''],
      ['', '×', '', '×', '', ''],
      ['', '', '×', '', '×', ''],
      ['', '', '', '×', '', ''],
      ['×', '', '', '', '', ''],
      ['', '', '', '', '', ''],
    ],
    beats: ['↓', '', '↑↓', '', '↑', ''],
  },
  ukulele: {
    label: '节奏型 · 4/4 慢板扫弦',
    names: ['A', 'E', 'C', 'G'],
    rows: [
      ['', '', '', '×'],
      ['', '×', '', ''],
      ['×', '', '×', ''],
      ['', '', '×', ''],
    ],
    beats: ['↓', '—', '↑', '↓'],
  },
}

interface RhythmPatternProps {
  instrument: ScoreInstrument
  pattern?: RhythmPatternData | null
}

function arrowPath(direction: 'down' | 'up', cx: number, top: number, bottom: number) {
  const mid = (top + bottom) / 2
  const h = (bottom - top) * 0.32
  if (direction === 'down') {
    return `M ${cx} ${mid - h} L ${cx} ${mid + h} M ${cx - 4} ${mid + h - 5} L ${cx} ${mid + h} L ${cx + 4} ${mid + h - 5}`
  }
  return `M ${cx} ${mid + h} L ${cx} ${mid - h} M ${cx - 4} ${mid - h + 5} L ${cx} ${mid - h} L ${cx + 4} ${mid - h + 5}`
}

export default function RhythmPattern({ instrument, pattern }: RhythmPatternProps) {
  const pat = pattern ?? FALLBACK_PATTERNS[instrument]
  const subtitle = pat.label.includes('·') ? pat.label.split('·').slice(1).join('·').trim() : pat.label
  const stringCount = pat.names.length
  const beatCols = pat.beats.length

  const padX = 10
  const padTop = 22
  const stringGap = 11
  const colGap = 18
  const gridW = padX * 2 + (beatCols - 1) * colGap
  const gridTop = padTop
  const gridBottom = padTop + (stringCount - 1) * stringGap
  const svgH = gridBottom + 36

  return (
    <div className="rhythm-pattern-card">
      <div className="rhythm-pattern-head">
        <span className="rhythm-badge">节奏型</span>
        <span className="rhythm-subtitle">{subtitle}</span>
      </div>
      <svg
        className="rhythm-pattern-svg"
        width={gridW}
        height={svgH}
        viewBox={`0 0 ${gridW} ${svgH}`}
        aria-label="扫弦节奏型"
      >
        {Array.from({ length: stringCount }, (_, i) => {
          const y = gridTop + i * stringGap
          return (
            <line
              key={`s-${i}`}
              x1={padX - 4}
              y1={y}
              x2={gridW - padX + 4}
              y2={y}
              className="rhythm-svg-string"
            />
          )
        })}

        {pat.beats.map((_, i) => {
          const cx = padX + i * colGap
          return (
            <line
              key={`col-${i}`}
              x1={cx}
              y1={gridTop - 4}
              x2={cx}
              y2={gridBottom + 4}
              className="rhythm-svg-beat-line"
            />
          )
        })}

        {pat.beats.map((beat, i) => {
          const cx = padX + i * colGap
          if (beat === '↓') {
            return (
              <path
                key={`arrow-${i}`}
                d={arrowPath('down', cx, gridTop, gridBottom)}
                className="rhythm-svg-arrow down"
              />
            )
          }
          if (beat === '↑' || beat === '↑↓') {
            return (
              <path
                key={`arrow-${i}`}
                d={arrowPath('up', cx, gridTop, gridBottom)}
                className="rhythm-svg-arrow up"
              />
            )
          }
          return null
        })}

        {pat.beats.map((beat, i) => {
          const cx = padX + i * colGap
          const stemBottom = svgH - 6
          const stemTop = gridBottom + 8
          if (!beat || beat === '—' || beat === '-') {
            return (
              <text key={`rest-${i}`} x={cx} y={stemBottom - 2} textAnchor="middle" className="rhythm-svg-rest">
                —
              </text>
            )
          }
          return (
            <g key={`stem-${i}`}>
              <line x1={cx} y1={stemTop} x2={cx} y2={stemBottom} className="rhythm-svg-stem" />
              {i % 2 === 1 && i > 0 ? (
                <line
                  x1={cx - colGap}
                  y1={stemBottom}
                  x2={cx}
                  y2={stemBottom}
                  className="rhythm-svg-beam"
                />
              ) : null}
            </g>
          )
        })}
      </svg>
    </div>
  )
}
