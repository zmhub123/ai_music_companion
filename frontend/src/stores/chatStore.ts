import { create } from 'zustand'
import {
  getMessages,
  resetChat,
  sendMessage as sendChatMessage,
} from '../services/chatService'
import type { ChatMessage, SongRecommendation } from '../types/api'
import { usePlayerStore } from './playerStore'

export type ChatFloatState = 'open' | 'minimized' | 'closed'

interface ChatState {
  messages: ChatMessage[]
  loading: boolean
  sending: boolean
  floatState: ChatFloatState
  playerChatDocked: boolean
  fetchMessages: () => Promise<void>
  sendMessage: (content: string) => Promise<void>
  resetConversation: () => Promise<void>
  openChat: () => void
  minimizeChat: () => void
  closeChat: () => void
  enterPlayerChatDock: () => void
  exitPlayerChatDock: () => void
  openPlayerChatFromDock: () => void
  syncForRoute: (pathname: string) => void
}

function toPlayerSong(rec: SongRecommendation) {
  return {
    netease_song_id: rec.netease_song_id,
    song_name: rec.song_name,
    artist_name: rec.artist_name,
    cover_url: rec.cover_url,
    reason: rec.reason,
    is_original: rec.is_original,
    vip_only: rec.vip_only,
    playable: rec.playable,
  }
}

function syncRecommendationsToPlayer(recs: SongRecommendation[] | undefined) {
  if (!recs?.length) return
  usePlayerStore.getState().setRecommendations(recs.map(toPlayerSong))
}

async function autoPlayIfRequested(
  recs: SongRecommendation[] | undefined,
  autoPlay: boolean | undefined,
) {
  if (!autoPlay || !recs?.[0]) return
  await usePlayerStore.getState().playSong(toPlayerSong(recs[0]))
}

const PENDING_USER_PREFIX = 'pending-user-'
const PENDING_AI_PREFIX = 'pending-ai-'

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  loading: false,
  sending: false,
  floatState: 'closed',
  playerChatDocked: false,

  fetchMessages: async () => {
    set({ loading: true })
    try {
      const messages = await getMessages()
      set({ loading: false, messages })
      const latestRecs = [...messages]
        .reverse()
        .find((m) => m.metadata?.recommendations?.length)?.metadata?.recommendations
      syncRecommendationsToPlayer(latestRecs)
    } catch {
      set({ loading: false })
    }
  },

  sendMessage: async (content) => {
    const text = content.trim()
    if (!text || get().sending) return

    const now = new Date().toISOString()
    const optimisticUser: ChatMessage = {
      id: `${PENDING_USER_PREFIX}${Date.now()}`,
      role: 'user',
      content: text,
      metadata: null,
      created_at: now,
    }
    const optimisticAssistant: ChatMessage = {
      id: `${PENDING_AI_PREFIX}${Date.now()}`,
      role: 'assistant',
      content: '',
      metadata: { pending: true },
      created_at: now,
    }

    set((state) => ({
      sending: true,
      messages: [...state.messages, optimisticUser, optimisticAssistant],
    }))

    try {
      const res = await sendChatMessage(text)
      set((state) => ({
        sending: false,
        messages: [
          ...state.messages.filter(
            (msg) =>
              !msg.id.startsWith(PENDING_USER_PREFIX) && !msg.id.startsWith(PENDING_AI_PREFIX),
          ),
          res.user_message,
          res.assistant_message,
        ],
      }))
      const meta = res.assistant_message.metadata
      syncRecommendationsToPlayer(meta?.recommendations)
      void autoPlayIfRequested(meta?.recommendations, meta?.auto_play)
    } catch (err) {
      set((state) => ({
        sending: false,
        messages: state.messages.filter(
          (msg) =>
            !msg.id.startsWith(PENDING_USER_PREFIX) && !msg.id.startsWith(PENDING_AI_PREFIX),
        ),
      }))
      throw err
    }
  },

  resetConversation: async () => {
    await resetChat()
    set({ messages: [] })
  },

  openChat: () => set({ floatState: 'open', playerChatDocked: false }),

  minimizeChat: () =>
    set((state) => ({
      floatState: 'minimized',
      playerChatDocked: state.playerChatDocked,
    })),

  closeChat: () => set({ floatState: 'closed', playerChatDocked: false }),

  enterPlayerChatDock: () => set({ playerChatDocked: true, floatState: 'minimized' }),

  exitPlayerChatDock: () => set({ playerChatDocked: false, floatState: 'open' }),

  openPlayerChatFromDock: () => set({ playerChatDocked: true, floatState: 'open' }),

  syncForRoute: (pathname) => {
    if (pathname === '/') {
      set({ floatState: 'closed', playerChatDocked: false })
      return
    }
    if (pathname.startsWith('/player')) {
      const { playerChatDocked } = get()
      if (!playerChatDocked) {
        set({ floatState: 'open' })
      }
      return
    }
    const { floatState } = get()
    if (floatState === 'open') {
      set({ floatState: 'minimized' })
    }
  },
}))
