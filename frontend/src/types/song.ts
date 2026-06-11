/** GET /api/v1/songs/search 列表项 — 对齐 docs/api-contracts.md SongSummary */
export interface SongSummary {
  netease_song_id: number
  song_name: string
  artist_name: string
  cover_url: string
  album_name?: string
  duration_ms?: number
  is_original?: boolean
  vip_only?: boolean
  playable?: boolean
}

export interface PlayUrl {
  url: string
  expires_in: number
  quality: string
  fallback_url: string | null
}

export interface PlayerSong {
  netease_song_id: number
  song_name: string
  artist_name: string
  cover_url: string
  reason?: string
  is_original?: boolean
  vip_only?: boolean
  playable?: boolean
}
