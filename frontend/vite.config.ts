import { defineConfig, loadEnv } from 'vite'
import type { Plugin } from 'vite'
import react from '@vitejs/plugin-react'

const DEFAULT_BACKEND_TARGET = 'http://127.0.0.1:8099'

function backendProxyHealthCheck(backendTarget: string): Plugin {
  return {
    name: 'backend-proxy-health-check',
    configureServer(server) {
      server.httpServer?.once('listening', () => {
        const healthUrl = `${backendTarget.replace(/\/$/, '')}/health`
        void fetch(healthUrl)
          .then((res) => {
            if (!res.ok) {
              throw new Error(`HTTP ${res.status}`)
            }
            console.log(`[vite] API 代理 -> ${backendTarget} (后端已就绪)`)
          })
          .catch(() => {
            console.warn(
              `[vite] API 代理 -> ${backendTarget}，但后端未响应 ${healthUrl}\n` +
                '       请先启动后端: cd .. && ./scripts/dev-backend.sh',
            )
          })
      })
    },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendTarget = env.VITE_BACKEND_PROXY_TARGET || DEFAULT_BACKEND_TARGET
  const wsTarget = backendTarget.replace(/^http/, 'ws')

  return {
    plugins: [react(), backendProxyHealthCheck(backendTarget)],
    server: {
      port: 5199,
      host: '127.0.0.1',
      proxy: {
        '/api': {
          target: backendTarget,
          changeOrigin: true,
        },
        '/ws': {
          target: wsTarget,
          ws: true,
          changeOrigin: true,
        },
      },
    },
  }
})
