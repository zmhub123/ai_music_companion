import {
  mockAddSongToPlaylist,
  mockCreatePlaylist,
  mockDeletePlaylist,
  mockGetPlaylist,
  mockListPlaylists,
  mockRemoveSongFromPlaylist,
} from '../mocks/playlists'
import type { ApiResponse } from '../types/api'
import type {
  AddSongToPlaylistRequest,
  CreatePlaylistRequest,
  PlaylistDetail,
  PlaylistSong,
  PlaylistSummary,
} from '../types/playlist'
import axios from 'axios'
import api, { rethrowApiError, usePlaylistMock } from './api'
import { ensureGuestSession } from './guestService'

async function withGuestAuth<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request()
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      await ensureGuestSession()
      try {
        return await request()
      } catch (retryErr) {
        rethrowApiError(retryErr)
      }
    }
    rethrowApiError(err)
  }
}

export async function listPlaylists(): Promise<PlaylistSummary[]> {
  if (usePlaylistMock) {
    const res = mockListPlaylists()
    if (res.code !== 200 || !res.data) throw new Error(res.message)
    return res.data.items
  }
  const { data } = await withGuestAuth(() =>
    api.get<ApiResponse<{ items: PlaylistSummary[] }>>('/v1/playlists'),
  )
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data.items
}

export async function createPlaylist(payload: CreatePlaylistRequest): Promise<PlaylistSummary> {
  if (usePlaylistMock) {
    const res = mockCreatePlaylist(payload)
    if (res.code !== 200 || !res.data) throw new Error(res.message)
    return res.data
  }
  const { data } = await withGuestAuth(() =>
    api.post<ApiResponse<PlaylistSummary>>('/v1/playlists', payload),
  )
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export async function getPlaylist(id: string): Promise<PlaylistDetail> {
  if (usePlaylistMock) {
    const res = mockGetPlaylist(id)
    if (res.code !== 200 || !res.data) throw new Error(res.message)
    return res.data
  }
  const { data } = await withGuestAuth(() =>
    api.get<ApiResponse<PlaylistDetail>>(`/v1/playlists/${id}`),
  )
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export async function deletePlaylist(id: string): Promise<void> {
  if (usePlaylistMock) {
    const res = mockDeletePlaylist(id)
    if (res.code !== 200) throw new Error(res.message)
    return
  }
  const { data } = await withGuestAuth(() =>
    api.delete<ApiResponse<unknown>>(`/v1/playlists/${id}`),
  )
  if (data.code !== 200) throw new Error(data.message)
}

export async function addSongToPlaylist(
  playlistId: string,
  payload: AddSongToPlaylistRequest,
): Promise<PlaylistSong> {
  if (usePlaylistMock) {
    const res = mockAddSongToPlaylist(playlistId, payload)
    if (res.code !== 200 || !res.data) throw new Error(res.message)
    return res.data
  }
  const { data } = await withGuestAuth(() =>
    api.post<ApiResponse<PlaylistSong>>(`/v1/playlists/${playlistId}/songs`, payload),
  )
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export async function removeSongFromPlaylist(
  playlistId: string,
  playlistSongId: string,
): Promise<void> {
  if (usePlaylistMock) {
    const res = mockRemoveSongFromPlaylist(playlistId, playlistSongId)
    if (res.code !== 200) throw new Error(res.message)
    return
  }
  const { data } = await withGuestAuth(() =>
    api.delete<ApiResponse<unknown>>(
      `/v1/playlists/${playlistId}/songs/${playlistSongId}`,
    ),
  )
  if (data.code !== 200) throw new Error(data.message)
}
