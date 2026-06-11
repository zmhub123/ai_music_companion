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
}

const CHORD_ALIASES: Record<string, string> = {
  D: 'Dm',
  A: 'Am',
  B: 'G',
}

export function resolveChordShape(
  chordName: string,
  instrument: ScoreInstrument,
): ChordShape | undefined {
  const bank = instrument === 'guitar' ? GUITAR_CHORD_SHAPES : UKULELE_CHORD_SHAPES
  const trimmed = chordName.trim()
  if (bank[trimmed]) return bank[trimmed]

  const alias = CHORD_ALIASES[trimmed]
  if (alias && bank[alias]) return bank[alias]

  const withoutSuffix = trimmed.replace(/maj7$/i, 'maj7').replace(/sus4$/i, 'Gsus4')
  if (bank[withoutSuffix]) return bank[withoutSuffix]

  const base = trimmed.replace(/maj7$/i, '').replace(/sus4$/i, '').replace(/7$/i, '')
  if (bank[base]) return bank[base]
  if (bank[`${base}m`]) return bank[`${base}m`]

  return undefined
}
