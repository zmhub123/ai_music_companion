import type { ApiResponse } from '../types/api'
import type { PlayUrl } from '../types/song'
import { SEED_RECOMMENDATIONS } from '../constants/seedSongs'
import { MOCK_SONGS } from './songs'

export const MOCK_RECOMMENDATIONS = SEED_RECOMMENDATIONS

const MOCK_AUDIO_URL =
  'https://interactive-examples.mdn.mozilla.net/media/cc0-audio/t-rex-roar.mp3'

export function mockGetPlayUrl(neteaseSongId: number): ApiResponse<PlayUrl> {
  const song = MOCK_SONGS.find((s) => s.netease_song_id === neteaseSongId)
  if (!song) {
    return { code: 40402, message: '歌曲不存在', data: null }
  }
  return {
    code: 200,
    message: 'success',
    data: {
      url: MOCK_AUDIO_URL,
      expires_in: 1200,
      quality: 'standard',
      fallback_url: `https://music.163.com/song?id=${neteaseSongId}`,
    },
  }
}
