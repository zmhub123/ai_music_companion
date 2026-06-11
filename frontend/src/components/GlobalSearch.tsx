import { useEffect, useState } from 'react'
import { Input, List } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { searchSongs } from '../services/musicService'
import { useMusicMock } from '../services/api'

export default function GlobalSearch() {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [results, setResults] = useState<{ netease_song_id: number; song_name: string; artist_name: string }[]>([])
  const navigate = useNavigate()
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
            setQuery('')
            setOpen(false)
            navigate('/player')
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
                    setQuery('')
                    setOpen(false)
                    navigate('/player')
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
