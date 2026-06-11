import { useEffect, useState } from 'react'
import { App, Modal, Radio } from 'antd'
import { addSongToPlaylist, listPlaylists } from '../../services/playlistService'
import { usePlayerStore } from '../../stores/playerStore'
import type { PlaylistSummary } from '../../types/playlist'

interface AddToPlaylistModalProps {
  open: boolean
  onClose: () => void
}

export default function AddToPlaylistModal({ open, onClose }: AddToPlaylistModalProps) {
  const { message } = App.useApp()
  const currentSong = usePlayerStore((s) => s.currentSong)
  const [playlists, setPlaylists] = useState<PlaylistSummary[]>([])
  const [selectedId, setSelectedId] = useState<string>('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!open) return
    void listPlaylists()
      .then((items) => {
        setPlaylists(items)
        setSelectedId(items[0]?.id ?? '')
      })
      .catch(() => message.error('加载歌单失败'))
  }, [open, message])

  const handleOk = async () => {
    if (!selectedId) {
      message.warning('请选择歌单')
      return
    }
    setLoading(true)
    try {
      await addSongToPlaylist(selectedId, {
        netease_song_id: currentSong.netease_song_id,
        song_name: currentSong.song_name,
        artist_name: currentSong.artist_name,
        cover_url: currentSong.cover_url,
      })
      message.success('已加入歌单')
      onClose()
    } catch (err) {
      message.error(err instanceof Error ? err.message : '添加失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title="加入歌单"
      open={open}
      onCancel={onClose}
      onOk={() => void handleOk()}
      confirmLoading={loading}
      okText="确认"
      cancelText="取消"
    >
      {playlists.length === 0 ? (
        <p>暂无歌单，请先在歌单页创建。</p>
      ) : (
        <Radio.Group value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
          {playlists.map((p) => (
            <Radio key={p.id} value={p.id} style={{ display: 'block', marginBottom: 8 }}>
              {p.name}（{p.song_count} 首）
            </Radio>
          ))}
        </Radio.Group>
      )}
    </Modal>
  )
}
