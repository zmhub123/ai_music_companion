import { create } from 'zustand'
import { getGuestMe } from '../services/guestService'
import type { GuestProfile, SkillLevel } from '../types/api'

interface GuestState {
  profile: GuestProfile | null
  loading: boolean
  showOnboarding: boolean
  fetchProfile: () => Promise<void>
  setOnboardingDone: (skillLevel: SkillLevel, styles: string[]) => void
}

export const useGuestStore = create<GuestState>((set) => ({
  profile: null,
  loading: true,
  showOnboarding: false,

  fetchProfile: async () => {
    set({ loading: true })
    try {
      const profile = await getGuestMe()
      set({
        profile,
        showOnboarding: !profile.onboarding_completed,
        loading: false,
      })
    } catch {
      set({ loading: false, showOnboarding: true })
    }
  },

  setOnboardingDone: (skillLevel, styles) => {
    set((state) => ({
      profile: state.profile
        ? {
            ...state.profile,
            skill_level: skillLevel,
            style_preferences: styles,
            onboarding_completed: true,
          }
        : {
            guest_id: '',
            skill_level: skillLevel,
            style_preferences: styles,
            onboarding_completed: true,
          },
      showOnboarding: false,
    }))
  },
}))
