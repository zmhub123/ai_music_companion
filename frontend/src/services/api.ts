import axios from 'axios'
import type { ApiResponse } from '../types/api'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  withCredentials: true,
})

export const useMock = import.meta.env.VITE_USE_MOCK === 'true'

/** 游客 Session 可单独切真实 API，其余服务仍走 Mock */
export const useGuestMock = useMock && import.meta.env.VITE_MOCK_GUEST !== 'false'

/** 歌单可单独切真实 API */
export const usePlaylistMock = useMock && import.meta.env.VITE_MOCK_PLAYLIST !== 'false'

/** 聊天可单独切真实 API */
export const useChatMock = useMock && import.meta.env.VITE_MOCK_CHAT !== 'false'

/** 音乐播放可单独切真实 API */
export const useMusicMock = useMock && import.meta.env.VITE_MOCK_MUSIC !== 'false'

/** 谱面可单独切真实 API */
export const useScoreMock = useMock && import.meta.env.VITE_MOCK_SCORE !== 'false'

export function getApiErrorMessage(err: unknown, fallback = '请求失败'): string {
  if (axios.isAxiosError(err)) {
    const body = err.response?.data as Partial<ApiResponse<unknown>> | undefined
    if (body?.message) return body.message
  }
  if (err instanceof Error) return err.message
  return fallback
}

export function rethrowApiError(err: unknown, fallback = '请求失败'): never {
  throw new Error(getApiErrorMessage(err, fallback))
}

export default api
