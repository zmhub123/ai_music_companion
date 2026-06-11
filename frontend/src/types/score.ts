import type { SkillLevel } from './api'

export type ScoreInstrument = 'guitar' | 'ukulele'

export type ScoreLineSection = 'intro' | 'vocal' | 'verse' | 'chorus'
export type VocalVersion = 'male' | 'female'

export interface ChordMark {
  position: number
  chord: string
}

export interface ScoreLine {
  position: number
  chord: string
  lyric_line: string
  section?: ScoreLineSection
  start_ms?: number
  chord_marks?: ChordMark[]
}

export interface RhythmPatternData {
  label: string
  names: string[]
  rows: string[][]
  beats: string[]
}

export interface ScoreData {
  netease_song_id: number
  song_name: string
  artist_name: string
  cover_url: string
  instrument: ScoreInstrument
  skill_level: SkillLevel
  key: string
  capo: number
  lines: ScoreLine[]
  practice_tips: string | null
  rhythm_pattern?: RhythmPatternData | null
  intro_duration_ms?: number
  duration_ms?: number | null
  lyric_source?: 'netease' | 'seed'
  vocal_version?: VocalVersion
  chord_source?: string
}

export interface ChordDot {
  s: number
  f: number
  n?: number
}

export interface ChordShape {
  tops: string[]
  dots: ChordDot[]
  barre?: { from: number; to: number; fret: number }
}

export interface LyricChordLine {
  section?: string
  lyric: string
  chords: { name: string; at: number }[]
}
