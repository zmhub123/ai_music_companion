import { create } from 'zustand'
import {
  getNeteaseAuthStatus,
  logoutNetease,
  type NeteaseAuthStatus,
} from '../services/neteaseAuthService'
import { getGuestMe } from '../services/guestService'

interface AuthState {
  guestReady: boolean
  netease: NeteaseAuthStatus
  neteaseLoginOpen: boolean
  scoreRetryNonce: number
  refreshAuth: () => Promise<void>
  logoutNeteaseAccount: () => Promise<void>
  openNeteaseLogin: () => void
  closeNeteaseLogin: () => void
  bumpScoreRetry: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  guestReady: false,
  netease: { logged_in: false, nickname: null },
  neteaseLoginOpen: false,
  scoreRetryNonce: 0,
  refreshAuth: async () => {
    await getGuestMe()
    const netease = await getNeteaseAuthStatus()
    set({ guestReady: true, netease })
  },
  logoutNeteaseAccount: async () => {
    const netease = await logoutNetease()
    set({ netease })
  },
  openNeteaseLogin: () => set({ neteaseLoginOpen: true }),
  closeNeteaseLogin: () => set({ neteaseLoginOpen: false }),
  bumpScoreRetry: () => set((s) => ({ scoreRetryNonce: s.scoreRetryNonce + 1 })),
}))
