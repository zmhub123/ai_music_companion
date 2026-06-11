import { type MouseEvent } from 'react'
import { App, Spin } from 'antd'
import { MenuFoldOutlined } from '@ant-design/icons'
import SongCover from '../common/SongCover'
import { usePlayerStore } from '../../stores/playerStore'
import type { PlayerSong } from '../../types/song'
import { confirmVipPlayback } from '../../utils/playConfirm'

interface RecommendListProps {
  onCollapse?: () => void
}

export default function RecommendList({ onCollapse }: RecommendListProps) {
  const { message } = App.useApp()
  const recommendations = usePlayerStore((s) => s.recommendations)
  const currentSong = usePlayerStore((s) => s.currentSong)
  const loading = usePlayerStore((s) => s.loading)
  const playSong = usePlayerStore((s) => s.playSong)

  const handlePlay = async (song: PlayerSong, e: MouseEvent) => {
    e.stopPropagation()
    const err = await playSong(song)
    if (!err) return
    if (err === '已取消播放') return
    if (err.startsWith('http')) {
      if (song.vip_only) {
        await confirmVipPlayback(song.song_name, err)
        return
      }
      message.warning('暂无法内嵌播放，请尝试外链播放')
      window.open(err, '_blank', 'noopener,noreferrer')
      return
    }
    message.error(err)
  }

  return (
    <aside className="panel-left">
      <div className="panel-left-header">
        <h3>为您推荐</h3>
        {onCollapse ? (
          <button
            type="button"
            className="panel-left-collapse"
            aria-label="收起推荐列表"
            onClick={onCollapse}
          >
            <MenuFoldOutlined />
          </button>
        ) : null}
      </div>
      <div className="rec-list">
        {recommendations.map((song, i) => (
          <div
            key={song.netease_song_id}
            className={`rec-card${currentSong.netease_song_id === song.netease_song_id ? ' active' : ''}`}
            style={{ animationDelay: `${0.05 + i * 0.05}s` }}
            onClick={() => void playSong(song)}
          >
            <SongCover
              coverUrl={song.cover_url}
              alt={`${song.song_name} 封面`}
            />
            <div className="song-info">
              <div className="name">
                {song.song_name}
                {song.vip_only ? <span className="song-vip-tag">VIP</span> : null}
              </div>
              <div className="artist">{song.artist_name}</div>
            </div>
            <button
              type="button"
              className="song-play-btn"
              aria-label="播放"
              disabled={loading && currentSong.netease_song_id === song.netease_song_id}
              onClick={(e) => void handlePlay(song, e)}
            >
              {loading && currentSong.netease_song_id === song.netease_song_id ? (
                <Spin size="small" />
              ) : (
                '▶'
              )}
            </button>
          </div>
        ))}
      </div>
      <button type="button" className="btn-more">
        查看更多推荐
      </button>
    </aside>
  )
}
