import type { ReactNode } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import HomePage from './pages/HomePage'
import PlayerPage from './pages/PlayerPage'
import PlaylistsPage from './pages/PlaylistsPage'
import PlaylistDetailPage from './pages/PlaylistDetailPage'
import ScoresPage from './pages/ScoresPage'
import MePage from './pages/MePage'

function withLayout(element: ReactNode) {
  return <AppLayout>{element}</AppLayout>
}

export const router = createBrowserRouter([
  { path: '/', element: withLayout(<HomePage />) },
  { path: '/player', element: withLayout(<PlayerPage />) },
  { path: '/playlists', element: withLayout(<PlaylistsPage />) },
  { path: '/playlists/:id', element: withLayout(<PlaylistDetailPage />) },
  { path: '/scores', element: withLayout(<ScoresPage />) },
  { path: '/me', element: withLayout(<MePage />) },
])
