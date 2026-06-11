import { UnorderedListOutlined } from '@ant-design/icons'
import { usePlayerStore } from '../../stores/playerStore'

export default function PlaylistDock() {
  const drawerOpen = usePlayerStore((s) => s.playlistDrawerOpen)
  const togglePlaylistDrawer = usePlayerStore((s) => s.togglePlaylistDrawer)

  if (drawerOpen) return null

  return (
    <button
      type="button"
      className="player-playlist-dock"
      aria-label="打开推荐歌曲列表"
      onClick={togglePlaylistDrawer}
    >
      <UnorderedListOutlined className="player-playlist-dock-icon" />
      <span className="player-playlist-dock-label">推荐</span>
    </button>
  )
}
