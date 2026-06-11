import { useEffect, useMemo, useState } from 'react'
import { App, Button, Input } from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import { getPlaylist, removeSongFromPlaylist } from '../services/playlistService'
import { usePlayerStore } from '../stores/playerStore'
import type { PlaylistDetail } from '../types/playlist'

export default function PlaylistDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { message } = App.useApp()
  const playSong = usePlayerStore((s) => s.playSong)
  const [detail, setDetail] = useState<PlaylistDetail | null>(null)
  const [query, setQuery] = useState('')

  const load = async () => {
    if (!id) return
    try {
      setDetail(await getPlaylist(id))
    } catch {
      message.error('歌单不存在')
      navigate('/playlists')
    }
  }

  useEffect(() => {
    if (!id) return
    let cancelled = false
    void (async () => {
      try {
        const data = await getPlaylist(id)
        if (!cancelled) setDetail(data)
      } catch {
        if (!cancelled) {
          message.error('歌单不存在')
          navigate('/playlists')
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [id, message, navigate])

  const songs = useMemo(() => {
    if (!detail) return []
    const q = query.trim().toLowerCase()
    if (!q) return detail.songs
    return detail.songs.filter(
      (s) => s.song_name.toLowerCase().includes(q) || s.artist_name.toLowerCase().includes(q),
    )
  }, [detail, query])

  if (!detail) return null

  return (
    <div className="page-content">
      <span className="back-link" onClick={() => navigate('/playlists')}>
        ← 返回歌单
      </span>
      <div className="page-header-row page-header-row--detail">
        <div>
          <h2>{detail.name}</h2>
          <p className="page-desc page-desc--inline">
            {detail.description} · {detail.song_count} 首
          </p>
        </div>
      </div>
      <div className="page-toolbar">
        <Input
          allowClear
          prefix={<span className="search-icon">⌕</span>}
          placeholder="在歌单内搜索歌曲"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      <div className="song-table">
        {songs.map((song) => (
          <div key={song.id} className="song-table-row">
            <button
              type="button"
              className="song-play-btn"
              aria-label="播放"
              onClick={() => {
                void playSong({
                  netease_song_id: song.netease_song_id,
                  song_name: song.song_name,
                  artist_name: song.artist_name,
                  cover_url: song.cover_url,
                })
                navigate('/player')
              }}
            >
              ▶
            </button>
            <div className="song-cover">封面</div>
            <div className="song-info">
              <div className="name">{song.song_name}</div>
              <div className="artist">{song.artist_name}</div>
            </div>
            <Button
              type="link"
              danger
              onClick={() =>
                void removeSongFromPlaylist(detail.id, song.id).then(() => {
                  message.success('已移除')
                  void load()
                })
              }
            >
              移除
            </Button>
          </div>
        ))}
      </div>
      {songs.length === 0 && <p className="search-empty">歌单内没有匹配的歌曲</p>}
    </div>
  )
}
