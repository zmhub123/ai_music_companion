export interface PlaylistSummary {
  id: string
  name: string
  description: string
  cover_url: string | null
  song_count: number
  created_at: string
  updated_at: string
}

export interface PlaylistSong {
  id: string
  netease_song_id: number
  song_name: string
  artist_name: string
  cover_url: string
  added_at: string
}

export interface PlaylistDetail extends PlaylistSummary {
  songs: PlaylistSong[]
}

export interface CreatePlaylistRequest {
  name: string
  description: string
}

export interface AddSongToPlaylistRequest {
  netease_song_id: number
  song_name: string
  artist_name: string
  cover_url: string
}
