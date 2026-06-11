import type { ApiResponse, GuestProfile, OnboardingRequest, OnboardingResponse } from '../types/api'

const STORAGE_KEY = 'yinban_guest_mock'

const DEFAULT_GUEST: GuestProfile = {
  guest_id: '550e8400-e29b-41d4-a716-446655440000',
  skill_level: null,
  style_preferences: [],
  onboarding_completed: false,
  created_at: '2026-06-07T10:00:00Z',
  last_active_at: '2026-06-07T10:00:00Z',
}

function loadGuest(): GuestProfile {
  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) return { ...DEFAULT_GUEST }
  return { ...DEFAULT_GUEST, ...JSON.parse(raw) } as GuestProfile
}

function saveGuest(profile: GuestProfile) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(profile))
}

export function mockGetGuestMe(): ApiResponse<GuestProfile> {
  return { code: 200, message: 'success', data: loadGuest() }
}

export function mockSubmitOnboarding(
  payload: OnboardingRequest,
): ApiResponse<OnboardingResponse> {
  if (payload.style_preferences.length < 1) {
    return { code: 40001, message: 'style_preferences 至少选择 1 项', data: null }
  }

  const profile: GuestProfile = {
    ...loadGuest(),
    skill_level: payload.skill_level,
    style_preferences: payload.style_preferences,
    onboarding_completed: true,
    last_active_at: new Date().toISOString(),
  }
  saveGuest(profile)

  return {
    code: 200,
    message: 'success',
    data: {
      guest_id: profile.guest_id,
      skill_level: payload.skill_level,
      style_preferences: payload.style_preferences,
      onboarding_completed: true,
    },
  }
}

export function mockUpdatePreferences(payload: {
  skill_level: OnboardingRequest['skill_level']
  style_preferences: string[]
}): ApiResponse<{ skill_level: OnboardingRequest['skill_level']; style_preferences: string[] }> {
  const profile: GuestProfile = {
    ...loadGuest(),
    skill_level: payload.skill_level,
    style_preferences: payload.style_preferences,
    last_active_at: new Date().toISOString(),
  }
  saveGuest(profile)
  return {
    code: 200,
    message: 'success',
    data: {
      skill_level: payload.skill_level,
      style_preferences: payload.style_preferences,
    },
  }
}

export function mockClearGuestData(): ApiResponse<{ cleared: boolean; onboarding_completed: boolean }> {
  localStorage.removeItem(STORAGE_KEY)
  return {
    code: 200,
    message: 'success',
    data: { cleared: true, onboarding_completed: false },
  }
}
