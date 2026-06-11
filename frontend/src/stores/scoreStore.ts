import { create } from 'zustand'
import { useChatStore } from './chatStore'
import type { VocalVersion } from '../types/score'

export type ScoreInstrument = 'guitar' | 'ukulele'

interface ScoreState {
  open: boolean
  modalOpen: boolean
  instrument: ScoreInstrument
  vocalVersion: VocalVersion
  openGenerateModal: () => void
  closeGenerateModal: () => void
  confirmGenerate: (instrument: ScoreInstrument, vocalVersion: VocalVersion) => void
  closePanel: () => void
  setInstrument: (instrument: ScoreInstrument) => void
  setVocalVersion: (vocalVersion: VocalVersion) => void
}

export const useScoreStore = create<ScoreState>((set) => ({
  open: false,
  modalOpen: false,
  instrument: 'guitar',
  vocalVersion: 'male',
  openGenerateModal: () => set({ modalOpen: true }),
  closeGenerateModal: () => set({ modalOpen: false }),
  confirmGenerate: (instrument, vocalVersion) => {
    useChatStore.getState().enterPlayerChatDock()
    set({ modalOpen: false, open: true, instrument, vocalVersion })
  },
  closePanel: () => {
    useChatStore.getState().exitPlayerChatDock()
    set({ open: false })
  },
  setInstrument: (instrument) => set({ instrument }),
  setVocalVersion: (vocalVersion) => set({ vocalVersion }),
}))
