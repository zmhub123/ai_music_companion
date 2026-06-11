/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_USE_MOCK: string
  readonly VITE_MOCK_GUEST: string
  readonly VITE_MOCK_PLAYLIST: string
  readonly VITE_MOCK_CHAT: string
  readonly VITE_MOCK_MUSIC: string
  readonly VITE_BACKEND_PROXY_TARGET: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
