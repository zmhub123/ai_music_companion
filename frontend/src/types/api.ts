export type SkillLevel = 'beginner' | 'intermediate' | 'advanced'

export interface ApiResponse<T> {
  code: number
  message: string
  data: T | null
}

export interface GuestProfile {
  guest_id: string
  skill_level: SkillLevel | null
  style_preferences: string[]
  onboarding_completed: boolean
  created_at?: string
  last_active_at?: string
}

export interface OnboardingRequest {
  skill_level: SkillLevel
  style_preferences: string[]
}

export interface OnboardingResponse {
  guest_id: string
  skill_level: SkillLevel
  style_preferences: string[]
  onboarding_completed: boolean
}

export interface SongRecommendation {
  netease_song_id: number
  song_name: string
  artist_name: string
  cover_url: string
  reason: string
  is_original?: boolean
  vip_only?: boolean
  playable?: boolean
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  metadata: {
    intent?: string
    recommendations?: SongRecommendation[]
    auto_play?: boolean
    pending?: boolean
  } | null
  created_at: string
}

export interface SendMessageResponse {
  user_message: ChatMessage
  assistant_message: ChatMessage
}
