import type { ApiResponse, ChatMessage, SendMessageResponse } from '../types/api'
import { MOCK_RECOMMENDATIONS } from './music'

let msgSeq = 2

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: 'msg-001',
    role: 'assistant',
    content: '你好，我是你的音乐陪伴助手。告诉我此刻的心情，我来为你荐歌。',
    metadata: null,
    created_at: '2026-06-07T10:00:00Z',
  },
  {
    id: 'msg-002',
    role: 'user',
    content: '我今天有点累',
    metadata: null,
    created_at: '2026-06-07T10:01:00Z',
  },
  {
    id: 'msg-003',
    role: 'assistant',
    content: '辛苦了，先慢慢呼吸一下。我挑了几首温柔的歌，你可以先听听看：',
    metadata: {
      intent: 'recommend_music',
      recommendations: MOCK_RECOMMENDATIONS.slice(0, 2),
    },
    created_at: '2026-06-07T10:01:08Z',
  },
]

let messageHistory = [...INITIAL_MESSAGES]

function nextId() {
  msgSeq += 1
  return `msg-${String(msgSeq).padStart(3, '0')}`
}

export function mockGetMessages(): ApiResponse<{ items: ChatMessage[]; total: number; page: number; page_size: number }> {
  return {
    code: 200,
    message: 'success',
    data: {
      items: messageHistory,
      total: messageHistory.length,
      page: 1,
      page_size: 50,
    },
  }
}

export function mockSendMessage(content: string): ApiResponse<SendMessageResponse> {
  const now = new Date().toISOString()
  const userId = nextId()
  const assistantId = nextId()

  const userMessage: ChatMessage = {
    id: userId,
    role: 'user',
    content,
    metadata: null,
    created_at: now,
  }
  const assistantMessage: ChatMessage = {
    id: assistantId,
    role: 'assistant',
    content: '我理解你现在的感受。根据你的心情，我为你挑选了这些歌：',
    metadata: {
      intent: 'recommend_music',
      recommendations: MOCK_RECOMMENDATIONS.slice(0, 3),
    },
    created_at: now,
  }

  messageHistory = [...messageHistory, userMessage, assistantMessage]

  return {
    code: 200,
    message: 'success',
    data: { user_message: userMessage, assistant_message: assistantMessage },
  }
}
