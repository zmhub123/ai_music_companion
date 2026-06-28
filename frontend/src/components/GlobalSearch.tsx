import { useEffect, useState } from 'react'
import { Input, List, message } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { searchSongs } from '../services/musicService'
import { useMusicMock } from '../services/api'
import { usePlayerStore } from '../stores/playerStore'
import type { PlayerSong, SongSummary } from '../types/song'

function toPlayerSong(item: SongSummary): PlayerSong {
  return {
    netease_song_id: item.netease_song_id,
    song_name: item.song_name,
    artist_name: item.artist_name,
    cover_url: item.cover_url,
    reason: '搜索命中',
    is_original: item.is_original,
    vip_only: item.vip_only,
    playable: item.playable,
  }
}

export default function GlobalSearch() {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [results, setResults] = useState<SongSummary[]>([])
  const navigate = useNavigate()
  const playSong = usePlayerStore((s) => s.playSong)
  const setRecommendations = usePlayerStore((s) => s.setRecommendations)
  const trimmedQuery = query.trim()
  const displayResults = trimmedQuery ? results : []

  useEffect(() => {
    if (!trimmedQuery) return
    if (useMusicMock) {
      void import('../mocks/songs').then(({ searchMockSongs }) => {
        setResults(searchMockSongs(trimmedQuery))
      })
      return
    }
    const timer = window.setTimeout(() => {
      void searchSongs(trimmedQuery, 8)
        .then(setResults)
        .catch(() => setResults([]))
    }, 300)
    return () => window.clearTimeout(timer)
  }, [trimmedQuery])

  const handleSelect = async (item: SongSummary) => {
    const songs = displayResults.map(toPlayerSong)
    setRecommendations(songs)
    setQuery('')
    setOpen(false)
    navigate('/player')
    const err = await playSong(toPlayerSong(item))
    if (err) message.warning(err)
  }

  return (
    <div className="header-search">
      <Input
        allowClear
        prefix={<SearchOutlined />}
        placeholder="搜索歌曲、歌手"
        value={query}
        onChange={(e) => {
          const value = e.target.value
          setQuery(value)
          if (!value.trim()) setResults([])
          setOpen(!!value.trim())
        }}
        onFocus={() => setOpen(!!query.trim())}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onPressEnter={() => {
          if (displayResults[0]) {
            void handleSelect(displayResults[0])
          }
        }}
      />
      {open && trimmedQuery && (
        <div className="header-search-dropdown">
          {displayResults.length === 0 ? (
            <div className="header-search-empty">未找到相关歌曲</div>
          ) : (
            <List
              size="small"
              dataSource={displayResults}
              renderItem={(item) => (
                <List.Item
                  className="header-search-item"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => {
                    void handleSelect(item)
                  }}
                >
                  <div>
                    <div className="header-search-name">{item.song_name}</div>
                    <div className="header-search-artist">{item.artist_name}</div>
                  </div>
                </List.Item>
              )}
            />
          )}
        </div>
      )}
    </div>
  )
}
