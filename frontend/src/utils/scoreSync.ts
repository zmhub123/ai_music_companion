import type { ScoreLine } from '../types/score'

export function findActiveLineIndex(lines: ScoreLine[], currentMs: number): number {
  if (!lines.length) return 0

  let active = 0
  for (let i = 0; i < lines.length; i += 1) {
    const start = lines[i].start_ms
    if (start != null && currentMs >= start) {
      active = i
    }
  }
  return active
}

export function formatScoreTime(ms: number): string {
  const totalSec = Math.max(0, Math.floor(ms / 1000))
  const min = Math.floor(totalSec / 60)
  const sec = totalSec % 60
  return `${min}:${sec.toString().padStart(2, '0')}`
}
