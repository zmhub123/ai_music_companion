import type { PlayerSong } from '../types/song'
import type { SongRecommendation } from '../types/api'

/** 与后端 SEED_SONGS 对齐，避免 Mock ID 与真实播放/谱面脱节 */
export const SEED_RECOMMENDATIONS: SongRecommendation[] = [
  {
    netease_song_id: 186016,
    song_name: '晴天',
    artist_name: '周杰伦',
    cover_url: '',
    reason: '安静舒缓，适合疲惫的晚上',
    is_original: true,
    vip_only: true,
    playable: false,
  },
  {
    netease_song_id: 29715551,
    song_name: '南山南',
    artist_name: '马頔',
    cover_url: '',
    reason: '旋律轻柔，帮你慢慢放松',
  },
  {
    netease_song_id: 436514312,
    song_name: '成都',
    artist_name: '赵雷',
    cover_url: '',
    reason: '节奏平稳，像晚风一样',
  },
  {
    netease_song_id: 28815250,
    song_name: '平凡之路',
    artist_name: '朴树',
    cover_url: '',
    reason: '简单和弦，适合入门弹唱',
  },
  {
    netease_song_id: 1330348068,
    song_name: '起风了',
    artist_name: '买辣椒也用券',
    cover_url: '',
    reason: '淡淡忧郁但不沉重',
  },
]

export const DEFAULT_PLAYER_SONG: PlayerSong = {
  netease_song_id: SEED_RECOMMENDATIONS[0].netease_song_id,
  song_name: SEED_RECOMMENDATIONS[0].song_name,
  artist_name: SEED_RECOMMENDATIONS[0].artist_name,
  cover_url: SEED_RECOMMENDATIONS[0].cover_url,
  reason: SEED_RECOMMENDATIONS[0].reason,
  is_original: SEED_RECOMMENDATIONS[0].is_original,
  vip_only: SEED_RECOMMENDATIONS[0].vip_only,
  playable: SEED_RECOMMENDATIONS[0].playable,
}
