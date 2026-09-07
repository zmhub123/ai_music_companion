import type { ChordShape, ScoreInstrument } from '../types/score'

export const GUITAR_CHORD_SHAPES: Record<string, ChordShape> = {
  C: {
    tops: ['×', '○', '', '○', '', '○'],
    dots: [
      { s: 2, f: 3, n: 3 },
      { s: 3, f: 2, n: 2 },
      { s: 5, f: 1, n: 1 },
    ],
  },
  Cmaj7: {
    tops: ['×', '○', '', '○', '', '○'],
    dots: [
      { s: 2, f: 3, n: 3 },
      { s: 3, f: 2, n: 2 },
      { s: 4, f: 2, n: 2 },
      { s: 5, f: 1, n: 1 },
    ],
  },
  Dm: {
    tops: ['×', '×', '○', '', '', '×'],
    dots: [
      { s: 2, f: 3, n: 3 },
      { s: 3, f: 2, n: 2 },
      { s: 4, f: 1, n: 1 },
    ],
  },
  Dm7: {
    tops: ['×', '×', '○', '', '', '×'],
    dots: [
      { s: 2, f: 3, n: 3 },
      { s: 3, f: 2, n: 2 },
      { s: 4, f: 1, n: 1 },
      { s: 5, f: 1, n: 1 },
    ],
  },
  Em: {
    tops: ['', '', '', '', '', '○'],
    dots: [
      { s: 2, f: 2, n: 2 },
      { s: 3, f: 2, n: 3 },
      { s: 4, f: 1, n: 1 },
    ],
  },
  Em7: {
    tops: ['', '', '', '', '', '○'],
    dots: [
      { s: 2, f: 2, n: 2 },
      { s: 3, f: 2, n: 3 },
      { s: 4, f: 1, n: 1 },
      { s: 5, f: 1, n: 1 },
    ],
  },
  E7: {
    tops: ['', '', '', '', '', '○'],
    dots: [
      { s: 2, f: 2, n: 2 },
      { s: 3, f: 1, n: 1 },
      { s: 4, f: 2, n: 3 },
      { s: 5, f: 1, n: 1 },
    ],
  },
  Am: {
    tops: ['×', '○', '', '', '', '○'],
    dots: [
      { s: 3, f: 2, n: 2 },
      { s: 4, f: 2, n: 3 },
      { s: 5, f: 1, n: 1 },
    ],
  },
  Am7: {
    tops: ['×', '○', '', '', '', '○'],
    dots: [
      { s: 3, f: 2, n: 2 },
      { s: 4, f: 2, n: 3 },
      { s: 5, f: 1, n: 1 },
      { s: 6, f: 1, n: 1 },
    ],
  },
  F: {
    tops: ['', '', '', '', '', ''],
    barre: { from: 1, to: 6, fret: 1 },
    dots: [
      { s: 3, f: 2, n: 2 },
      { s: 4, f: 3, n: 3 },
      { s: 5, f: 3, n: 4 },
    ],
  },
  Fm: {
    tops: ['', '', '', '', '', ''],
    barre: { from: 1, to: 6, fret: 1 },
    dots: [
      { s: 2, f: 2, n: 1 },
      { s: 3, f: 3, n: 3 },
      { s: 4, f: 3, n: 4 },
    ],
  },
  G: {
    tops: ['', '', '○', '○', '○', ''],
    dots: [
      { s: 1, f: 3, n: 4 },
      { s: 2, f: 2, n: 1 },
      { s: 6, f: 3, n: 3 },
    ],
  },
  Gmaj7: {
    tops: ['', '', '○', '○', '○', ''],
    dots: [
      { s: 1, f: 2, n: 1 },
      { s: 2, f: 2, n: 1 },
      { s: 6, f: 3, n: 3 },
    ],
  },
  B7: {
    tops: ['×', '○', '', '', '', '○'],
    dots: [
      { s: 3, f: 2, n: 2 },
      { s: 4, f: 1, n: 1 },
      { s: 5, f: 2, n: 3 },
    ],
  },
  Bm: {
    tops: ['×', '○', '', '', '', '○'],
    dots: [
      { s: 2, f: 3, n: 3 },
      { s: 3, f: 4, n: 4 },
      { s: 4, f: 2, n: 2 },
      { s: 5, f: 1, n: 1 },
    ],
  },
  Bm7: {
    tops: ['×', '○', '', '', '', '○'],
    dots: [
      { s: 2, f: 3, n: 3 },
      { s: 3, f: 2, n: 2 },
      { s: 4, f: 2, n: 2 },
      { s: 5, f: 1, n: 1 },
    ],
  },
  Gsus4: {
    tops: ['', '', '○', '○', '○', ''],
    dots: [
      { s: 1, f: 3, n: 4 },
      { s: 2, f: 3, n: 2 },
      { s: 6, f: 3, n: 3 },
    ],
  },
  Gm: {
    tops: ['', '', '', '', '', ''],
    barre: { from: 1, to: 6, fret: 3 },
    dots: [
      { s: 2, f: 4, n: 2 },
      { s: 3, f: 4, n: 3 },
      { s: 4, f: 4, n: 4 },
    ],
  },
  Gm7: {
    tops: ['', '', '', '', '', ''],
    dots: [
      { s: 1, f: 3, n: 4 },
      { s: 2, f: 3, n: 3 },
      { s: 3, f: 3, n: 2 },
      { s: 4, f: 3, n: 1 },
      { s: 5, f: 1, n: 1 },
      { s: 6, f: 3, n: 2 },
    ],
  },
  Cm: {
    tops: ['×', '', '', '', '', '×'],
    dots: [
      { s: 2, f: 4, n: 2 },
      { s: 3, f: 5, n: 3 },
      { s: 4, f: 5, n: 4 },
    ],
  },
  Cm7: {
    tops: ['×', '', '', '', '', '×'],
    dots: [
      { s: 2, f: 4, n: 2 },
      { s: 3, f: 3, n: 1 },
      { s: 4, f: 3, n: 3 },
      { s: 5, f: 3, n: 4 },
    ],
  },
  Ebmaj7: {
    tops: ['×', '×', '', '', '', ''],
    dots: [
      { s: 4, f: 1, n: 1 },
      { s: 3, f: 3, n: 3 },
      { s: 2, f: 3, n: 4 },
      { s: 1, f: 3, n: 2 },
    ],
  },
  Abmaj7: {
    tops: ['', '×', '', '', '', '×'],
    barre: { from: 1, to: 4, fret: 4 },
    dots: [
      { s: 1, f: 4, n: 1 },
      { s: 2, f: 4 },
      { s: 3, f: 5, n: 2 },
      { s: 4, f: 5, n: 3 },
      { s: 5, f: 4 },
    ],
  },
  D7: {
    tops: ['×', '×', '○', '', '', '×'],
    dots: [
      { s: 2, f: 2, n: 1 },
      { s: 3, f: 2, n: 2 },
      { s: 4, f: 1, n: 3 },
    ],
  },
  A7: {
    tops: ['×', '○', '', '', '', '○'],
    dots: [
      { s: 3, f: 2, n: 2 },
      { s: 4, f: 2, n: 3 },
      { s: 5, f: 2, n: 1 },
    ],
  },
}

export const UKULELE_CHORD_SHAPES: Record<string, ChordShape> = {
  C: { tops: ['○', '○', '○', ''], dots: [{ s: 4, f: 3, n: 3 }] },
  Am: { tops: ['', '○', '', '○'], dots: [{ s: 2, f: 2, n: 1 }] },
  Dm: {
    tops: ['', '○', '', '○'],
    dots: [
      { s: 1, f: 1, n: 1 },
      { s: 2, f: 2, n: 2 },
      { s: 3, f: 2, n: 3 },
    ],
  },
  Em: {
    tops: ['', '○', '', '○'],
    dots: [
      { s: 1, f: 2, n: 2 },
      { s: 2, f: 4, n: 4 },
      { s: 3, f: 3, n: 3 },
    ],
  },
  E7: {
    tops: ['', '○', '', '○'],
    dots: [
      { s: 1, f: 1, n: 1 },
      { s: 2, f: 2, n: 2 },
      { s: 3, f: 2, n: 3 },
    ],
  },
  F: { tops: ['', '○', '', '○'], dots: [{ s: 1, f: 2, n: 1 }, { s: 3, f: 1, n: 2 }] },
  G: {
    tops: ['', '', '', ''],
    dots: [
      { s: 1, f: 2, n: 1 },
      { s: 2, f: 3, n: 3 },
      { s: 3, f: 2, n: 2 },
      { s: 4, f: 3, n: 4 },
    ],
  },
  Gm7: {
    tops: ['', '○', '', '○'],
    dots: [
      { s: 1, f: 2, n: 1 },
      { s: 2, f: 2, n: 2 },
      { s: 3, f: 2, n: 3 },
    ],
  },
  Cm7: {
    tops: ['', '○', '', '○'],
    dots: [
      { s: 1, f: 3, n: 2 },
      { s: 2, f: 3, n: 3 },
      { s: 3, f: 3, n: 4 },
    ],
  },
  Ebmaj7: {
    tops: ['', '○', '', '○'],
    dots: [
      { s: 1, f: 1, n: 1 },
      { s: 2, f: 2, n: 2 },
      { s: 3, f: 2, n: 3 },
    ],
  },
  Abmaj7: {
    tops: ['', '', '', ''],
    dots: [
      { s: 1, f: 1, n: 1 },
      { s: 2, f: 1, n: 2 },
      { s: 3, f: 2, n: 3 },
      { s: 4, f: 2, n: 4 },
    ],
  },
}

const CHORD_ALIASES: Record<string, string> = {
  D: 'Dm',
  A: 'Am',
  B: 'G',
  'D#maj7': 'Ebmaj7',
  'G#maj7': 'Abmaj7',
}

/** 升号根音统一为降号等价和弦名，便于查表 */
const ENHARMONIC_ROOT: Record<string, string> = {
  'D#': 'Eb',
  'G#': 'Ab',
  'A#': 'Bb',
  'C#': 'Db',
  'F#': 'Gb',
}

function canonicalChordName(chordName: string): string {
  const trimmed = chordName.trim()
  for (const [sharp, flat] of Object.entries(ENHARMONIC_ROOT)) {
    if (trimmed.startsWith(sharp)) {
      return flat + trimmed.slice(sharp.length)
    }
  }
  return trimmed
}

function chordLookupCandidates(chordName: string): string[] {
  const raw = chordName.trim()
  const canonical = canonicalChordName(raw)
  const candidates = new Set<string>([raw, canonical])

  const add = (name: string) => {
    if (name) candidates.add(name)
  }

  for (const name of [raw, canonical]) {
    if (/m7$/i.test(name)) {
      const root = name.replace(/m7$/i, '')
      add(name)
      add(`${root}m`)
      add(root)
    } else if (/maj7$/i.test(name)) {
      const root = name.replace(/maj7$/i, '')
      add(name)
      add(root)
    } else if (/7$/i.test(name)) {
      const root = name.replace(/7$/i, '')
      add(name)
      add(root)
    } else if (/m$/i.test(name) && !/maj/i.test(name)) {
      const root = name.replace(/m$/i, '')
      add(name)
      add(root)
    } else if (/sus4$/i.test(name)) {
      add('Gsus4')
    }
  }

  const withAliases = [...candidates]
  for (const name of withAliases) {
    const alias = CHORD_ALIASES[name]
    if (alias) candidates.add(alias)
  }

  return [...candidates]
}

export function resolveChordShape(
  chordName: string,
  instrument: ScoreInstrument,
): ChordShape | undefined {
  const bank = instrument === 'guitar' ? GUITAR_CHORD_SHAPES : UKULELE_CHORD_SHAPES
  for (const candidate of chordLookupCandidates(chordName)) {
    if (bank[candidate]) return bank[candidate]
  }
  return undefined
}
