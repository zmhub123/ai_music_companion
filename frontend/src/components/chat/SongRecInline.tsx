import { App } from 'antd'
import SongCover from '../common/SongCover'
import type { SongRecommendation } from '../../types/api'
import { usePlayerStore } from '../../stores/playerStore'
import { confirmVipPlayback } from '../../utils/playConfirm'

interface SongRecInlineProps {
  recommendations: SongRecommendation[]
}

export default function SongRecInline({ recommendations }: SongRecInlineProps) {
  const { message } = App.useApp()
  const playSong = usePlayerStore((s) => s.playSong)

  const handlePlay = async (rec: SongRecommendation) => {
    const err = await playSong({
      netease_song_id: rec.netease_song_id,
      song_name: rec.song_name,
      artist_name: rec.artist_name,
      cover_url: rec.cover_url,
      reason: rec.reason,
      is_original: rec.is_original,
      vip_only: rec.vip_only,
      playable: rec.playable,
    })
    if (!err) return
    if (err === '已取消播放') return
    if (err.startsWith('http')) {
      if (rec.vip_only) {
        await confirmVipPlayback(rec.song_name, err)
        return
      }
      message.warning('暂无法内嵌播放，请尝试外链播放')
      window.open(err, '_blank', 'noopener,noreferrer')
      return
    }
    message.error(err)
  }

  return (
    <div className="song-rec-inline">
      {recommendations.map((rec) => (
        <div
          key={rec.netease_song_id}
          className="song-row"
          onClick={() => void handlePlay(rec)}
        >
          <SongCover coverUrl={rec.cover_url} alt={`${rec.song_name} 封面`} />
          <div className="song-info">
            <div className="name">
              {rec.song_name}
              {rec.vip_only ? <span className="song-vip-tag">VIP</span> : null}
            </div>
            <div className="artist">{rec.artist_name}</div>
          </div>
          <button type="button" className="song-play-btn" aria-label="播放">
            ▶
          </button>
        </div>
      ))}
    </div>
  )
}
