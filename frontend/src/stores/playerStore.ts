import { create } from 'zustand'
import { EMPTY_PLAYER_SONG } from '../constants/seedSongs'
import { getPlayUrl, PlayUrlError } from '../services/musicService'
import type { PlayUrl, PlayerSong } from '../types/song'
import { confirmVipPlayback, neteaseSongUrl, showVipTrialNotice } from '../utils/playConfirm'

let audioEl: HTMLAudioElement | null = null
let loadedSongId: number | null = null
let preloadGeneration = 0
const playUrlCache = new Map<number, { meta: PlayUrl; expiresAt: number }>()

const MOCK_SONG_ID_THRESHOLD = 1_000_000

export type PlayMode = 'sequential' | 'loop' | 'shuffle'

const PLAY_MODE_CYCLE: PlayMode[] = ['sequential', 'loop', 'shuffle']

export const PLAY_MODE_LABELS: Record<PlayMode, string> = {
  sequential: '顺序播放',
  loop: '单曲循环',
  shuffle: '随机播放',
}

function playableList(recommendations: PlayerSong[]): PlayerSong[] {
  return recommendations.filter((song) => song.netease_song_id > 0)
}

function songIndex(list: PlayerSong[], songId: number): number {
  return list.findIndex((song) => song.netease_song_id === songId)
}

function pickShuffleNext(list: PlayerSong[], currentId: number): PlayerSong | null {
  if (!list.length) return null
  const others = list.filter((song) => song.netease_song_id !== currentId)
  if (others.length) return others[Math.floor(Math.random() * others.length)] ?? null
  return list[0] ?? null
}

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

function getCachedPlayUrl(songId: number): PlayUrl | null {
  const cached = playUrlCache.get(songId)
  if (cached && Date.now() < cached.expiresAt) return cached.meta
  if (cached) playUrlCache.delete(songId)
  return null
}

function cachePlayUrl(songId: number, meta: PlayUrl, expiresInSec: number) {
  playUrlCache.set(songId, {
    meta,
    expiresAt: Date.now() + Math.max(expiresInSec * 1000 - 60_000, 30_000),
  })
}

async function resolvePlayUrl(songId: number): Promise<PlayUrl> {
  const cached = getCachedPlayUrl(songId)
  if (cached) {
    const { useAuthStore } = await import('./authStore')
    const loggedIn = useAuthStore.getState().netease.logged_in
    // 登录后丢弃登录前缓存的 VIP 试听地址
    if (!loggedIn || !cached.vip_trial) return cached
    playUrlCache.delete(songId)
  }

  const meta = await getPlayUrl(songId)
  cachePlayUrl(songId, meta, meta.expires_in)
  return meta
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

/** 网易云登录态变化后须清空，避免继续播放登录前的 VIP 试听缓存 */
export function clearPlaybackCache(): void {
  playUrlCache.clear()
  preloadGeneration += 1
  resetAudioElement()
}

interface PlayerState {
  recommendations: PlayerSong[]
  recommendationsReady: boolean
  currentSong: PlayerSong
  playing: boolean
  loading: boolean
  progress: number
  duration: number
  miniPlayerVisible: boolean
  playlistDrawerOpen: boolean
  playMode: PlayMode
  setRecommendations: (songs: PlayerSong[]) => void
  openPlaylistDrawer: () => void
  closePlaylistDrawer: () => void
  togglePlaylistDrawer: () => void
  selectSong: (song: PlayerSong) => void
  playSong: (song: PlayerSong) => Promise<string | null>
  playNext: () => Promise<string | null>
  playPrevious: () => Promise<string | null>
  cyclePlayMode: () => void
  handleTrackEnd: () => Promise<void>
  togglePlay: () => Promise<string | null>
  pause: () => void
  seek: (ratio: number) => void
  tickProgress: () => void
  dismissMiniPlayer: () => void
  resetAfterGuestClear: () => void
}

export const usePlayerStore = create<PlayerState>((set, get) => ({
  recommendations: [],
  recommendationsReady: false,
  currentSong: EMPTY_PLAYER_SONG,
  playing: false,
  loading: false,
  progress: 0,
  duration: 0,
  miniPlayerVisible: false,
  playlistDrawerOpen: false,
  playMode: 'sequential',

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
      recommendationsReady: true,
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
    if (song.netease_song_id <= 0) {
      return '请先选择歌曲'
    }

    const { useAuthStore } = await import('./authStore')
    const neteaseLoggedIn = useAuthStore.getState().netease.logged_in

    if (song.vip_only && song.playable === false && !neteaseLoggedIn) {
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
      const playMeta = await resolvePlayUrl(song.netease_song_id)
      if (generation !== preloadGeneration) return null
      preloadAudioSrc(song.netease_song_id, playMeta.url, generation)

      await audio.play()
      if (playMeta.vip_trial) {
        showVipTrialNotice(song.song_name, playMeta.trial_duration_sec ?? 30)
      }
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

  playNext: async (): Promise<string | null> => {
    const { currentSong, recommendations, loading, playMode } = get()
    if (loading || currentSong.netease_song_id <= 0) return null

    const list = playableList(recommendations)
    if (list.length <= 1) return '没有下一首'

    const idx = songIndex(list, currentSong.netease_song_id)
    let next: PlayerSong | null = null

    if (playMode === 'shuffle') {
      next = pickShuffleNext(list, currentSong.netease_song_id)
    } else if (idx >= 0 && idx < list.length - 1) {
      next = list[idx + 1] ?? null
    }

    if (!next) return '没有下一首'
    return get().playSong(next)
  },

  playPrevious: async (): Promise<string | null> => {
    const { currentSong, recommendations, loading } = get()
    if (loading || currentSong.netease_song_id <= 0) return null

    const list = playableList(recommendations)
    if (list.length <= 1) return '没有上一首'

    const idx = songIndex(list, currentSong.netease_song_id)
    if (idx <= 0) return '没有上一首'

    const prev = list[idx - 1]
    if (!prev) return '没有上一首'
    return get().playSong(prev)
  },

  cyclePlayMode: () => {
    const { playMode } = get()
    const nextIdx = (PLAY_MODE_CYCLE.indexOf(playMode) + 1) % PLAY_MODE_CYCLE.length
    set({ playMode: PLAY_MODE_CYCLE[nextIdx] })
  },

  handleTrackEnd: async () => {
    const { playMode, currentSong, recommendations } = get()
    if (currentSong.netease_song_id <= 0) return

    if (playMode === 'loop') {
      await get().playSong(currentSong)
      return
    }

    const list = playableList(recommendations)
    if (!list.length) {
      get().pause()
      set({ progress: 0 })
      return
    }

    if (playMode === 'shuffle') {
      const next = pickShuffleNext(list, currentSong.netease_song_id)
      if (next) {
        await get().playSong(next)
      } else {
        get().pause()
        set({ progress: 0 })
      }
      return
    }

    const idx = songIndex(list, currentSong.netease_song_id)
    if (idx >= 0 && idx < list.length - 1) {
      await get().playSong(list[idx + 1]!)
      return
    }

    get().pause()
    set({ progress: 0 })
  },

  togglePlay: async (): Promise<string | null> => {
    const { playing, currentSong, loading } = get()
    if (loading || currentSong.netease_song_id <= 0) return null

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

  resetAfterGuestClear: () => {
    clearPlaybackCache()
    set({
      recommendations: [],
      recommendationsReady: false,
      currentSong: EMPTY_PLAYER_SONG,
      playing: false,
      loading: false,
      progress: 0,
      duration: 0,
      miniPlayerVisible: false,
      playlistDrawerOpen: false,
      playMode: 'sequential',
    })
  },
}))

export function bindAudioEnded(onEnded: () => void) {
  const audio = getAudio()
  audio.onended = onEnded
}
