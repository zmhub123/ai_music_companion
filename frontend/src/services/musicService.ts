import axios from 'axios'
import { mockGetPlayUrl } from '../mocks/music'
import type { ApiResponse } from '../types/api'
import type { PlayUrl, SongSummary } from '../types/song'
import api, { rethrowApiError, useMusicMock } from './api'

export class PlayUrlError extends Error {
  fallbackUrl: string | null
  vipRequired: boolean
  needNeteaseLogin: boolean

  constructor(
    message: string,
    fallbackUrl: string | null = null,
    vipRequired = false,
    needNeteaseLogin = false,
  ) {
    super(message)
    this.name = 'PlayUrlError'
    this.fallbackUrl = fallbackUrl
    this.vipRequired = vipRequired
    this.needNeteaseLogin = needNeteaseLogin
  }
}

export async function searchSongs(query: string, limit = 10): Promise<SongSummary[]> {
  if (useMusicMock) {
    const { searchMockSongs } = await import('../mocks/songs')
    return searchMockSongs(query).slice(0, limit)
  }

  try {
    const { data } = await api.get<ApiResponse<{ items: SongSummary[] }>>('/v1/songs/search', {
      params: { q: query, limit },
    })
    if (data.code !== 200 || !data.data) throw new Error(data.message)
    return data.data.items
  } catch (err) {
    rethrowApiError(err)
  }
}

export async function getSong(neteaseSongId: number): Promise<SongSummary & { netease_url?: string }> {
  if (useMusicMock) {
    const { MOCK_SONGS } = await import('../mocks/songs')
    const song = MOCK_SONGS.find((s) => s.netease_song_id === neteaseSongId)
    if (!song) throw new Error('歌曲不存在')
    return song
  }

  try {
    const { data } = await api.get<ApiResponse<SongSummary & { netease_url?: string }>>(
      `/v1/songs/${neteaseSongId}`,
    )
    if (data.code !== 200 || !data.data) throw new Error(data.message)
    return data.data
  } catch (err) {
    rethrowApiError(err)
  }
}

export async function getPlayUrl(neteaseSongId: number): Promise<PlayUrl> {
  if (useMusicMock) {
    await new Promise((r) => setTimeout(r, 600))
    const res = mockGetPlayUrl(neteaseSongId)
    if (res.code !== 200 || !res.data) throw new Error(res.message)
    return res.data
  }

  try {
    const { data } = await api.get<ApiResponse<PlayUrl>>(`/v1/songs/${neteaseSongId}/play-url`)
    if (data.code !== 200 || !data.data) throw new Error(data.message)
    return data.data
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 500) {
      const body = err.response.data as ApiResponse<{ fallback_url?: string }>
      if (body.code === 50004) {
        const payload = body.data as
          | { fallback_url?: string; vip_required?: boolean; need_netease_login?: boolean }
          | undefined
        throw new PlayUrlError(
          body.message,
          payload?.fallback_url ?? null,
          Boolean(payload?.vip_required),
          Boolean(payload?.need_netease_login),
        )
      }
    }
    rethrowApiError(err)
  }
}
