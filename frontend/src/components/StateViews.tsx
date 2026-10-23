export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-8 text-steel text-sm">
      <span className="h-2 w-2 rounded-full bg-signal animate-pulse" />
      {label}…
    </div>
  )
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="py-8 text-sm">
      <p className="text-paper font-600">Couldn't load this data.</p>
      <p className="text-steel mt-1">{message}</p>
    </div>
  )
}

export function EmptyState({ message }: { message: string }) {
  return <div className="py-8 text-sm text-steel">{message}</div>
}
