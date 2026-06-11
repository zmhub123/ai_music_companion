import { Modal } from 'antd'

export function neteaseSongUrl(songId: number): string {
  return `https://music.163.com/song?id=${songId}`
}

export function confirmNeteaseLogin(message: string): Promise<boolean> {
  return new Promise((resolve) => {
    Modal.confirm({
      title: '需要登录网易云',
      content: message,
      okText: '扫码登录',
      cancelText: '取消',
      centered: true,
      onOk: () => resolve(true),
      onCancel: () => resolve(false),
    })
  })
}

export function showVipPaidMessage(): void {
  Modal.info({
    title: '无法播放',
    content: '抱歉，呜呜音源要钱',
    centered: true,
    okText: '知道了',
  })
}

export function confirmVipPlayback(songName: string, fallbackUrl: string): Promise<boolean> {
  return new Promise((resolve) => {
    Modal.confirm({
      title: 'VIP 歌曲',
      content: `《${songName}》为网易云 VIP 专享。登录后若仍无法播放，说明该曲需要付费会员。`,
      okText: '去网易云',
      cancelText: '取消',
      centered: true,
      onOk: () => {
        window.open(fallbackUrl, '_blank', 'noopener,noreferrer')
        resolve(true)
      },
      onCancel: () => resolve(false),
    })
  })
}

export async function handlePlaybackError(
  err: string,
  songName: string,
  options?: { vipRequired?: boolean },
): Promise<void> {
  if (options?.vipRequired && err.startsWith('http')) {
    await confirmVipPlayback(songName, err)
    return
  }
  if (err.startsWith('http')) {
    Modal.confirm({
      title: '无法内嵌播放',
      content: `《${songName}》暂无法在本页播放，是否跳转外链？`,
      okText: '去播放',
      cancelText: '取消',
      centered: true,
      onOk: () => window.open(err, '_blank', 'noopener,noreferrer'),
    })
  }
}
