import { useState } from 'react'

interface SongCoverProps {
  coverUrl?: string
  alt?: string
  className?: string
}

export default function SongCover({ coverUrl, alt = '', className = '' }: SongCoverProps) {
  const [failed, setFailed] = useState(false)
  const src = coverUrl?.trim()
  const showImage = Boolean(src) && !failed

  return (
    <div className={`song-cover${showImage ? ' has-image' : ''}${className ? ` ${className}` : ''}`}>
      {showImage ? (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          referrerPolicy="no-referrer"
          onError={() => setFailed(true)}
        />
      ) : (
        <span className="song-cover-fallback" aria-hidden="true">
          ♪
        </span>
      )}
    </div>
  )
}
