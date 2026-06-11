import type { SongSummary } from '../types/song'

export const MOCK_SONGS: SongSummary[] = [
  {
    netease_song_id: 100001,
    song_name: '[Mock] 夜航船',
    artist_name: '示例歌手',
    cover_url: '',
  },
  {
    netease_song_id: 100002,
    song_name: '[Mock] 半句再见',
    artist_name: '示例歌手',
    cover_url: '',
  },
  {
    netease_song_id: 100003,
    song_name: '[Mock] 云上.walk',
    artist_name: '示例歌手',
    cover_url: '',
  },
  {
    netease_song_id: 100004,
    song_name: '[Mock] 木吉他练习曲',
    artist_name: '示例歌手',
    cover_url: '',
  },
  {
    netease_song_id: 100005,
    song_name: '[Mock] 雨后街角',
    artist_name: '示例歌手',
    cover_url: '',
  },
]

export function searchMockSongs(query: string): SongSummary[] {
  const q = query.trim().toLowerCase()
  if (!q) return []
  return MOCK_SONGS.filter(
    (s) =>
      s.song_name.toLowerCase().includes(q) ||
      s.artist_name.toLowerCase().includes(q),
  )
}
