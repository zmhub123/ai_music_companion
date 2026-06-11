import { useMemo, useState } from 'react'
import { Button, Input } from 'antd'
import { useNavigate } from 'react-router-dom'
import { MOCK_RECOMMENDATIONS } from '../mocks/music'
import { MOCK_SCORE_SONG_IDS } from '../mocks/score'
import { usePlayerStore } from '../stores/playerStore'
import { useScoreStore } from '../stores/scoreStore'

export default function ScoresPage() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()
  const selectSong = usePlayerStore((s) => s.selectSong)
  const openGenerateModal = useScoreStore((s) => s.openGenerateModal)

  const scoreSongs = useMemo(
    () =>
      MOCK_RECOMMENDATIONS.filter((s) => MOCK_SCORE_SONG_IDS.includes(s.netease_song_id)).filter(
        (s) => {
          const q = query.trim().toLowerCase()
          if (!q) return true
          return (
            s.song_name.toLowerCase().includes(q) || s.artist_name.toLowerCase().includes(q)
          )
        },
      ),
    [query],
  )

  const openScore = (song: (typeof MOCK_RECOMMENDATIONS)[0]) => {
    selectSong({
      netease_song_id: song.netease_song_id,
      song_name: song.song_name,
      artist_name: song.artist_name,
      cover_url: song.cover_url,
    })
    navigate('/player')
    openGenerateModal()
  }

  return (
    <div className="page-content">
      <div className="page-header-row">
        <h2>谱库</h2>
      </div>
      <p className="page-desc">
        已生成弹唱谱的歌曲会保存在这里，可随时查看吉他谱或尤克里里谱
      </p>
      <div className="page-toolbar">
        <Input
          allowClear
          prefix={<span className="search-icon">⌕</span>}
          placeholder="搜索谱库歌曲"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      <div className="song-table">
        {scoreSongs.map((song) => (
          <div key={song.netease_song_id} className="song-table-row score-lib-row">
            <div className="song-cover">封面</div>
            <div className="song-info">
              <div className="name">{song.song_name}</div>
              <div className="artist">{song.artist_name} · 吉他 / 尤克里里</div>
            </div>
            <Button className="btn-view-score" onClick={() => openScore(song)}>
              查看谱面
            </Button>
          </div>
        ))}
      </div>
      {scoreSongs.length === 0 && <p className="search-empty">没有匹配的谱面歌曲</p>}
    </div>
  )
}
