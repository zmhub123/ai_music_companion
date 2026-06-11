import { GUITAR_CHORD_SHAPES, UKULELE_CHORD_SHAPES } from '../constants/chordShapes'
import type { ApiResponse } from '../types/api'
import type { LyricChordLine, ScoreData, ScoreInstrument } from '../types/score'
import { mockGetGuestMe } from './guest'

const SCORE_SONG_IDS = [186016, 29715551, 478507889]

export { GUITAR_CHORD_SHAPES, UKULELE_CHORD_SHAPES }

const LYRIC_LINES: LyricChordLine[] = [
  { section: 'A', lyric: '后来 我总算学会了', chords: [{ name: 'Am', at: 0 }] },
  { lyric: '如何去爱', chords: [{ name: 'F', at: 0 }] },
  { lyric: '可惜你早已远去', chords: [{ name: 'C', at: 0 }] },
  { lyric: '消失在人海', chords: [{ name: 'G', at: 0 }] },
  {
    section: 'B',
    lyric: '后来 终于在眼泪中明白',
    chords: [
      { name: 'Am', at: 0 },
      { name: 'F', at: 6 },
    ],
  },
  {
    lyric: '有些人 一旦错过就不再',
    chords: [
      { name: 'C', at: 0 },
      { name: 'G', at: 10 },
    ],
  },
]

const UNIQUE_CHORDS = ['Am', 'F', 'C', 'G']

export function getScoreChordLines(instrument: ScoreInstrument) {
  return { unique: UNIQUE_CHORDS, lines: LYRIC_LINES, instrument }
}

function toApiLines(lines: LyricChordLine[]): ScoreData['lines'] {
  return lines.map((line) => ({
    position: line.chords[0]?.at ?? 0,
    chord: line.chords.map((c) => c.name).join(' '),
    lyric_line: line.lyric,
  }))
}

export function mockGetScore(
  neteaseSongId: number,
  instrument: ScoreInstrument,
): ApiResponse<ScoreData> {
  if (!SCORE_SONG_IDS.includes(neteaseSongId)) {
    return { code: 40403, message: '暂无该歌曲谱面数据', data: null }
  }

  const guest = mockGetGuestMe().data
  const skillLevel = guest?.skill_level ?? 'beginner'

  return {
    code: 200,
    message: 'success',
    data: {
      netease_song_id: neteaseSongId,
      song_name: neteaseSongId === 100001 ? '夜航船' : '木吉他练习曲',
      artist_name: '示例歌手',
      cover_url: 'https://p1.music.126.net/example.jpg',
      instrument,
      skill_level: skillLevel,
      key: 'G',
      capo: 0,
      lines: toApiLines(LYRIC_LINES),
      practice_tips:
        instrument === 'guitar'
          ? '整首歌以 G、Em、C、D 四个基础和弦循环，适合零基础练习扫弦节奏。'
          : '尤克里里版使用 Am、F、C、G，节奏轻柔，适合慢速扫弦。',
    },
  }
}

export const MOCK_SCORE_SONG_IDS = SCORE_SONG_IDS
