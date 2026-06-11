import axios from 'axios'
import { mockGetMessages, mockSendMessage } from '../mocks/chat'
import type { ApiResponse, ChatMessage, SendMessageResponse } from '../types/api'
import api, { rethrowApiError, useChatMock } from './api'
import { ensureGuestSession } from './guestService'

async function withGuestAuth<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request()
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 401) {
      await ensureGuestSession()
      try {
        return await request()
      } catch (retryErr) {
        rethrowApiError(retryErr)
      }
    }
    rethrowApiError(err)
  }
}

export async function getMessages(): Promise<ChatMessage[]> {
  if (useChatMock) {
    const res = mockGetMessages()
    if (res.code !== 200 || !res.data) throw new Error(res.message)
    return res.data.items
  }

  const { data } = await withGuestAuth(() =>
    api.get<ApiResponse<{ items: ChatMessage[] }>>('/v1/chat/messages'),
  )
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data.items
}

export async function sendMessage(content: string): Promise<SendMessageResponse> {
  if (useChatMock) {
    const res = mockSendMessage(content)
    if (res.code !== 200 || !res.data) throw new Error(res.message)
    return res.data
  }

  const { data } = await withGuestAuth(() =>
    api.post<ApiResponse<SendMessageResponse>>('/v1/chat/messages', { content }),
  )
  if (data.code !== 200 || !data.data) throw new Error(data.message)
  return data.data
}

export async function resetChat(): Promise<void> {
  if (useChatMock) {
    return
  }
  const { data } = await withGuestAuth(() =>
    api.post<ApiResponse<{ reset: boolean }>>('/v1/chat/reset'),
  )
  if (data.code !== 200) throw new Error(data.message)
}
