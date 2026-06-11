import { getScoreChordLines } from '../../mocks/score'
import type { ScoreInstrument, ScoreLine } from '../../types/score'

interface LyricChordLinesProps {
  instrument: ScoreInstrument
  lines?: ScoreLine[]
  activeLineIndex?: number
  neteaseStyle?: boolean
}

function buildChordMap(line: ScoreLine): Record<number, string> {
  const map: Record<number, string> = {}
  if (line.chord_marks?.length) {
    for (const mark of line.chord_marks) {
      map[mark.position] = mark.chord
    }
    return map
  }
  if (line.chord) {
    map[line.position ?? 0] = line.chord
  }
  return map
}

export default function LyricChordLines({
  instrument,
  lines,
  activeLineIndex = -1,
  neteaseStyle = false,
}: LyricChordLinesProps) {
  const displayLines: ScoreLine[] = lines?.length
    ? lines
    : getScoreChordLines(instrument).lines.map((line) => ({
        position: line.chords[0]?.at ?? 0,
        chord: line.chords.map((c) => c.name).join(' '),
        lyric_line: line.lyric,
        section: line.section as ScoreLine['section'],
        chord_marks: line.chords.map((c) => ({ position: c.at, chord: c.name })),
      }))

  const firstIntroIndex = displayLines.findIndex((line) => line.section === 'intro')

  return (
    <div className={`lyrics-block${neteaseStyle ? ' netease-style' : ''}`}>
      {displayLines.map((line, index) => {
        const chordMap = buildChordMap(line)
        const chars = [...line.lyric_line]
        const isIntro = line.section === 'intro'
        const showIntroTag = index === firstIntroIndex && firstIntroIndex >= 0

        return (
          <div
            key={`${line.lyric_line}-${index}`}
            data-line-index={index}
            className={`lyric-line${neteaseStyle ? ' netease' : ''}${index === activeLineIndex ? ' active' : ''}${isIntro ? ' intro' : ''}`}
          >
            {showIntroTag && <span className="lyric-section-tag">前奏</span>}
            <div className={`lyric-chars${neteaseStyle ? ' centered' : ''}`}>
              {chars.map((ch, charIndex) => (
                <span key={`${index}-${charIndex}`} className="char-cell">
                  <span className="chord-slot">{chordMap[charIndex] || ''}</span>
                  <span className="char">{ch === ' ' ? '\u00a0' : ch}</span>
                </span>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
