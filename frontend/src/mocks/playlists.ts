import type { ApiResponse } from '../types/api'
import type {
  AddSongToPlaylistRequest,
  CreatePlaylistRequest,
  PlaylistDetail,
  PlaylistSong,
  PlaylistSummary,
} from '../types/playlist'

const STORAGE_KEY = 'yinban_playlists_mock'

interface PlaylistRecord extends PlaylistSummary {
  songs: PlaylistSong[]
}

let plSeq = 3
let plsSeq = 10

function nextPlId() {
  plSeq += 1
  return `pl-${String(plSeq).padStart(3, '0')}`
}

function nextPlsId() {
  plsSeq += 1
  return `pls-${String(plsSeq).padStart(3, '0')}`
}

const DEFAULT_PLAYLISTS: PlaylistRecord[] = [
  {
    id: 'pl-001',
    name: '今晚治愈',
    description: '适合疲惫夜晚的安静歌单',
    cover_url: 'https://p1.music.126.net/example.jpg',
    song_count: 3,
    created_at: '2026-06-07T08:00:00Z',
    updated_at: '2026-06-07T11:00:00Z',
    songs: [
      {
        id: 'pls-001',
        netease_song_id: 100001,
        song_name: '夜航船',
        artist_name: '示例歌手',
        cover_url: 'https://p1.music.126.net/example.jpg',
        added_at: '2026-06-07T09:00:00Z',
      },
      {
        id: 'pls-002',
        netease_song_id: 100002,
        song_name: '半句再见',
        artist_name: '示例歌手',
        cover_url: 'https://p1.music.126.net/example2.jpg',
        added_at: '2026-06-07T09:30:00Z',
      },
      {
        id: 'pls-003',
        netease_song_id: 100003,
        song_name: '云上.walk',
        artist_name: '示例歌手',
        cover_url: 'https://p1.music.126.net/example3.jpg',
        added_at: '2026-06-07T10:00:00Z',
      },
    ],
  },
  {
    id: 'pl-002',
    name: '周末练琴',
    description: '适合周末练习的弹唱曲',
    cover_url: null,
    song_count: 2,
    created_at: '2026-06-07T08:30:00Z',
    updated_at: '2026-06-07T10:30:00Z',
    songs: [
      {
        id: 'pls-004',
        netease_song_id: 100004,
        song_name: '木吉他练习曲',
        artist_name: '示例歌手',
        cover_url: 'https://p1.music.126.net/example4.jpg',
        added_at: '2026-06-07T10:00:00Z',
      },
      {
        id: 'pls-005',
        netease_song_id: 100001,
        song_name: '夜航船',
        artist_name: '示例歌手',
        cover_url: 'https://p1.music.126.net/example.jpg',
        added_at: '2026-06-07T10:15:00Z',
      },
    ],
  },
]

function loadPlaylists(): PlaylistRecord[] {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return DEFAULT_PLAYLISTS.map((p) => ({ ...p, songs: [...p.songs] }))
  return JSON.parse(raw) as PlaylistRecord[]
}

function savePlaylists(list: PlaylistRecord[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
}

function toSummary(p: PlaylistRecord): PlaylistSummary {
  return {
    id: p.id,
    name: p.name,
    description: p.description,
    cover_url: p.cover_url,
    song_count: p.songs.length,
    created_at: p.created_at,
    updated_at: p.updated_at,
  }
}

export function mockListPlaylists(): ApiResponse<{ items: PlaylistSummary[]; total: number }> {
  const items = loadPlaylists()
    .map(toSummary)
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
  return { code: 200, message: 'success', data: { items, total: items.length } }
}

export function mockCreatePlaylist(
  payload: CreatePlaylistRequest,
): ApiResponse<PlaylistSummary> {
  const now = new Date().toISOString()
  const record: PlaylistRecord = {
    id: nextPlId(),
    name: payload.name,
    description: payload.description,
    cover_url: null,
    song_count: 0,
    created_at: now,
    updated_at: now,
    songs: [],
  }
  const list = loadPlaylists()
  list.unshift(record)
  savePlaylists(list)
  return { code: 200, message: 'success', data: toSummary(record) }
}

export function mockGetPlaylist(id: string): ApiResponse<PlaylistDetail> {
  const p = loadPlaylists().find((x) => x.id === id)
  if (!p) return { code: 40401, message: '歌单不存在', data: null }
  return {
    code: 200,
    message: 'success',
    data: { ...toSummary(p), songs: p.songs },
  }
}

export function mockDeletePlaylist(id: string): ApiResponse<{ deleted: boolean; playlist_id: string }> {
  const list = loadPlaylists()
  const next = list.filter((p) => p.id !== id)
  if (next.length === list.length) return { code: 40401, message: '歌单不存在', data: null }
  savePlaylists(next)
  return { code: 200, message: 'success', data: { deleted: true, playlist_id: id } }
}

export function mockAddSongToPlaylist(
  playlistId: string,
  payload: AddSongToPlaylistRequest,
): ApiResponse<PlaylistSong> {
  const list = loadPlaylists()
  const p = list.find((x) => x.id === playlistId)
  if (!p) return { code: 40401, message: '歌单不存在', data: null }
  if (p.songs.some((s) => s.netease_song_id === payload.netease_song_id)) {
    return { code: 40001, message: '歌曲已在歌单中', data: null }
  }
  const song: PlaylistSong = {
    id: nextPlsId(),
    ...payload,
    added_at: new Date().toISOString(),
  }
  p.songs.push(song)
  p.song_count = p.songs.length
  p.updated_at = song.added_at
  savePlaylists(list)
  return { code: 200, message: 'success', data: song }
}

export function mockRemoveSongFromPlaylist(
  playlistId: string,
  playlistSongId: string,
): ApiResponse<{ deleted: boolean; playlist_song_id: string }> {
  const list = loadPlaylists()
  const p = list.find((x) => x.id === playlistId)
  if (!p) return { code: 40401, message: '歌单不存在', data: null }
  const before = p.songs.length
  p.songs = p.songs.filter((s) => s.id !== playlistSongId)
  if (p.songs.length === before) {
    return { code: 40402, message: '歌曲不存在', data: null }
  }
  p.song_count = p.songs.length
  p.updated_at = new Date().toISOString()
  savePlaylists(list)
  return { code: 200, message: 'success', data: { deleted: true, playlist_song_id: playlistSongId } }
}

export function mockClearPlaylists(): void {
  localStorage.removeItem(STORAGE_KEY)
}
