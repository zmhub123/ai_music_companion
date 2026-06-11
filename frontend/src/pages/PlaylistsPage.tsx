import { useEffect, useMemo, useState } from 'react'
import { App, Button, Input, Modal } from 'antd'
import { useNavigate } from 'react-router-dom'
import { createPlaylist, deletePlaylist, listPlaylists } from '../services/playlistService'
import type { PlaylistSummary } from '../types/playlist'

export default function PlaylistsPage() {
  const { message, modal } = App.useApp()
  const navigate = useNavigate()
  const [playlists, setPlaylists] = useState<PlaylistSummary[]>([])
  const [query, setQuery] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')

  const load = async () => {
    try {
      setPlaylists(await listPlaylists())
    } catch {
      message.error('加载歌单失败')
    }
  }

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const items = await listPlaylists()
        if (!cancelled) setPlaylists(items)
      } catch {
        if (!cancelled) message.error('加载歌单失败')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [message])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return playlists
    return playlists.filter(
      (p) => p.name.toLowerCase().includes(q) || p.description.toLowerCase().includes(q),
    )
  }, [playlists, query])

  const handleCreate = async () => {
    if (!newName.trim()) {
      message.warning('请输入歌单名称')
      return
    }
    try {
      const created = await createPlaylist({
        name: newName.trim(),
        description: newDesc.trim(),
      })
      message.success('歌单已创建')
      setCreateOpen(false)
      setNewName('')
      setNewDesc('')
      await load()
      navigate(`/playlists/${created.id}`)
    } catch (err) {
      message.error(err instanceof Error ? err.message : '创建失败')
    }
  }

  const handleDelete = (pl: PlaylistSummary) => {
    modal.confirm({
      title: `删除歌单「${pl.name}」？`,
      content: '删除后无法恢复',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        await deletePlaylist(pl.id)
        message.success('已删除')
        await load()
      },
    })
  }

  return (
    <div className="page-content">
      <div className="page-header-row">
        <h2>我的歌单</h2>
        <Button type="primary" className="btn-create-playlist" onClick={() => setCreateOpen(true)}>
          新建歌单
        </Button>
      </div>
      <div className="page-toolbar">
        <Input
          allowClear
          prefix={<span className="search-icon">⌕</span>}
          placeholder="搜索歌单名称"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      <div className="playlist-grid">
        {filtered.map((pl) => (
          <div
            key={pl.id}
            className="playlist-card"
            onClick={() => navigate(`/playlists/${pl.id}`)}
          >
            <div className="playlist-cover">♪</div>
            <h3>{pl.name}</h3>
            <p>{pl.song_count} 首歌曲</p>
            <button
              type="button"
              className="playlist-delete-btn"
              onClick={(e) => {
                e.stopPropagation()
                handleDelete(pl)
              }}
            >
              删除
            </button>
          </div>
        ))}
      </div>
      {filtered.length === 0 && <p className="search-empty">没有匹配的歌单</p>}

      <Modal
        title="新建歌单"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={() => void handleCreate()}
        okText="创建"
        cancelText="取消"
      >
        <Input
          placeholder="歌单名称"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          style={{ marginBottom: 12 }}
        />
        <Input.TextArea
          placeholder="描述（可选）"
          value={newDesc}
          onChange={(e) => setNewDesc(e.target.value)}
          rows={3}
        />
      </Modal>
    </div>
  )
}
