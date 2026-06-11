import { create } from 'zustand'
import { DEFAULT_PLAYER_SONG, SEED_RECOMMENDATIONS } from '../constants/seedSongs'
import { getPlayUrl, PlayUrlError } from '../services/musicService'
import type { PlayerSong } from '../types/song'
import { confirmVipPlayback, neteaseSongUrl } from '../utils/playConfirm'

let audioEl: HTMLAudioElement | null = null
let loadedSongId: number | null = null
let preloadGeneration = 0
const playUrlCache = new Map<number, { url: string; expiresAt: number }>()

const MOCK_SONG_ID_THRESHOLD = 1_000_000

function getAudio() {
  if (!audioEl) {
    audioEl = new Audio()
    audioEl.preload = 'auto'
  }
  return audioEl
}

function resolveAudioUrl(url: string): string {
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  if (url.startsWith('/')) return `${window.location.origin}${url}`
  return url
}

function resetAudioElement() {
  const audio = getAudio()
  audio.pause()
  audio.removeAttribute('src')
  audio.load()
  loadedSongId = null
}

function getCachedPlayUrl(songId: number): string | null {
  const cached = playUrlCache.get(songId)
  if (cached && Date.now() < cached.expiresAt) return cached.url
  if (cached) playUrlCache.delete(songId)
  return null
}

function cachePlayUrl(songId: number, url: string, expiresInSec: number) {
  playUrlCache.set(songId, {
    url,
    expiresAt: Date.now() + Math.max(expiresInSec * 1000 - 60_000, 30_000),
  })
}

async function resolvePlayUrl(songId: number): Promise<string> {
  const cached = getCachedPlayUrl(songId)
  if (cached) return cached

  const { url, expires_in: expiresIn } = await getPlayUrl(songId)
  cachePlayUrl(songId, url, expiresIn)
  return url
}

function preloadAudioSrc(songId: number, url: string, generation: number) {
  if (generation !== preloadGeneration) return

  const audio = getAudio()
  const resolved = resolveAudioUrl(url)
  if (loadedSongId === songId && audio.src === resolved) return

  audio.pause()
  audio.src = resolved
  audio.load()
  loadedSongId = songId
}

export async function prefetchPlayUrl(songId: number): Promise<void> {
  const cached = getCachedPlayUrl(songId)
  if (cached) return
  try {
    await resolvePlayUrl(songId)
  } catch {
    // 预取失败不影响后续点击播放
  }
}

interface PlayerState {
  recommendations: PlayerSong[]
  currentSong: PlayerSong
  playing: boolean
  loading: boolean
  progress: number
  duration: number
  miniPlayerVisible: boolean
  playlistDrawerOpen: boolean
  setRecommendations: (songs: PlayerSong[]) => void
  openPlaylistDrawer: () => void
  closePlaylistDrawer: () => void
  togglePlaylistDrawer: () => void
  selectSong: (song: PlayerSong) => void
  playSong: (song: PlayerSong) => Promise<string | null>
  togglePlay: () => Promise<string | null>
  pause: () => void
  seek: (ratio: number) => void
  tickProgress: () => void
  dismissMiniPlayer: () => void
}

export const usePlayerStore = create<PlayerState>((set, get) => ({
  recommendations: SEED_RECOMMENDATIONS.map((r) => ({
    netease_song_id: r.netease_song_id,
    song_name: r.song_name,
    artist_name: r.artist_name,
    cover_url: r.cover_url,
    reason: r.reason,
    is_original: r.is_original,
    vip_only: r.vip_only,
    playable: r.playable,
  })),
  currentSong: DEFAULT_PLAYER_SONG,
  playing: false,
  loading: false,
  progress: 0,
  duration: 0,
  miniPlayerVisible: false,
  playlistDrawerOpen: false,

  openPlaylistDrawer: () => set({ playlistDrawerOpen: true }),
  closePlaylistDrawer: () => set({ playlistDrawerOpen: false }),
  togglePlaylistDrawer: () => set((s) => ({ playlistDrawerOpen: !s.playlistDrawerOpen })),

  setRecommendations: (songs) => {
    if (!songs.length) return
    const { currentSong } = get()
    const shouldSyncCurrent =
      currentSong.netease_song_id < MOCK_SONG_ID_THRESHOLD ||
      !songs.some((song) => song.netease_song_id === currentSong.netease_song_id)

    preloadGeneration += 1
    if (shouldSyncCurrent) {
      resetAudioElement()
    }

    set({
      recommendations: songs,
      ...(shouldSyncCurrent
        ? { currentSong: songs[0], playing: false, progress: 0, duration: 0 }
        : {}),
    })
    songs.slice(0, 3).forEach((song) => {
      void prefetchPlayUrl(song.netease_song_id)
    })
  },

  selectSong: (song) => {
    preloadGeneration += 1
    if (loadedSongId !== song.netease_song_id) {
      resetAudioElement()
    }
    set({ currentSong: song, playing: false, progress: 0, duration: 0 })
    void prefetchPlayUrl(song.netease_song_id)
  },

  playSong: async (song): Promise<string | null> => {
    if (song.vip_only && song.playable === false) {
      const jumped = await confirmVipPlayback(
        song.song_name,
        neteaseSongUrl(song.netease_song_id),
      )
      return jumped ? null : '已取消播放'
    }

    const audio = getAudio()
    const generation = ++preloadGeneration
    const sameLoaded = loadedSongId === song.netease_song_id && Boolean(audio.src)

    if (!sameLoaded) {
      if (loadedSongId !== null && loadedSongId !== song.netease_song_id) {
        resetAudioElement()
      }
      set({ loading: true, currentSong: song, progress: 0 })
    }

    try {
      const url = await resolvePlayUrl(song.netease_song_id)
      if (generation !== preloadGeneration) return null
      preloadAudioSrc(song.netease_song_id, url, generation)

      await audio.play()
      set({
        currentSong: song,
        playing: true,
        loading: false,
        miniPlayerVisible: true,
        duration: audio.duration && Number.isFinite(audio.duration) ? audio.duration : get().duration,
      })
      return null
    } catch (err) {
      if (loadedSongId === song.netease_song_id) {
        resetAudioElement()
      }
      set({ playing: false, loading: false })
      if (err instanceof PlayUrlError) {
        if (err.needNeteaseLogin) {
          const { confirmNeteaseLogin } = await import('../utils/playConfirm')
          const { useAuthStore } = await import('./authStore')
          const ok = await confirmNeteaseLogin(err.message || '登录网易云后可尝试播放并生成曲谱')
          if (ok) useAuthStore.getState().openNeteaseLogin()
          return '需要登录网易云'
        }
        if (err.vipRequired) {
          const { showVipPaidMessage, confirmVipPlayback } = await import('../utils/playConfirm')
          if (err.message.includes('呜呜音源要钱')) {
            showVipPaidMessage()
            return err.message
          }
          if (err.fallbackUrl) {
            const jumped = await confirmVipPlayback(song.song_name, err.fallbackUrl)
            return jumped ? null : '已取消播放'
          }
        }
        return err.fallbackUrl
      }
      return err instanceof Error ? err.message : '播放失败'
    }
  },

  togglePlay: async (): Promise<string | null> => {
    const { playing, currentSong, loading } = get()
    if (loading) return null

    if (playing) {
      getAudio().pause()
      set({ playing: false })
      return null
    }

    const audio = getAudio()
    if (loadedSongId !== null && loadedSongId !== currentSong.netease_song_id) {
      resetAudioElement()
    }
    if (loadedSongId === currentSong.netease_song_id && audio.src) {
      try {
        await audio.play()
        set({
          playing: true,
          duration: audio.duration && Number.isFinite(audio.duration) ? audio.duration : get().duration,
        })
        return null
      } catch {
        // 音频源失效时回退到完整加载流程
      }
    }

    return get().playSong(currentSong)
  },

  pause: () => {
    getAudio().pause()
    set({ playing: false })
  },

  seek: (ratio) => {
    const audio = getAudio()
    const duration = audio.duration
    if (!duration || !Number.isFinite(duration)) return
    const next = Math.max(0, Math.min(1, ratio)) * duration
    audio.currentTime = next
    set({ progress: next, duration })
  },

  tickProgress: () => {
    const audio = getAudio()
    if (!get().playing) return
    set({
      progress: audio.currentTime,
      duration: audio.duration && Number.isFinite(audio.duration) ? audio.duration : get().duration,
    })
  },

  dismissMiniPlayer: () => {
    getAudio().pause()
    set({ playing: false, miniPlayerVisible: false })
  },
}))

export function bindAudioEnded(onEnded: () => void) {
  const audio = getAudio()
  audio.onended = onEnded
}
