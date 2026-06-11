import type { ChordShape } from '../../types/score'

interface ChordDiagramProps {
  name: string
  shape: ChordShape
  stringCount: number
}

const STRING_GAP = 12
const FRET_H = 14
const PAD_X = 8
const PAD_TOP = 18
const NUT_H = 2.5

function stringX(index: number) {
  return PAD_X + index * STRING_GAP
}

export default function ChordDiagram({ name, shape, stringCount }: ChordDiagramProps) {
  const frets = 4
  const cols = Array.from({ length: stringCount }, (_, i) => i)
  const topMarks = shape.tops.length ? shape.tops : cols.map(() => '')
  const boardW = PAD_X * 2 + (stringCount - 1) * STRING_GAP
  const boardH = PAD_TOP + NUT_H + frets * FRET_H + 8
  const nutY = PAD_TOP + NUT_H

  const fretLine = (f: number) => nutY + f * FRET_H
  const dotY = (fret: number) => nutY + (fret - 0.5) * FRET_H

  return (
    <div className="chord-diagram">
      <div className="chord-diagram-name">{name}</div>
      <svg
        className="chord-diagram-svg"
        width={boardW}
        height={boardH}
        viewBox={`0 0 ${boardW} ${boardH}`}
        aria-label={`${name} 和弦指法`}
      >
        {cols.map((i) => {
          const mark = topMarks[i] || ''
          const x = stringX(i)
          if (mark === '×') {
            return (
              <text key={`top-${i}`} x={x} y={PAD_TOP - 6} textAnchor="middle" className="chord-svg-muted">
                ×
              </text>
            )
          }
          if (mark === '○' || mark === '0') {
            return (
              <circle key={`top-${i}`} cx={x} cy={PAD_TOP - 4} r={3} className="chord-svg-open" />
            )
          }
          if (mark) {
            return (
              <text key={`top-${i}`} x={x} y={PAD_TOP - 5} textAnchor="middle" className="chord-svg-fret-num">
                {mark}
              </text>
            )
          }
          return null
        })}

        <rect x={PAD_X - 1} y={PAD_TOP} width={boardW - PAD_X * 2 + 2} height={NUT_H} className="chord-svg-nut" />

        {Array.from({ length: frets + 1 }, (_, f) => (
          <line
            key={`fret-${f}`}
            x1={PAD_X - 1}
            y1={fretLine(f)}
            x2={boardW - PAD_X + 1}
            y2={fretLine(f)}
            className="chord-svg-fret-line"
          />
        ))}

        {cols.map((i) => (
          <line
            key={`string-${i}`}
            x1={stringX(i)}
            y1={PAD_TOP}
            x2={stringX(i)}
            y2={fretLine(frets)}
            className="chord-svg-string"
          />
        ))}

        {shape.barre ? (
          <rect
            x={stringX(shape.barre.from - 1) - 6}
            y={dotY(shape.barre.fret) - 5}
            width={stringX(shape.barre.to - 1) - stringX(shape.barre.from - 1) + 12}
            height={10}
            rx={5}
            className="chord-svg-barre"
          />
        ) : null}

        {shape.dots.map((dot) => {
          const x = stringX(dot.s - 1)
          const y = dotY(dot.f)
          return (
            <g key={`dot-${dot.s}-${dot.f}`}>
              <circle cx={x} cy={y} r={5.5} className="chord-svg-dot" />
              {dot.n ? (
                <text x={x} y={y + 3} textAnchor="middle" className="chord-svg-finger">
                  {dot.n}
                </text>
              ) : null}
            </g>
          )
        })}
      </svg>
    </div>
  )
}
