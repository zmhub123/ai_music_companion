import { mockClearGuestData, mockGetGuestMe, mockSubmitOnboarding, mockUpdatePreferences } from '../mocks/guest'
import { mockClearPlaylists } from '../mocks/playlists'
import type { ApiResponse, GuestProfile, OnboardingRequest, OnboardingResponse, SkillLevel } from '../types/api'
import api, { useGuestMock } from './api'

export async function ensureGuestSession(): Promise<GuestProfile> {
  const { data } = await api.post<ApiResponse<GuestProfile>>('/v1/guest/session')
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

async function loadGuestMe(): Promise<GuestProfile> {
  const { data } = await api.get<ApiResponse<GuestProfile>>('/v1/guest/me')
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export async function getGuestMe(): Promise<GuestProfile> {
  if (useGuestMock) {
    const res = mockGetGuestMe()
    if (res.code !== 200 || !res.data) throw new Error(res.message)
    return res.data
  }

  try {
    return await loadGuestMe()
  } catch (err) {
    const status = (err as { response?: { status?: number } }).response?.status
    if (status === 401) {
      await ensureGuestSession()
      return loadGuestMe()
    }
    throw err
  }
}

export async function submitOnboarding(payload: OnboardingRequest): Promise<OnboardingResponse> {
  if (useGuestMock) {
    const res = mockSubmitOnboarding(payload)
    if (res.code !== 200 || !res.data) throw new Error(res.message)
    return res.data
  }

  const { data } = await api.post<ApiResponse<OnboardingResponse>>('/v1/guest/onboarding', payload)
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export async function updatePreferences(payload: {
  skill_level: SkillLevel
  style_preferences: string[]
}): Promise<void> {
  if (useGuestMock) {
    const res = mockUpdatePreferences(payload)
    if (res.code !== 200) throw new Error(res.message)
    return
  }
  const { data } = await api.put<ApiResponse<unknown>>('/v1/guest/preferences', payload)
  if (data.code !== 200) throw new Error(data.message)
}

export async function clearGuestData(): Promise<void> {
  if (useGuestMock) {
    mockClearGuestData()
    mockClearPlaylists()
    return
  }
  const { data } = await api.delete<ApiResponse<unknown>>('/v1/guest/data')
  if (data.code !== 200) throw new Error(data.message)
}
