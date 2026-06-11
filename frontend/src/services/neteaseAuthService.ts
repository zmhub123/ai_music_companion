import type { ApiResponse } from '../types/api'
import api, { rethrowApiError } from './api'

export interface NeteaseAuthStatus {
  logged_in: boolean
  nickname: string | null
}

export interface NeteaseQrStart {
  login_token: string
  qr_content: string
  qr_image_base64: string
  expires_in: number
}

export interface NeteaseQrPollResult {
  status: 'waiting' | 'scanned' | 'success' | 'expired'
  message: string
  nickname?: string
  logged_in?: boolean
}

export async function getNeteaseAuthStatus(): Promise<NeteaseAuthStatus> {
  const { data } = await api.get<ApiResponse<NeteaseAuthStatus>>('/v1/netease/auth/status')
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export async function startNeteaseQrLogin(): Promise<NeteaseQrStart> {
  const { data } = await api.post<ApiResponse<NeteaseQrStart>>('/v1/netease/login/qr')
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export async function pollNeteaseQrLogin(loginToken: string): Promise<NeteaseQrPollResult> {
  const { data } = await api.get<ApiResponse<NeteaseQrPollResult>>(`/v1/netease/login/qr/${loginToken}`)
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export async function logoutNetease(): Promise<NeteaseAuthStatus> {
  const { data } = await api.post<ApiResponse<NeteaseAuthStatus>>('/v1/netease/logout')
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export async function ensureGuestSession(): Promise<void> {
  try {
    const { data } = await api.post('/v1/guest/session')
    if (data.code !== 200) throw new Error(data.message)
  } catch (err) {
    rethrowApiError(err)
  }
}
