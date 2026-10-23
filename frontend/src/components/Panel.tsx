import type { ReactNode } from 'react'

interface PanelProps {
  title?: string
  accent?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}

/** A timing-tower-style panel: sharp corners, hairline top accent instead
 * of a drop shadow, matching broadcast graphics rather than SaaS cards. */
export function Panel({ title, accent, action, children, className = '' }: PanelProps) {
  return (
    <section
      className={`bg-graphite border border-hairline ${className}`}
      style={{ borderTopWidth: 2, borderTopColor: accent ?? 'var(--color-hairline)' }}
    >
      {title && (
        <header className="flex items-center justify-between px-4 py-2.5 border-b border-hairline">
          <h2 className="text-[13px] font-600 tracking-[0.04em] text-steel uppercase">{title}</h2>
          {action}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  )
}
