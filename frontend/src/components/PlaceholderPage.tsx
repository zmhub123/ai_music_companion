import type { ReactNode } from 'react'

interface PlaceholderPageProps {
  title: string
  description?: string
  children?: ReactNode
}

export default function PlaceholderPage({ title, description, children }: PlaceholderPageProps) {
  return (
    <div className="placeholder-page">
      <h2>{title}</h2>
      {description && <p className="placeholder-desc">{description}</p>}
      {children}
    </div>
  )
}
