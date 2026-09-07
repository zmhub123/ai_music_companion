import { useAuthStore } from './authStore'
import { useChatStore } from './chatStore'
import { usePlayerStore } from './playerStore'

/** 游客清除全部数据后，同步重置前端内存态（后端已删库）。 */
export async function resetClientSessionAfterGuestClear(): Promise<void> {
  useChatStore.getState().resetAfterGuestClear()
  usePlayerStore.getState().resetAfterGuestClear()
  await useAuthStore.getState().refreshAuth()
}
